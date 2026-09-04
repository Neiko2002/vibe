import json
import os
import sys
import time
from pathlib import Path
import numpy as np
import h5py

from vibe.definitions import get_definitions, instantiate_algorithm
from vibe.runner import load_and_transform_dataset, run_individual_query, build_index
from vibe.results import store_results


def run_benchmark():
    dataset_name = "yandex-200-cosine"
    count = 100
    runs = 2
    
    print(f"=== Starting VIBE Benchmark for DEG on {dataset_name} (count={count}) ===", flush=True)
    t_start_total = time.time()
    
    # 1. Load dataset
    print(f"Loading dataset '{dataset_name}'...", flush=True)
    t0 = time.time()
    X_train, X_test, distance = load_and_transform_dataset(dataset_name)
    print(f"Dataset loaded in {time.time() - t0:.2f}s: train={X_train.shape}, test={X_test.shape}, distance={distance}", flush=True)

    # 2. Get DEG definitions
    defs = [d for d in get_definitions(dimension=X_train.shape[1], distance_metric=distance) if d.algorithm == "deg"]
    print(f"Found {len(defs)} parameter configurations for DEG.", flush=True)

    summary_records = []
    summary_file = Path("results") / dataset_name / "deg_summary_top100.json"
    summary_file.parent.mkdir(parents=True, exist_ok=True)

    # Load Ground Truth distances for official VIBE Recall@100 computation
    with h5py.File(f"data/{dataset_name}.hdf5", "r") as f_gt:
        gt_distances = f_gt["distances"][:, :count]

    for idx, definition in enumerate(defs, 1):
        print(f"\n[{idx}/{len(defs)}] Configuring DEG with arguments: {definition.arguments}", flush=True)
        algo = instantiate_algorithm(definition)
        build_time, index_size = build_index(algo, definition.constructor, X_train, None, None)
        print(f"Index built in {build_time:.2f}s, index size: {index_size:.2f} KB", flush=True)

        for pos, query_arguments in enumerate(definition.query_argument_groups, 1):
            algo.set_query_arguments(*query_arguments)

            descriptor, results = run_individual_query(
                algo, X_train, X_test, distance, count, runs, definition.gpu
            )

            descriptor.update({
                "build_time": build_time,
                "index_size": index_size,
                "algo": definition.algorithm,
                "dataset": dataset_name,
                "k": definition.arguments[1],
                "opt_target": definition.arguments[2],
                "prune_non_rng": definition.arguments[3],
                "search_eps": query_arguments[0],
            })

            # Store standard VIBE HDF5 result under results/yandex-200-cosine/100/deg/
            store_results(dataset_name, count, definition, query_arguments, descriptor, results, definition.gpu)

            # Compute official VIBE distance-threshold Recall@100
            run_distances = np.array([[dist for _, dist in res] for _, res in results])
            eps_tol = 1e-3
            t_threshold = gt_distances[:, count - 1] + eps_tol
            recalls = np.array([(run_distances[i] <= t_threshold[i]).sum() for i in range(len(run_distances))]) / float(count)
            mean_recall = float(recalls.mean())
            qps = float(descriptor.get("best_qps", 0))
            latency_ms = float(descriptor.get("best_search_time", 0)) * 1000

            print(f"  -> [{pos}/{len(definition.query_argument_groups)}] eps={query_arguments[0]:5.3f} | Recall@100: {mean_recall*100:6.2f}% | QPS: {qps:7.1f} | Latency: {latency_ms:5.3f}ms", flush=True)

            rec = {
                "config": str(definition.arguments),
                "k": definition.arguments[1],
                "opt_target": definition.arguments[2],
                "prune_rng": definition.arguments[3],
                "eps": query_arguments[0],
                "recall_100": mean_recall,
                "qps": qps,
                "search_time_ms": latency_ms,
                "build_time_s": float(build_time),
                "index_size_kb": float(index_size),
            }
            summary_records.append(rec)

            with open(summary_file, "w") as f:
                json.dump(summary_records, f, indent=2)

    total_time = time.time() - t_start_total
    print(f"\n=== Top-100 Benchmark Complete in {total_time/60:.2f} minutes! ===", flush=True)


if __name__ == "__main__":
    run_benchmark()
