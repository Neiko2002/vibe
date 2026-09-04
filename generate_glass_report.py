from pathlib import Path
from collections import defaultdict
import json


def generate_glass_markdown_report(dataset_name: str, data: list, output_path: Path):
    """
    Generates a comprehensive Markdown report for Glass benchmark results,
    matching the format of DEG_QG_YANDEX_TOP100_RESULTS_LINUX.md.
    Also compares against existing DEG / DEG-QG results if available.
    """
    md = []
    total_evals = len(data)
    unique_configs = len({d["config"] for d in data})

    md.append(f"# Glass Benchmark Results: `{dataset_name}` (Top-100 / Recall@100)\n")
    md.append(f"- **Algorithm**: `glass` (PyGlass / Zilliz Glass HNSW + Quantization)")
    md.append("- **Environment**: Docker (Linux x86_64 Ubuntu 24.04, Python 3.11)")
    md.append(f"- **Dataset**: `{dataset_name}` (1,000,000 base vectors, 1,000 queries, metric = Cosine)")
    md.append("- **Benchmark Setting**: Single-Core, $K_{\\text{search}} = 100$ (`count=100`)")
    md.append(f"- **Total Evaluations**: {unique_configs} index configurations $\\times$ query ef settings = **{total_evals} evaluations**\n")
    md.append("---\n")

    # 1. Pareto-Stufen Übersicht
    md.append("## 1. Pareto-Stufen Übersicht (Beste QPS ab Recall-Schwellenwert)\n")
    md.append("| Ziel-Stufe | Recall@100 | QPS (Single-Core) | Latency / Query | Config ($R$, $L$, Quant, Search, Refine) | `ef` |")
    md.append("| :--- | :--- | :--- | :--- | :--- | :--- |")

    tiers = [0.70, 0.75, 0.80, 0.85, 0.90, 0.92, 0.95, 0.97, 0.98, 0.99, 0.995, 0.999, 1.0]
    for t in tiers:
        candidates = [d for d in data if d["recall_100"] >= t]
        if candidates:
            best = max(candidates, key=lambda x: x["qps"])
            cfg_desc = f"R={best.get('R', '?')}, L={best.get('L', '?')}, {best.get('quant', '')}->{best.get('search_quant', '')}+{best.get('refine_quant', '')}"
            md.append(
                f"| **$\\ge {t*100:4.1f}\\%$** | **{best['recall_100']*100:6.2f} %** | "
                f"**{best['qps']:7.1f}** | {best['search_time_ms']:5.2f} ms | "
                f"`{cfg_desc}` | `ef={best.get('ef', '?')}` |"
            )

    md.append("\n---\n")

    # 2. Direkter Vergleich: DEG-QG vs. Glass (wenn DEG-QG Daten existieren)
    deg_qg_file = Path("results") / dataset_name / "deg_qg_summary_top100_LINUX.json"
    if deg_qg_file.exists():
        try:
            with open(deg_qg_file, "r") as f:
                deg_qg_data = json.load(f)
            
            md.append("## 2. Direkter Vergleich: DEG-QG (INT8) vs. Glass\n")
            md.append("| Ziel-Recall@100 | DEG-QG QPS | **Glass QPS** | **Speedup / Faktor** | Glass Beste Konfiguration |")
            md.append("| :--- | :--- | :--- | :--- | :--- |")

            for t in tiers:
                deg_candidates = [d for d in deg_qg_data if d["recall_100"] >= t]
                glass_candidates = [d for d in data if d["recall_100"] >= t]
                if deg_candidates and glass_candidates:
                    best_deg = max(deg_candidates, key=lambda x: x["qps"])
                    best_glass = max(glass_candidates, key=lambda x: x["qps"])
                    speedup = best_glass["qps"] / best_deg["qps"]
                    factor_str = f"**{speedup:.2f}x** ({'+' if speedup >= 1.0 else ''}{(speedup - 1.0)*100:.1f}%)"
                    g_cfg = f"R={best_glass['R']}, {best_glass['search_quant']}+{best_glass['refine_quant']} (ef={best_glass['ef']})"
                    md.append(
                        f"| **$\\ge {t*100:4.1f}\\%$** | {best_deg['qps']:7.1f} QPS | "
                        f"**{best_glass['qps']:7.1f} QPS** | {factor_str} | `{g_cfg}` |"
                    )
            md.append("\n---\n")
        except Exception as e:
            print(f"Warning: Could not load DEG-QG comparison data: {e}")

    # 3. Vollständige Aufschlüsselung aller Konfigurationen
    md.append(f"## 3. Vollständige Aufschlüsselung aller {unique_configs} Konfigurationen ({total_evals} Messpunkte)\n")
    grouped = defaultdict(list)
    for d in data:
        grouped[d["config"]].append(d)

    for config_str, records in grouped.items():
        r0 = records[0]
        md.append(
            f"### Configuration: $R={r0.get('R')}$, $L={r0.get('L')}$ | "
            f"Quant: `{r0.get('quant')}` | Search: `{r0.get('search_quant')}` | Refine: `{r0.get('refine_quant')}`"
        )
        md.append(f"- **Build Time**: {r0['build_time_s']:.1f} s ({r0['build_time_s']/60:.2f} min)")
        md.append(f"- **Index Memory**: {r0['index_size_kb']/1024:.1f} MB\n")

        md.append("| `ef` | Recall@100 | QPS (Single-Core) | Latency / Query |")
        md.append("| :--- | :--- | :--- | :--- |")
        for r in records:
            md.append(
                f"| `{r['ef']}` | **{r['recall_100']*100:6.2f} %** | "
                f"{r['qps']:7.1f} | {r['search_time_ms']:5.2f} ms |"
            )
        md.append("\n")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    print(f"Report saved at {output_path}")


if __name__ == "__main__":
    # Test script standalone if json exists
    dataset = "yandex-200-cosine"
    json_path = Path("results") / dataset / "glass_summary_top100_LINUX.json"
    if json_path.exists():
        with open(json_path, "r") as f:
            records = json.load(f)
        generate_glass_markdown_report(
            dataset, records, Path("results") / dataset / "GLASS_YANDEX_TOP100_RESULTS_LINUX.md"
        )
