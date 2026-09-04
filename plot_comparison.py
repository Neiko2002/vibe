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

    # Alle DEG Runs lückenlos von Run 0 bis zum neuesten Rekord (Run 16/17):
    runs = {
        "glass": (glass_pareto, {
            "color": "#D90429", "label": "Glass Referenz (Vollständige Pareto-Front, R=16..48)", "marker": "o", "lw": 3.0, "ms": 7, "zorder": 12
        }),
        "r0": (get_pareto_frontier(load_run("results/yandex-200-cosine/deg_qg_baseline_eps_top100.json")), {
            "color": "#ADB5BD", "label": "Run 0: Baseline (eps-Radius, K=48)", "marker": "x", "lw": 1.3, "ms": 5, "ls": ":", "zorder": 2
        }),
        "r1": (get_pareto_frontier(load_run("results/yandex-200-cosine/deg_qg_summary_top100_linear_pool.json")), {
            "color": "#8D99AE", "label": "Run 1: LinearPool ef", "marker": "+", "lw": 1.4, "ms": 5, "ls": "--", "zorder": 3
        }),
        "r2": (get_pareto_frontier(load_run("results/yandex-200-cosine/deg_qg_summary_top100_run2.json")), {
            "color": "#4A90E2", "label": "Run 2: 64 Medoids + Edge Prefetch", "marker": "v", "lw": 1.5, "ms": 5, "ls": "-.", "zorder": 4
        }),
        "r3": (get_pareto_frontier(load_run("results/yandex-200-cosine/deg_qg_summary_top100_run3.json")), {
            "color": "#00B4D8", "label": "Run 3: Auto Prefetch (po=14, pl=4)", "marker": "^", "lw": 1.6, "ms": 5, "ls": "-.", "zorder": 5
        }),
        "r4": (get_pareto_frontier(load_run("results/yandex-200-cosine/deg_qg_summary_top100_run4.json")), {
            "color": "#0077B6", "label": "Run 4: 128 KM Medoids + Top-2 Entry", "marker": "s", "lw": 1.7, "ms": 5, "zorder": 6
        }),
        "r5": (get_pareto_frontier(load_run("results/yandex-200-cosine/deg_qg_summary_top100_run5.json")), {
            "color": "#52B788", "label": "Run 5: Unrolled AVX-512 VNNI D=200", "marker": "p", "lw": 1.8, "ms": 5, "zorder": 7
        }),
        "r6": (get_pareto_frontier(load_run("results/yandex-200-cosine/deg_qg_summary_top100_run6.json")), {
            "color": "#2D6A4F", "label": "Run 6: Vector Tail + 4CL Prefetch (Fine Grid)", "marker": "h", "lw": 2.0, "ms": 6, "zorder": 8
        }),
        "r7": (get_pareto_frontier(load_run("results/yandex-200-cosine/deg_qg_summary_top100_run7.json") + load_run("results/yandex-200-cosine/deg_qg_summary_top100_run6.json")), {
            "color": "#081C15", "label": "Run 7: Contiguous 256B Aligned + Adaptiv Rerank", "marker": "D", "lw": 2.2, "ms": 6, "ls": "--", "zorder": 9
        }),
        "phase2": (get_pareto_frontier(load_run("results/yandex-200-cosine/deg_qg_summary_top100_phase2_final.json")), {
            "color": "#7209B7", "label": "Phase 2 (Run 11): Feines ef-Gitter & Rerank (4.233 QPS)", "marker": "*", "lw": 2.4, "ms": 7, "ls": "-.", "zorder": 10
        }),
        "r16": (get_pareto_frontier(load_run("results/yandex-200-cosine/deg_qg_summary_top100_run16_latest.json")), {
            "color": "#F77F00", "label": "Run 16: AVX-512 F16C Batch Reranker (4.363 QPS)", "marker": "^", "lw": 2.2, "ms": 7, "ls": "--", "zorder": 13
        }),
        "r24": (get_pareto_frontier(load_run("results/yandex-200-cosine/deg_qg_autoresearch_latest.json")), {
            "color": "#9B5DE5", "label": "Aktueller Rekord (Run 24): 4.509 QPS (1.713 QPS @ 99.9%)", "marker": "*", "lw": 3.8, "ms": 11, "zorder": 16
        }),
    }

    fig, ax = plt.subplots(figsize=(13, 8.5), dpi=300)

    for run_key, (pareto, style) in runs.items():
        px = [p["recall"] for p in pareto if p["recall"] >= 0.88]
        py = [p["qps"] for p in pareto if p["recall"] >= 0.88]
        ax.plot(px, py, **style)

    ax.set_xlim(0.89, 1.0015)
    ax.set_ylim(800, 14000)
    ax.set_xlabel("Recall@100", fontsize=13, fontweight="bold")
    ax.set_ylabel("QPS (Queries / Sekunde)", fontsize=13, fontweight="bold")
    ax.set_title("Vollständige AutoResearch Evolution: ALLE Verbesserungen vs. Glass auf yandex-200-cosine (Single-Core)",
                 fontsize=14, fontweight="bold", pad=15)
    ax.grid(True, which="both", ls=":", alpha=0.6)
    ax.legend(loc="upper right", fontsize=9.5, framealpha=0.95)

    # Reale Vergleiche & Lücken-Annotationen
    # Reale Vergleiche & Lücken-Annotationen (ohne Überlappung)
    ax.annotate("Run 7 / Aktuell (ef=80)\n11.890 QPS @ 90.56% (+50.5% vs Glass)", (0.9056, 11890.3), textcoords="offset points", xytext=(20, 20),
                arrowprops=dict(arrowstyle="->", color="#081C15", lw=1.3), fontsize=9, color="#081C15", fontweight="bold")
    ax.annotate("Glass (R=48, ef=20)\n7.897 QPS @ 94.88%", (0.9488, 7897.4), textcoords="offset points", xytext=(-130, -45),
                arrowprops=dict(arrowstyle="->", color="#D90429", lw=1.3), fontsize=9, color="#D90429", fontweight="bold")
    ax.annotate("Run 7 / Aktuell (ef=150)\n7.706 QPS @ 95.25% (+24.1% vs Glass)", (0.9525, 7706.4), textcoords="offset points", xytext=(25, 25),
                arrowprops=dict(arrowstyle="->", color="#081C15", lw=1.3), fontsize=9, color="#081C15", fontweight="bold")
    ax.annotate("Aktuell Run 24 (ef=250)\n4.921 QPS @ 98.41% (+14.8% vs Glass 4.288)", (0.9841, 4920.8), textcoords="offset points", xytext=(-170, 35),
                arrowprops=dict(arrowstyle="->", color="#9B5DE5", lw=1.5), fontsize=9, color="#9B5DE5", fontweight="bold")
    ax.annotate("Aktuell Run 24 (ef=350)\n3.722 QPS @ 99.09% (+12.1% vs Glass 3.320)", (0.9909, 3722.3), textcoords="offset points", xytext=(-170, 25),
                arrowprops=dict(arrowstyle="->", color="#9B5DE5", lw=1.5), fontsize=9, color="#9B5DE5", fontweight="bold")
    ax.annotate("Aktuell Run 24 (ef=500)\n2.753 QPS @ 99.57% (+19.7% vs Glass 2.300)", (0.9957, 2753.1), textcoords="offset points", xytext=(25, 25),
                arrowprops=dict(arrowstyle="->", color="#9B5DE5", lw=1.5), fontsize=9, color="#9B5DE5", fontweight="bold")
    ax.annotate("Aktuell Run 24 (1.35x, ef=845)\n1.713 QPS @ 99.90% (Glass: 1.764 QPS)", (0.9990, 1713.4), textcoords="offset points", xytext=(-185, -45),
                arrowprops=dict(arrowstyle="->", color="#9B5DE5", lw=1.5), fontsize=9, color="#9B5DE5", fontweight="bold")
    ax.annotate("Glass (ef=1000)\n1.421 QPS @ 99.96%", (0.9996, 1421.0), textcoords="offset points", xytext=(-110, -45),
                arrowprops=dict(arrowstyle="->", color="#D90429", lw=1.3), fontsize=9, color="#D90429", fontweight="bold")
    output_path = "results/yandex-200-cosine/deg_vs_glass_yandex_top100.png"
    plt.savefig(output_path, bbox_inches="tight")
    print(f"Plot successfully saved at {output_path}")


if __name__ == "__main__":
    main()
