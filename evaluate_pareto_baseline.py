import json
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np


def get_pareto_frontier(points):
    """Computes the upper-right Pareto frontier (sorted by recall ascending)."""
    sorted_pts = sorted(points, key=lambda p: (p["recall"], p["qps"]))
    pareto = []
    for p in sorted_pts:
        while pareto and pareto[-1]["qps"] <= p["qps"]:
            pareto.pop()
        pareto.append(p)
    return pareto


def load_glass_pareto(json_path="results/yandex-200-cosine/glass_summary_top100_LINUX.json"):
    with open(json_path) as f:
        glass_all = json.load(f)
    pts = [
        {
            "recall": g["recall_100"],
            "qps": g["qps"],
            "param": f"R={g['R']}, ef={g['ef']} ({g['search_quant']}+{g['refine_quant']})",
            "algo": "Glass",
        }
        for g in glass_all
        if g.get("quant") == "SQ8U"
    ]
    return get_pareto_frontier(pts)


def load_deg_qg_pareto(json_path="results/yandex-200-cosine/deg_qg_autoresearch_latest.json"):
    with open(json_path) as f:
        deg_all = json.load(f)
    pts = [
        {
            "recall": d["recall_100"],
            "qps": d["qps"],
            "param": f"rerank={d['rerank_factor']:.2f}x, ef={d['ef']}",
            "algo": "DEG-QG",
        }
        for d in deg_all
    ]
    return get_pareto_frontier(pts)


def plot_clean_pareto(glass_pareto, deg_pareto, output_path="results/yandex-200-cosine/deg_vs_glass_pareto_baseline.png"):
    fig, ax = plt.subplots(figsize=(11.5, 7.5), dpi=300)

    # 1. Glass Pareto line (Filter recall >= 0.88)
    gx = [p["recall"] for p in glass_pareto if p["recall"] >= 0.88]
    gy = [p["qps"] for p in glass_pareto if p["recall"] >= 0.88]
    ax.plot(gx, gy, color="#D90429", label="Glass Referenz (HNSW + SQ8U -> FP16/FP32)", marker="o", lw=2.8, ms=7, zorder=10)

    # 2. DEG-QG Pareto line
    dx = [p["recall"] for p in deg_pareto if p["recall"] >= 0.88]
    dy = [p["qps"] for p in deg_pareto if p["recall"] >= 0.88]
    ax.plot(dx, dy, color="#1D3557", label="DEG-QG Status Quo (K=48, INT8 -> FP16)", marker="s", lw=2.8, ms=6.5, zorder=12)

    # Format plot
    ax.set_xlim(0.89, 1.001)
    ax.set_ylim(1000, 13000)
    ax.set_xlabel("Recall@100 (Threshold Tol = 1e-3)", fontsize=12, fontweight="bold")
    ax.set_ylabel("QPS (Queries / Sekunde, Single-Core)", fontsize=12, fontweight="bold")
    ax.set_title("Saubere Pareto-Ausgangsbasis: Glass Referenz vs. DEG-QG\nDatensatz: yandex-200-cosine (Single-Core, Top-100)", fontsize=13, fontweight="bold", pad=15)
    ax.grid(True, which="both", ls=":", alpha=0.6)
    ax.legend(loc="upper right", fontsize=10.5, framealpha=0.95)

    # Specific matching comparison pairs (closest recall points)
    comparison_pairs = [
        # (Glass target recall, DEG target recall, label)
        (0.9488, 0.9525, "~95.0%"),
        (0.9682, 0.9671, "~96.8%"),
        (0.9833, 0.9841, "~98.4%"),
        (0.9906, 0.9909, "~99.1%"),
        (0.9962, 0.9957, "~99.6%"),
        (0.9990, 0.9990, "99.90%"),
    ]

    print("\n" + "=" * 96)
    print(f"{'Recall Bereich':14s} | {'Glass Referenz':25s} | {'DEG-QG Status Quo':25s} | {'Diff vs Glass':13s}")
    print("=" * 96)

    md_table = []
    md_table.append("| Recall-Bereich | Glass Referenz (Recall / QPS) | DEG-QG Status Quo (Recall / QPS) | Differenz | DEG-QG Parameter |")
    md_table.append("| :--- | :--- | :--- | :--- | :--- |")

    for g_rec, d_rec, label in comparison_pairs:
        # Find closest points
        g_point = min(glass_pareto, key=lambda p: abs(p["recall"] - g_rec))
        d_point = min(deg_pareto, key=lambda p: abs(p["recall"] - d_rec))

        diff_pct = (d_point["qps"] / g_point["qps"] - 1.0) * 100
        sign = "+" if diff_pct >= 0 else ""

        g_str = f"{g_point['recall']*100:5.2f}% @ {g_point['qps']:6.1f} QPS"
        d_str = f"{d_point['recall']*100:5.2f}% @ {d_point['qps']:6.1f} QPS"

        print(f"{label:14s} | {g_str:25s} | {d_str:25s} | {sign}{diff_pct:6.1f}%")
        md_table.append(f"| **{label}** | {g_str} (`{g_point['param']}`) | **{d_str}** | **{sign}{diff_pct:5.1f}%** | `{d_point['param']}` |")

    print("=" * 96 + "\n")

    # Annotations on plot
    # 1. Point at ~96.8%
    ax.annotate("Glass (ef=200): 6.210 QPS\nDEG (ef=200): 6.231 QPS", (0.9682, 6210.1),
                xytext=(-120, -45), textcoords="offset points", arrowprops=dict(arrowstyle="->", color="#333333", lw=1.2), fontsize=8.5, fontweight="bold")

    # 2. Point at ~98.4%
    ax.annotate("DEG (ef=250): 4.978 QPS\nGlass (ef=300): 4.313 QPS (+15.4%)", (0.9841, 4978.0),
                xytext=(-170, 25), textcoords="offset points", arrowprops=dict(arrowstyle="->", color="#1D3557", lw=1.2), fontsize=8.5, fontweight="bold", color="#1D3557")

    # 3. Point at ~99.1%
    ax.annotate("DEG (ef=350): 3.748 QPS\nGlass (ef=400): 3.320 QPS (+12.9%)", (0.9909, 3747.6),
                xytext=(-170, 20), textcoords="offset points", arrowprops=dict(arrowstyle="->", color="#1D3557", lw=1.2), fontsize=8.5, fontweight="bold", color="#1D3557")

    # 4. Point at 99.90%
    ax.annotate("Glass: 1.764 QPS (ef=800)\nDEG: 1.725 QPS (ef=845) (-2.2%)", (0.9990, 1724.8),
                xytext=(-170, -40), textcoords="offset points", arrowprops=dict(arrowstyle="->", color="#D90429", lw=1.2), fontsize=8.5, fontweight="bold", color="#D90429")

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, bbox_inches="tight")
    print(f"Clean comparison plot saved to: {output_path}")

    # Write clean Markdown table
    report_path = Path("results/yandex-200-cosine/PARETO_BASELINE_COMPARISON.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Saubere Pareto-Ausgangsbasis: Glass Referenz vs. DEG-QG\n\n")
        f.write("Dieses Dokument und der zugehörige Plot definieren die **unverfälschte Ausgangsbasis** für die anstehende systematische Evaluation und Bereinigung aller Teiländerungen.\n\n")
        f.write("![Glass vs DEG-QG](deg_vs_glass_pareto_baseline.png)\n\n")
        f.write("## 1. Direkter Pareto-Vergleich an deckungsgleichen Recall-Punkten\n\n")
        f.write("Im Gegensatz zu groben Schwellenwert-Sprüngen vergleicht diese Tabelle direkt die nah beieinander liegenden Messpunkte beider Pareto-Fronten:\n\n")
        f.write("\n".join(md_table) + "\n\n")
        f.write("## 2. Alle Pareto-Punkte von Glass\n\n")
        f.write("| Recall@100 | QPS | Konfiguration |\n| :--- | :--- | :--- |\n")
        for p in glass_pareto:
            if p["recall"] >= 0.88:
                f.write(f"| {p['recall']*100:6.2f} % | {p['qps']:7.1f} | `{p['param']}` |\n")
        f.write("\n## 3. Alle Pareto-Punkte von DEG-QG (Entzerrtes, wohlverteiltes Gitter)\n\n")
        f.write("| Recall@100 | QPS | Konfiguration |\n| :--- | :--- | :--- |\n")
        for p in deg_pareto:
            if p["recall"] >= 0.88:
                f.write(f"| {p['recall']*100:6.2f} % | {p['qps']:7.1f} | `{p['param']}` |\n")
    print(f"Clean Markdown report saved to: {report_path}")


def main():
    print("=== Extracting & Plotting Clean Pareto Baseline (Glass vs DEG-QG) ===")
    glass_pareto = load_glass_pareto()
    print(f"Glass Pareto frontier has {len(glass_pareto)} points.")

    deg_pareto = load_deg_qg_pareto()
    print(f"DEG-QG Pareto frontier has {len(deg_pareto)} points.")

    plot_clean_pareto(glass_pareto, deg_pareto)


if __name__ == "__main__":
    main()
