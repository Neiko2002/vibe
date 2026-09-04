import json
import math
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
from generate_report import generate_markdown_report

GLASS_REFERENCE = {
    0.90: 7897.4,
    0.95: 6210.1,
    0.98: 4287.6,
    0.99: 3319.7,
    0.995: 2300.3,
    0.999: 1763.8,
}

RUN7_BASELINE = {
    0.90: 12078.1,
    0.95: 7757.4,
    0.98: 4273.9,
    0.99: 3360.3,
    0.995: 2547.9,
    0.999: 1533.9,
}


def main():
    dataset_name = "yandex-200-cosine"
    count = 100
    runs = 2

    print(f"=== AutoResearch Benchmark: DEG-QG vs Glass ({dataset_name}, count={count}) ===", flush=True)
    t_start = time.time()

    # 1. Load dataset
    print(f"Loading dataset '{dataset_name}'...", flush=True)
    X_train, X_test, distance = load_and_transform_dataset(dataset_name)

    # 2. Get DEG-QG definition
    defs = [d for d in get_definitions(dimension=X_train.shape[1], distance_metric=distance) if d.algorithm == "deg-qg"]
    if not defs:
        print("Error: No DEG-QG definition found!", file=sys.stderr)
        sys.exit(1)
    definition = defs[0]

    # 3. Ground truth for Recall@100
    gt_file = Path(f"data/{dataset_name}.hdf5")
    if not gt_file.exists():
        print(f"Error: Ground truth file {gt_file} not found!", file=sys.stderr)
        sys.exit(1)
    with h5py.File(str(gt_file), "r") as f_gt:
        gt_distances = f_gt["distances"][:, :count]

    # 4. Build / load index
    print(f"Instantiating {definition.algorithm} with args: {definition.arguments}...", flush=True)
    algo = instantiate_algorithm(definition)
    build_time, index_size = build_index(algo, definition.constructor, X_train, None, None)
    print(f"Index ready in {build_time:.2f}s (size: {index_size:.1f} KB)", flush=True)

    # Cooling down CPU briefly
    gc.collect()
    time.sleep(2)

    # 5. Run queries
    summary_records = []
    print(f"Running {len(definition.query_argument_groups)} query evaluations...", flush=True)
    for pos, query_arguments in enumerate(definition.query_argument_groups, 1):
        algo.set_query_arguments(*query_arguments)
        descriptor, results = run_individual_query(
            algo, X_train, X_test, distance, count, runs, definition.gpu
        )

        rerank_factor = float(query_arguments[0])
        raw_param = query_arguments[1]
        is_ef = isinstance(raw_param, int) or (isinstance(raw_param, float) and raw_param >= 1.0 and raw_param.is_integer())
        ef_val = int(raw_param) if is_ef else 0
        eps_val = float(raw_param) if not is_ef else 0.0

        # Compute official distance-threshold Recall@100
        run_distances = np.array([[dist for _, dist in res] for _, res in results])
        eps_tol = 1e-3
        t_threshold = gt_distances[:, count - 1] + eps_tol
        recalls = np.array([(run_distances[i] <= t_threshold[i]).sum() for i in range(len(run_distances))]) / float(count)
        mean_recall = float(recalls.mean())
        qps = float(descriptor.get("best_qps", 0))
        latency_ms = float(descriptor.get("best_search_time", 0)) * 1000

        summary_records.append({
            "config": str(definition.arguments),
            "k": definition.arguments[1],
            "opt_target": definition.arguments[2],
            "prune_rng": definition.arguments[3],
            "rerank_factor": rerank_factor,
            "eps": eps_val,
            "ef": ef_val,
            "recall_100": mean_recall,
            "qps": qps,
            "search_time_ms": latency_ms,
            "build_time_s": float(build_time),
            "index_size_kb": float(index_size),
        })

    total_eval_time = time.time() - t_start
    print(f"Evaluations complete in {total_eval_time:.1f}s", flush=True)

    # 6. Compute Pareto tier metrics
    tiers = [0.90, 0.95, 0.98, 0.99, 0.995, 0.999]
    tier_qps = {}
    tier_records = {}
    for t in tiers:
        candidates = [d for d in summary_records if d["recall_100"] >= t]
        if candidates:
            best = max(candidates, key=lambda x: x["qps"])
            tier_qps[t] = best["qps"]
            tier_records[t] = best
        else:
            tier_qps[t] = 0.0
            tier_records[t] = None

    # Calculate Pareto geometric mean
    if all(tier_qps[t] > 0 for t in tiers):
        prod = 1.0
        for t in tiers:
            prod *= tier_qps[t]
        pareto_qps = prod ** (1.0 / len(tiers))
    else:
        pareto_qps = 0.0

    max_recall = max(d["recall_100"] for d in summary_records) if summary_records else 0.0

    # 7. Print summary table
    print("\n" + "=" * 90)
    print(f"{'Recall Tier':<12} | {'Current QPS':<11} | {'Glass Ref':<10} | {'vs Glass':<10} | {'Run 7 Base':<10} | {'vs Run 7':<10} | {'Config'}")
    print("-" * 90)
    for t in tiers:
        q_curr = tier_qps[t]
        q_glass = GLASS_REFERENCE.get(t, 0.0)
        q_run7 = RUN7_BASELINE.get(t, 0.0)
        diff_glass = ((q_curr / q_glass - 1.0) * 100) if q_glass > 0 and q_curr > 0 else 0.0
        diff_run7 = ((q_curr / q_run7 - 1.0) * 100) if q_run7 > 0 and q_curr > 0 else 0.0
        best_r = tier_records[t]
        cfg_str = f"rerank={best_r['rerank_factor']:.1f}x, ef={best_r['ef']}" if best_r else "N/A"
        sign_g = "+" if diff_glass >= 0 else ""
        sign_7 = "+" if diff_run7 >= 0 else ""
        print(f">={t*100:4.1f}%     | {q_curr:9.1f}   | {q_glass:8.1f}   | {sign_g}{diff_glass:6.1f}%    | {q_run7:8.1f}   | {sign_7}{diff_run7:6.1f}%   | {cfg_str}")
    print("=" * 90)
    print(f"Geometric Mean (pareto_qps): {pareto_qps:.1f} QPS (Glass: 3845.8 QPS, Run 7: 4148.9 QPS)")
    print(f"Maximum Recall reached: {max_recall*100:.2f}%\n")

    # 8. Save results
    results_dir = Path("results") / dataset_name
    results_dir.mkdir(parents=True, exist_ok=True)
    summary_file = results_dir / "deg_qg_autoresearch_latest.json"
    with open(summary_file, "w") as f:
        json.dump(summary_records, f, indent=2)

    report_file = results_dir / "DEG_QG_AUTORESEARCH_LATEST.md"
    generate_markdown_report(f"{dataset_name}-DEG-QG-AUTORESEARCH", summary_records, report_file)

    # 9. Output canonical METRIC lines
    print(f"METRIC pareto_qps={pareto_qps:.1f}")
    print(f"METRIC qps_rec999={tier_qps[0.999]:.1f}")
    print(f"METRIC qps_rec995={tier_qps[0.995]:.1f}")
    print(f"METRIC qps_rec99={tier_qps[0.99]:.1f}")
    print(f"METRIC qps_rec98={tier_qps[0.98]:.1f}")
    print(f"METRIC qps_rec95={tier_qps[0.95]:.1f}")
    print(f"METRIC qps_rec90={tier_qps[0.90]:.1f}")
    print(f"METRIC max_recall={max_recall:.4f}")
    print(f"METRIC build_time={build_time:.2f}")


if __name__ == "__main__":
    main()
