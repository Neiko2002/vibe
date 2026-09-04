from pathlib import Path


def generate_markdown_report(dataset_name, data, output_path):
    md = []
    md.append(f"# DEG Benchmark Results: `{dataset_name}` (Top-100 / Recall@100)\n")
    md.append(f"- **Dataset**: `{dataset_name}` (1,000,000 base vectors, 1,000 queries, metric = Cosine)")
    md.append("- **Benchmark Setting**: Single-Core, $K_{\\text{search}} = 100$ (`count=100`)")
    md.append(f"- **Evaluations in Report**: {len(data)}\n")
    md.append("---\n")

    # 1. Stufen-Tabelle (Pareto-Stufen)
    md.append("## 1. Pareto-Stufen Übersicht (Beste QPS ab Recall-Schwellenwert)\n")
    md.append("| Ziel-Stufe | Recall@100 | QPS (Single-Core) | Latency / Query | Config ($K$, Target, Pruning) | rerank | search_eps |")
    md.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |")

    tiers = [0.70, 0.75, 0.80, 0.85, 0.90, 0.92, 0.95, 0.97, 0.98, 0.99, 0.995, 0.999, 1.0]
    for t in tiers:
        candidates = [d for d in data if d["recall_100"] >= t]
        if candidates:
            best = max(candidates, key=lambda x: x["qps"])
            prune_str = "Pruned" if best["prune_rng"] else "No-Prune"
            rerank_str = f"{best.get('rerank_factor', 1.0):.1f}x"
            param_col = f"`ef={best['ef']}`" if best.get("ef", 0) > 0 else f"`eps={best['eps']}`"
            md.append(f"| **$\\ge {t*100:4.1f}\\%$** | **{best['recall_100']*100:6.2f} %** | **{best['qps']:7.1f}** | {best['search_time_ms']:5.2f} ms | $K={best['k']}$, {best['opt_target']}, {prune_str} | `{rerank_str}` | {param_col} |")
    md.append("\n---\n")

    # 2. Detailed Breakdown per Configuration
    md.append("## 2. Vollständige Aufschlüsselung aller Konfigurationen\n")
    from collections import defaultdict
    grouped = defaultdict(list)
    for d in data:
        grouped[d["config"]].append(d)

    for config_str, records in grouped.items():
        r0 = records[0]
        prune_str = "Enabled (prune_non_rng=True)" if r0["prune_rng"] else "Disabled (prune_non_rng=False)"
        md.append(f"### Configuration: $K={r0['k']}$ | `{r0['opt_target']}` | RNG-Pruning: {prune_str}")
        md.append(f"- **Build Time**: {r0['build_time_s']:.1f} s ({r0['build_time_s']/60:.2f} min)")
        md.append(f"- **Index Memory**: {r0['index_size_kb']/1024:.1f} MB\n")
        
        has_rerank = "rerank_factor" in r0
        if has_rerank:
            md.append("| `rerank_factor` | `param` | Recall@100 | QPS (Single-Core) | Latency / Query |")
            md.append("| :--- | :--- | :--- | :--- | :--- |")
            for r in records:
                param_str = f"`ef={r['ef']}`" if r.get("ef", 0) > 0 else f"`eps={r['eps']:5.3f}`"
                md.append(f"| `{r['rerank_factor']:.1f}x` | {param_str} | **{r['recall_100']*100:6.2f} %** | {r['qps']:7.1f} | {r['search_time_ms']:5.2f} ms |")
        else:
            md.append("| `search_eps` | Recall@100 | QPS (Single-Core) | Latency / Query |")
            md.append("| :--- | :--- | :--- | :--- |")
            for r in records:
                md.append(f"| `{r['eps']:5.3f}` | **{r['recall_100']*100:6.2f} %** | {r['qps']:7.1f} | {r['search_time_ms']:5.2f} ms |")
        md.append("\n")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    print(f"Report saved at {output_path}")
