import numpy as np
from pathlib import Path
import deglib

from ..base.module import BaseANN


_METRIC_MAP = {
    "euclidean": (deglib.Metric.FP32_L2, deglib.Metric.Int8_L2, deglib.Metric.FP16_L2),
    "cosine": (deglib.Metric.FP32_InnerProduct, deglib.Metric.Int8_InnerProduct, deglib.Metric.FP16_InnerProduct),
    "ip": (deglib.Metric.FP32_InnerProduct, deglib.Metric.Int8_InnerProduct, deglib.Metric.FP16_InnerProduct),
    "normalized": (deglib.Metric.FP32_InnerProduct, deglib.Metric.Int8_InnerProduct, deglib.Metric.FP16_InnerProduct),
}


class DEG(BaseANN):
    """
    Dynamic Exploration Graph (DEG) using Float32 throughout.
    """

    def __init__(
        self,
        metric: str,
        k: int = 30,
        opt_target: str = "LowLID",
        prune_non_rng: bool = False,
    ):
        self.metric = metric.lower().strip()
        if self.metric not in _METRIC_MAP:
            raise ValueError(f"Unsupported metric '{self.metric}'. Choose from: {list(_METRIC_MAP.keys())}")

        self.k = int(k)
        self.opt_target = opt_target
        self.prune_non_rng = bool(prune_non_rng)
        self.search_eps = 0.1

        self.metric_enum = _METRIC_MAP[self.metric][0]
        self.opt_enum = deglib.builder.OptimizationTarget[self.opt_target]
        self.graph = None
        self.searcher = None

    def fit(self, X: np.ndarray):
        """Builds the DEG graph in FP32."""
        if self.metric == "cosine":
            X = X / np.linalg.norm(X, axis=1)[:, np.newaxis]
        X = np.ascontiguousarray(X, dtype=np.float32)

        # 1. FLAS 1D Pre-sorting
        sorted_indices = deglib.optimization.presort(
            X,
            metric=self.metric_enum,
            threads=1,
        )

        # 2. Build graph in FP32
        graph = deglib.builder.build_from_data(
            data=X[sorted_indices],
            labels=sorted_indices,
            edges_per_vertex=self.k,
            metric=self.metric_enum,
            seed=7,
            optimization_target=self.opt_enum,
            thread_count=1,
        )

        # 3. Optional MRNG edge pruning
        if self.prune_non_rng:
            deglib.optimization.prune_non_rng_edges(graph, num_threads=1)

        self.graph = graph.to_readonly()
        self.searcher = deglib.search.create_searcher(graph=self.graph)

    def set_query_arguments(self, search_eps: float):
        """Sets query-time search_eps."""
        self.search_eps = float(search_eps)

    def query(self, v: np.ndarray, n: int) -> np.ndarray:
        """Single query search on 1 thread with Float32 via C++ searcher."""
        if self.metric == "cosine":
            v = v / np.linalg.norm(v)
        return self.searcher.search(
            np.ascontiguousarray(v, dtype=np.float32),
            k=n,
            eps=self.search_eps,
            threads=1,
            return_distances=False,
            unsorted=True,
        )

    def __str__(self) -> str:
        return f"DEG(k={self.k}, opt={self.opt_target}, prune_rng={self.prune_non_rng}, eps={self.search_eps})"


class QG(BaseANN):
    """
    Quantized DEG (DEG-QG): Graph search with INT8 quantized vectors and FP16 reranking.
    """

    def __init__(
        self,
        metric: str,
        k: int = 30,
        opt_target: str = "LowLID",
        prune_non_rng: bool = False,
    ):
        self.metric = metric.lower().strip()
        if self.metric not in _METRIC_MAP:
            raise ValueError(f"Unsupported metric '{self.metric}'. Choose from: {list(_METRIC_MAP.keys())}")

        self.k = int(k)
        self.opt_target = opt_target
        self.prune_non_rng = bool(prune_non_rng)
        self.rerank_size_factor = 1.0
        self.search_eps = 0.1

        self.base_metric, self.int8_metric, self.fp16_metric = _METRIC_MAP[self.metric]
        self.opt_enum = deglib.builder.OptimizationTarget[self.opt_target]

        self.graph = None
        self.searcher = None
        self.quantizer = None
        self.original_features_fp16 = None
        self.rerank_space_fp16 = None

    def fit(self, X: np.ndarray):
        """Builds DEG graph, quantizes vectors to INT8 using ScalarQuantizer, and prepares C++ searcher."""
        if self.metric == "cosine":
            X = X / np.linalg.norm(X, axis=1)[:, np.newaxis]
        X = np.ascontiguousarray(X, dtype=np.float32)
        dims = X.shape[1]

        self.original_features_fp16 = deglib.distances.floats_to_fp16(X)
        self.rerank_space_fp16 = deglib.FloatSpace.create(dim=dims, metric=self.fp16_metric)

        cache_file = Path(f"data/cache_deg_{self.metric}_k{self.k}_{self.opt_target}_n{len(X)}.deg")
        if cache_file.exists():
            print(f"Loading cached DEG graph from {cache_file}...", flush=True)
            loaded_graph = deglib.load_readonly_graph(str(cache_file))
        else:
            # 1. FLAS 1D Pre-sorting
            sorted_indices = deglib.optimization.presort(
                X,
                metric=self.base_metric,
                threads=1,
            )

            # 2. Build graph in FP32
            graph = deglib.builder.build_from_data(
                data=X[sorted_indices],
                labels=sorted_indices,
                edges_per_vertex=self.k,
                metric=self.base_metric,
                seed=7,
                optimization_target=self.opt_enum,
                thread_count=1,
            )

            # 3. Optional MRNG edge pruning
            if self.prune_non_rng:
                deglib.optimization.prune_non_rng_edges(graph, num_threads=1)

            print(f"Saving graph to cache {cache_file}...", flush=True)
            graph.save_graph(str(cache_file))
            loaded_graph = graph
        # 4. Finalize ReadOnlyGraph with INT8 features using calibrated ScalarQuantizer
        self.quantizer = deglib.optimization.make_scalar_quantizer_int8(X)
        int8_features = self.quantizer.quantize(X, num_threads=1)
        target_space = deglib.FloatSpace.create(dim=dims, metric=self.int8_metric)
        self.graph = loaded_graph.to_readonly(target_space, int8_features)
        # Set 64 well-spaced entrypoints across the graph to reduce cluster navigation hops
        rng = np.random.default_rng(42)
        n_entries = min(64, len(X))
        entry_indices = rng.choice(len(X), size=n_entries, replace=False).astype(np.uint32)
        self.graph.set_entry_vertex_indices(entry_indices)

        # 5. Initialize C++ Zero-overhead Searcher
        self.searcher = deglib.search.create_searcher(
            graph=self.graph,
            quantizer=self.quantizer,
            refine_space=self.rerank_space_fp16,
            refine_data=self.original_features_fp16,
        )

    def set_query_arguments(self, *args, **kwargs):
        """Sets query-time parameters: supports (rerank_factor, search_eps) or (rerank_factor, ef)."""
        self.rerank_size_factor = float(kwargs.get("rerank_size_factor", 1.0))
        self.search_eps = float(kwargs.get("search_eps", 0.0))
        self.ef = int(kwargs.get("ef", 0))

        if len(args) == 1:
            val = args[0]
            if isinstance(val, int) or (isinstance(val, float) and val >= 1.0 and val.is_integer()):
                self.ef = int(val)
            else:
                self.search_eps = float(val)
        elif len(args) == 2:
            self.rerank_size_factor = float(args[0])
            val = args[1]
            if isinstance(val, int) or (isinstance(val, float) and val >= 1.0 and val.is_integer()):
                self.ef = int(val)
                self.search_eps = 0.0
            else:
                self.search_eps = float(val)
                self.ef = 0
        elif len(args) >= 3:
            self.rerank_size_factor = float(args[0])
            self.search_eps = float(args[1])
            self.ef = int(args[2])

    def query(self, v: np.ndarray, n: int) -> np.ndarray:
        """Single query search on 1 thread with INT8 search and FP16 reranking directly in C++."""
        if self.metric == "cosine":
            v = v / np.linalg.norm(v)
        return self.searcher.search(
            np.ascontiguousarray(v, dtype=np.float32),
            k=n,
            eps=self.search_eps,
            rerank_factor=self.rerank_size_factor,
            threads=1,
            return_distances=False,
            unsorted=True,
            ef=self.ef,
        )

    def __str__(self) -> str:
        if getattr(self, "ef", 0) > 0:
            return (
                f"DEG-QG(k={self.k}, opt={self.opt_target}, prune_rng={self.prune_non_rng}, "
                f"rerank_factor={self.rerank_size_factor}, ef={self.ef})"
            )
        return (
            f"DEG-QG(k={self.k}, opt={self.opt_target}, prune_rng={self.prune_non_rng}, "
            f"rerank_factor={self.rerank_size_factor}, eps={self.search_eps})"
        )
