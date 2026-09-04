import json
import matplotlib.pyplot as plt


def get_pareto_frontier(points):
    """Computes the upper-right Pareto frontier (sorted by recall ascending)."""
    sorted_pts = sorted(points, key=lambda p: (p["recall"], p["qps"]))
    pareto = []
    for p in sorted_pts:
        while pareto and pareto[-1]["qps"] <= p["qps"]:
            pareto.pop()
        pareto.append(p)
    return pareto


def load_run(json_path):
    with open(json_path) as f:
        data = json.load(f)
    return [
        {"recall": d["recall_100"], "qps": d["qps"], "param": f"ef={d.get('ef', d.get('eps', 0))}"}
        for d in data
    ]


def main():
    # 1. Vollständige Glass Referenz (Pareto-Front über alle R und ef Konfigurationen)
    with open("results/yandex-200-cosine/glass_summary_top100_LINUX.json") as f:
        glass_all = json.load(f)
    glass_all_pts = [
        {"recall": g["recall_100"], "qps": g["qps"], "param": f"R={g['R']}, ef={g['ef']}"}
        for g in glass_all
        if g["quant"] == "SQ8U"
    ]
    glass_pareto = get_pareto_frontier(glass_all_pts)

    # Alle DEG Runs lückenlos von Run 0 bis Run 7:
    runs = {
        "glass": (glass_pareto, {
            "color": "#D90429", "label": "Glass Referenz (Vollständige Pareto-Front, R=16..48)", "marker": "o", "lw": 3.0, "ms": 7, "zorder": 12
        }),
        "r0": (get_pareto_frontier(load_run("results/yandex-200-cosine/deg_qg_baseline_eps_top100.json")), {
            "color": "#ADB5BD", "label": "Run 0: Baseline (eps-Radius, K=48)", "marker": "x", "lw": 1.4, "ms": 5, "ls": ":", "zorder": 2
        }),
        "r1": (get_pareto_frontier(load_run("results/yandex-200-cosine/deg_qg_summary_top100_linear_pool.json")), {
            "color": "#8D99AE", "label": "Run 1: LinearPool ef", "marker": "+", "lw": 1.5, "ms": 6, "ls": "--", "zorder": 3
        }),
        "r2": (get_pareto_frontier(load_run("results/yandex-200-cosine/deg_qg_summary_top100_run2.json")), {
            "color": "#4A90E2", "label": "Run 2: 64 Medoids + Edge Prefetch", "marker": "v", "lw": 1.7, "ms": 5, "ls": "-.", "zorder": 4
        }),
        "r3": (get_pareto_frontier(load_run("results/yandex-200-cosine/deg_qg_summary_top100_run3.json")), {
            "color": "#00B4D8", "label": "Run 3: Auto Prefetch (po=14, pl=4)", "marker": "^", "lw": 1.8, "ms": 5, "ls": "-.", "zorder": 5
        }),
        "r4": (get_pareto_frontier(load_run("results/yandex-200-cosine/deg_qg_summary_top100_run4.json")), {
            "color": "#0077B6", "label": "Run 4: 128 KM Medoids + Top-2 Entry", "marker": "s", "lw": 2.0, "ms": 6, "zorder": 6
        }),
        "r5": (get_pareto_frontier(load_run("results/yandex-200-cosine/deg_qg_summary_top100_run5.json")), {
            "color": "#52B788", "label": "Run 5: Unrolled AVX-512 VNNI D=200", "marker": "p", "lw": 2.2, "ms": 6, "zorder": 7
        }),
        "r6": (get_pareto_frontier(load_run("results/yandex-200-cosine/deg_qg_summary_top100_run6.json")), {
            "color": "#2D6A4F", "label": "Run 6: Vector Tail + 4CL Prefetch (Fine Grid)", "marker": "h", "lw": 2.5, "ms": 7, "zorder": 8
        }),
        "r7": (get_pareto_frontier(load_run("results/yandex-200-cosine/deg_qg_summary_top100_run7.json") + load_run("results/yandex-200-cosine/deg_qg_summary_top100_run6.json")), {
            "color": "#081C15", "label": "DEG-QG Run 7 (Bester Stand: 256B Aligned + Adaptiv Rerank)", "marker": "D", "lw": 3.2, "ms": 8, "zorder": 11
        }),
    }

    fig, ax = plt.subplots(figsize=(13, 8.5), dpi=300)

    for run_key, (pareto, style) in runs.items():
        px = [p["recall"] for p in pareto if p["recall"] >= 0.88]
        py = [p["qps"] for p in pareto if p["recall"] >= 0.88]
        ax.plot(px, py, **style)

    ax.set_xlim(0.93, 1.001)
    ax.set_ylim(1000, 11000)
    ax.set_xlabel("Recall@100", fontsize=13, fontweight="bold")
    ax.set_ylabel("QPS (Queries / Sekunde)", fontsize=13, fontweight="bold")
    ax.set_title("Echter Pareto-Vergleich im Fokus-Bereich (Recall >= 94%): Glass vs. DEG-QG (Single-Core)",
                 fontsize=14, fontweight="bold", pad=15)
    ax.grid(True, which="both", ls=":", alpha=0.6)
    ax.legend(loc="upper right", fontsize=10, framealpha=0.95)

    # Reale Vergleiche & Lücken-Annotationen
    ax.annotate("Glass (R=48, ef=20)\n7.897 QPS @ 94.88% (führt vor DEG 7.623)", (0.9488, 7897.4), textcoords="offset points", xytext=(20, 20),
                arrowprops=dict(arrowstyle="->", color="#D90429", lw=1.3), fontsize=9, color="#D90429", fontweight="bold")
    ax.annotate("Glass (R=48, ef=200)\n6.210 QPS @ 96.82% (führt vor DEG 5.127)", (0.9682, 6210.1), textcoords="offset points", xytext=(-120, 25),
                arrowprops=dict(arrowstyle="->", color="#D90429", lw=1.3), fontsize=9, color="#D90429", fontweight="bold")
    ax.annotate("DEG Run 7 (1.15x, ef=250)\n4.526 QPS @ 98.41% vs Glass 4.313", (0.9841, 4525.6), textcoords="offset points", xytext=(-130, 25),
                arrowprops=dict(arrowstyle="->", color="#081C15", lw=1.3), fontsize=9, color="#081C15", fontweight="bold")
    ax.annotate("Glass führt bei 99.9%:\n1.764 QPS @ 99.90% (DEG: 1.577 QPS, -10.6%)", (0.9990, 1763.8), textcoords="offset points", xytext=(-180, 25),
                arrowprops=dict(arrowstyle="->", color="#D90429", lw=1.5), fontsize=9, color="#D90429", fontweight="bold")
    ax.annotate("Glass erreicht 99.96% (1.421 QPS)\nDEG bricht bei 99.91% ab!", (0.9996, 1421.0), textcoords="offset points", xytext=(-160, -35),
                arrowprops=dict(arrowstyle="->", color="#D90429", lw=1.5), fontsize=9, color="#D90429", fontweight="bold")
    output_path = "results/yandex-200-cosine/deg_vs_glass_yandex_top100.png"
    plt.savefig(output_path, bbox_inches="tight")
    print(f"Plot successfully saved at {output_path}")


if __name__ == "__main__":
    main()
