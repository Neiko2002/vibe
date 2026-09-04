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
    # 1. Glass Referenz
    with open("results/yandex-200-cosine/glass_summary_top100_LINUX.json") as f:
        glass_all = json.load(f)
    glass_r48 = [
        {"recall": g["recall_100"], "qps": g["qps"], "param": f"ef={g['ef']}"}
        for g in glass_all
        if g["R"] == 48 and g["quant"] == "SQ8U" and g["search_quant"] == "SQ8U" and g["refine_quant"] == "FP16"
    ]

    runs = {
        "glass": (get_pareto_frontier(glass_r48), {
            "color": "#D90429", "label": "Glass Referenz (HNSW R=48, SQ8U->FP16)", "marker": "o", "lw": 2.8, "ms": 7, "zorder": 10
        }),
        "base": (get_pareto_frontier(load_run("results/yandex-200-cosine/deg_qg_baseline_eps_top100.json")), {
            "color": "#CED4DA", "label": "DEG-QG Baseline (eps-Radius, K=48)", "marker": "x", "lw": 1.4, "ms": 4, "ls": ":", "zorder": 2
        }),
        "r1": (get_pareto_frontier(load_run("results/yandex-200-cosine/deg_qg_summary_top100_linear_pool.json")), {
            "color": "#ADB5BD", "label": "Run 1: LinearPool ef", "marker": "^", "lw": 1.5, "ms": 5, "ls": "--", "zorder": 3
        }),
        "r4": (get_pareto_frontier(load_run("results/yandex-200-cosine/deg_qg_summary_top100_run4.json")), {
            "color": "#457B9D", "label": "Run 4: 128 KM Medoids + Top-2 Entry", "marker": "P", "lw": 1.8, "ms": 6, "ls": "-.", "zorder": 5
        }),
        "r6": (get_pareto_frontier(load_run("results/yandex-200-cosine/deg_qg_summary_top100_run6.json")), {
            "color": "#52B788", "label": "Run 6: Unrolled SIMD + 4CL Prefetch", "marker": "s", "lw": 2.2, "ms": 6, "zorder": 7
        }),
        "r7": (get_pareto_frontier(load_run("results/yandex-200-cosine/deg_qg_summary_top100_run7.json") + load_run("results/yandex-200-cosine/deg_qg_summary_top100_run6.json")), {
            "color": "#081C15", "label": "Run 7: Contiguous 256B Aligned + Adaptiv Rerank (Final)", "marker": "D", "lw": 3.2, "ms": 8, "zorder": 9
        }),
    }

    fig, ax = plt.subplots(figsize=(11.5, 8), dpi=300)

    for run_key, (pareto, style) in runs.items():
        px = [p["recall"] for p in pareto if p["recall"] >= 0.88]
        py = [p["qps"] for p in pareto if p["recall"] >= 0.88]
        ax.plot(px, py, **style)

    ax.set_xlim(0.89, 1.002)
    ax.set_ylim(0, 14500)
    ax.set_xlabel("Recall@100", fontsize=13, fontweight="bold")
    ax.set_ylabel("QPS (Queries / Sekunde)", fontsize=13, fontweight="bold")
    ax.set_title("Vollständige AutoResearch Evolution: DEG-QG (Runs 0–7) übertrifft Glass auf yandex-200-cosine",
                 fontsize=14, fontweight="bold", pad=15)
    ax.grid(True, which="both", ls=":", alpha=0.6)
    ax.legend(loc="upper right", fontsize=10, framealpha=0.95)

    # Key Annotations
    ax.annotate("Run 7 (1.0x, ef=100)\n10.454 QPS @ 92.55% (+32.4% vs Glass)", (0.9255, 10453.5), textcoords="offset points", xytext=(-60, 25),
                arrowprops=dict(arrowstyle="->", color="#081C15", lw=1.3), fontsize=9, color="#081C15", fontweight="bold")
    ax.annotate("Run 7 (1.0x, ef=150)\n7.757 QPS @ 95.25% (+24.9% vs Glass)", (0.9525, 7757.4), textcoords="offset points", xytext=(-100, 25),
                arrowprops=dict(arrowstyle="->", color="#081C15", lw=1.3), fontsize=9, color="#081C15", fontweight="bold")
    ax.annotate("Glass (ef=20)\n7.897 QPS @ 94.88%", (0.9488, 7897.4), textcoords="offset points", xytext=(20, 20),
                arrowprops=dict(arrowstyle="->", color="#D90429", lw=1.3), fontsize=9, color="#D90429", fontweight="bold")
    ax.annotate("Run 6 (1.2x, ef=350)\n3.452 QPS @ 99.09% (+4.0% vs Glass)", (0.9909, 3451.7), textcoords="offset points", xytext=(-130, 25),
                arrowprops=dict(arrowstyle="->", color="#081C15", lw=1.3), fontsize=9, color="#081C15", fontweight="bold")
    ax.annotate("Glass (ef=400)\n3.320 QPS @ 99.06%", (0.9906, 3319.7), textcoords="offset points", xytext=(-90, -35),
                arrowprops=dict(arrowstyle="->", color="#D90429", lw=1.3), fontsize=9, color="#D90429", fontweight="bold")
    ax.annotate("Run 6 (1.1x, ef=600)\n2.266 QPS @ 99.80% (+28.4% vs Glass)", (0.9980, 2265.5), textcoords="offset points", xytext=(-140, -35),
                arrowprops=dict(arrowstyle="->", color="#081C15", lw=1.3), fontsize=9, color="#081C15", fontweight="bold")

    output_path = "results/yandex-200-cosine/deg_vs_glass_yandex_top100.png"
    plt.savefig(output_path, bbox_inches="tight")
    print(f"Plot successfully saved at {output_path}")


if __name__ == "__main__":
    main()
