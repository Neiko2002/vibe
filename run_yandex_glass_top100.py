import json
import os
import sys
import time
import gc
from pathlib import Path
import numpy as np
import h5py

from vibe.definitions import get_definitions, instantiate_algorithm
from vibe.runner import load_and_transform_dataset, run_individual_query, build_index
from vibe.results import store_results
from generate_glass_report import generate_glass_markdown_report


def run_benchmark():
    dataset_name = "yandex-200-cosine"
    count = 100
    runs = 2

    print(f"=== Starting VIBE Benchmark for GLASS on {dataset_name} (count={count}) ===", flush=True)
    t_start_total = time.time()

    # 1. Load dataset (opens local data/yandex-200-cosine.hdf5)
    print(f"Loading dataset '{dataset_name}' from local disk...", flush=True)
    t0 = time.time()
    X_train, X_test, distance = load_and_transform_dataset(dataset_name)
    print(
        f"Dataset loaded in {time.time() - t0:.2f}s: train={X_train.shape}, test={X_test.shape}, distance={distance}",
        flush=True,
    )

    # 2. Get GLASS definitions
    defs = [
        d
        for d in get_definitions(dimension=X_train.shape[1], distance_metric=distance)
        if d.algorithm == "glass"
    ]
    if not defs:
        print("ERROR: No Glass definitions found!", flush=True)
        sys.exit(1)

    print(
        f"Found {len(defs)} parameter configurations for GLASS ({len(defs[0].query_argument_groups)} query ef settings each).",
        flush=True,
    )

    summary_records = []
    summary_file = Path("results") / dataset_name / "glass_summary_top100_LINUX.json"
    summary_file.parent.mkdir(parents=True, exist_ok=True)
    report_file = Path("results") / dataset_name / "GLASS_YANDEX_TOP100_RESULTS_LINUX.md"

    # Load Ground Truth distances for official VIBE Recall@100 computation
    with h5py.File(f"data/{dataset_name}.hdf5", "r") as f_gt:
        gt_distances = f_gt["distances"][:, :count]

    for idx, definition in enumerate(defs, 1):
        # definition.arguments: [metric, L, R, quant, search_quant, refine_quant]
        metric, L, R, quant, search_quant, refine_quant = definition.arguments
        print(
            f"\n[{idx}/{len(defs)}] Configuring GLASS: L={L}, R={R}, quant={quant}, search_quant={search_quant}, refine_quant={refine_quant}",
            flush=True,
        )

        algo = instantiate_algorithm(definition)
        build_time, index_size = build_index(algo, definition.constructor, X_train, None, None)
        print(f"Index built in {build_time:.2f}s, index size: {index_size:.2f} KB", flush=True)

        # Cleanup, Garbage Collection and Cooldown Sleep after Graph Build
        print("Cleaning memory and cooling down CPU for 5 seconds before queries...", flush=True)
        gc.collect()
        time.sleep(5)

        for pos, query_arguments in enumerate(definition.query_argument_groups, 1):
            ef = query_arguments[0]
            algo.set_query_arguments(*query_arguments)

            descriptor, results = run_individual_query(
                algo, X_train, X_test, distance, count, runs, definition.gpu
            )

            descriptor.update({
                "build_time": build_time,
                "index_size": index_size,
                "algo": definition.algorithm,
                "dataset": dataset_name,
                "L": L,
                "R": R,
                "quant": quant,
                "search_quant": search_quant,
                "refine_quant": refine_quant,
                "ef": ef,
            })

            # Store standard VIBE HDF5 result under results/yandex-200-cosine/100/glass/
            store_results(
                dataset_name,
                count,
                definition,
                query_arguments,
                descriptor,
                results,
                definition.gpu,
            )

            # Compute official VIBE distance-threshold Recall@100
            run_distances = np.array([[dist for _, dist in res] for _, res in results])
            eps_tol = 1e-3
            t_threshold = gt_distances[:, count - 1] + eps_tol
            recalls = np.array(
                [(run_distances[i] <= t_threshold[i]).sum() for i in range(len(run_distances))]
            ) / float(count)
            mean_recall = float(recalls.mean())
            qps = float(descriptor.get("best_qps", 0))
            latency_ms = float(descriptor.get("best_search_time", 0)) * 1000

            print(
                f"  -> [{pos:2d}/{len(definition.query_argument_groups)}] ef={ef:4d} | Recall@100: {mean_recall*100:6.2f}% | QPS: {qps:7.1f} | Latency: {latency_ms:5.3f}ms",
                flush=True,
            )

            rec = {
                "config": str(definition.arguments),
                "L": L,
                "R": R,
                "quant": quant,
                "search_quant": search_quant,
                "refine_quant": refine_quant,
                "ef": ef,
                "recall_100": mean_recall,
                "qps": qps,
                "search_time_ms": latency_ms,
                "build_time_s": float(build_time),
                "index_size_kb": float(index_size),
            }
            summary_records.append(rec)

            # Continuous write of summary json so progress is saved
            with open(summary_file, "w") as f:
                json.dump(summary_records, f, indent=2)

    total_time = time.time() - t_start_total
    print(
        f"\n=== GLASS Top-100 Benchmark Complete in {total_time/60:.2f} minutes! ===",
        flush=True,
    )

    # Generate Markdown Report
    generate_glass_markdown_report(
        dataset_name=dataset_name,
        data=summary_records,
        output_path=report_file,
    )


if __name__ == "__main__":
    run_benchmark()
