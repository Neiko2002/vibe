import numpy as np
import time
from pathlib import Path
import deglib

from ..base.module import BaseANN


_METRIC_MAP = {
    "euclidean": (deglib.Metric.FP32_L2, deglib.Metric.Int8_L2, deglib.Metric.FP16_L2),
    "cosine": (deglib.Metric.FP32_InnerProduct, deglib.Metric.Int8_InnerProduct, deglib.Metric.FP16_InnerProduct),
    "ip": (deglib.Metric.FP32_InnerProduct, deglib.Metric.Int8_InnerProduct, deglib.Metric.FP16_InnerProduct),
    "normalized": (deglib.Metric.FP32_InnerProduct, deglib.Metric.Int8_InnerProduct, deglib.Metric.FP16_InnerProduct),
}

def find_kmeans_medoids(X: np.ndarray, n_clusters: int = 128, n_iter: int = 15, sample_size: int = 30000) -> np.ndarray:
    rng = np.random.default_rng(42)
    sample_indices = rng.choice(len(X), size=min(sample_size, len(X)), replace=False)
    sub_X = X[sample_indices]
    n_clusters = min(n_clusters, len(sub_X))
    init_idx = rng.choice(len(sub_X), size=n_clusters, replace=False)
    centroids = sub_X[init_idx].copy()
    for _ in range(n_iter):
        sims = np.dot(sub_X, centroids.T)
        labels = np.argmax(sims, axis=1)
        for c in range(n_clusters):
            members = sub_X[labels == c]
            if len(members) > 0:
                mean_vec = np.mean(members, axis=0)
                norm = np.linalg.norm(mean_vec)
                if norm > 1e-6:
                    centroids[c] = mean_vec / norm
    medoids = [sample_indices[np.argmax(np.dot(sub_X, centroids[c]))] for c in range(n_clusters)]
    return np.array(medoids, dtype=np.uint32)


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
        # Set 128 K-Means cluster medoids across the graph to reduce cluster navigation hops
        t_km = time.time()
        entry_indices = find_kmeans_medoids(X, n_clusters=128, n_iter=15, sample_size=30000)
        print(f"K-Means 128 cluster medoids computed in {time.time() - t_km:.2f}s", flush=True)
        self.graph.set_entry_vertex_indices(entry_indices)

        # 5. Initialize C++ Zero-overhead Searcher
        self.searcher = deglib.search.create_searcher(
            graph=self.graph,
            quantizer=self.quantizer,
            refine_space=self.rerank_space_fp16,
            refine_data=self.original_features_fp16,
        )

        # 6. Auto-tune prefetch parameters (po, pl) using 100 sample queries
        sample_queries = X[:100]
        best_po, best_pl = self.searcher.optimize(
            sample_queries,
            k=100,
            ef=200,
            try_pos=[4, 6, 8, 10, 12, 14, 16],
            try_pls=[2, 3, 4],
        )
        print(f"Prefetch auto-tuner selected: best_po={best_po}, best_pl={best_pl}", flush=True)

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
