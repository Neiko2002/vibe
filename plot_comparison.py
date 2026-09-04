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


def main():
    # 1. Load Glass
    with open("results/yandex-200-cosine/glass_summary_top100_LINUX.json") as f:
        glass_all = json.load(f)
    glass_r48 = [
        {"recall": g["recall_100"], "qps": g["qps"], "param": f"ef={g['ef']}"}
        for g in glass_all
        if g["R"] == 48 and g["quant"] == "SQ8U" and g["search_quant"] == "SQ8U" and g["refine_quant"] == "FP16"
    ]

    # 2. Load DEG Baseline (eps)
    with open("results/yandex-200-cosine/deg_qg_baseline_eps_top100.json") as f:
        deg_base_all = json.load(f)
    deg_base = [
        {"recall": d["recall_100"], "qps": d["qps"], "param": f"eps={d['eps']}"}
        for d in deg_base_all
    ]

    # 3. Load DEG Phase 1 (LinearPool ef)
    with open("results/yandex-200-cosine/deg_qg_summary_top100_linear_pool.json") as f:
        deg_lp_all = json.load(f)
    deg_lp = [
        {"recall": d["recall_100"], "qps": d["qps"], "param": f"ef={d['ef']}"}
        for d in deg_lp_all
    ]

    # 4. Load DEG Run 4 (128 K-Means Medoids + Top-2 Entry)
    with open("results/yandex-200-cosine/deg_qg_summary_top100_run4.json") as f:
        deg_r4_all = json.load(f)
    deg_r4 = [
        {"recall": d["recall_100"], "qps": d["qps"], "param": f"ef={d['ef']}"}
        for d in deg_r4_all
    ]

    # 5. Load DEG Run 6 (Final Breakthrough: Unrolled SIMD + Tail Vectorization + 4CL Prefetch)
    with open("results/yandex-200-cosine/deg_qg_summary_top100_run6.json") as f:
        deg_r6_all = json.load(f)
    deg_r6 = [
        {"recall": d["recall_100"], "qps": d["qps"], "param": f"ef={d['ef']}"}
        for d in deg_r6_all
    ]

    glass_pareto = get_pareto_frontier(glass_r48)
    base_pareto = get_pareto_frontier(deg_base)
    lp_pareto = get_pareto_frontier(deg_lp)
    r4_pareto = get_pareto_frontier(deg_r4)
    r6_pareto = get_pareto_frontier(deg_r6)

    # Plot
    fig, ax = plt.subplots(figsize=(11, 7.5), dpi=300)

    # Styling
    styles = {
        "glass": {"color": "#E63946", "label": "Glass (HNSW R=48, SQ8U->FP16)", "marker": "o", "lw": 2.6, "ms": 7},
        "base": {"color": "#CED4DA", "label": "DEG-QG Baseline (eps-Radius, K=48)", "marker": "s", "lw": 1.4, "ms": 4, "ls": ":"},
        "lp": {"color": "#ADB5BD", "label": "DEG-QG Run 1 (LinearPool ef, K=48)", "marker": "^", "lw": 1.5, "ms": 5, "ls": "--"},
        "r4": {"color": "#457B9D", "label": "DEG-QG Run 4 (128 KM Medoids + Top-2)", "marker": "P", "lw": 1.8, "ms": 6, "ls": "-."},
        "r6": {"color": "#2A9D8F", "label": "DEG-QG Run 6 (Vectorized Tail + 4CL Prefetch)", "marker": "D", "lw": 3.0, "ms": 8},
    }

    # Curves
    for key, pdata in [("glass", glass_pareto), ("base", base_pareto), ("lp", lp_pareto), ("r4", r4_pareto), ("r6", r6_pareto)]:
        px = [p["recall"] for p in pdata if p["recall"] >= 0.94]
        py = [p["qps"] for p in pdata if p["recall"] >= 0.94]
        ax.plot(px, py, **styles[key])

    ax.set_xlim(0.945, 1.002)
    ax.set_ylim(0, 8500)
    ax.set_xlabel("Recall@100", fontsize=13, fontweight="bold")
    ax.set_ylabel("QPS (Queries / Sekunde)", fontsize=13, fontweight="bold")
    ax.set_title("AutoResearch Ziel Erreicht: DEG-QG Run 6 übertrifft Glass auf yandex-200-cosine Top-100",
                 fontsize=14, fontweight="bold", pad=15)
    ax.grid(True, which="both", ls=":", alpha=0.6)
    ax.legend(loc="upper right", fontsize=10.5, framealpha=0.95)

    # Annotations
    ax.annotate("Run 6 (ef=350)\n3.452 QPS @ 99.09% (+4.0% vs Glass)", (0.9909, 3451.7), textcoords="offset points", xytext=(-110, 25),
                arrowprops=dict(arrowstyle="->", color="#2A9D8F", lw=1.3), fontsize=9, color="#2A9D8F", fontweight="bold")
    ax.annotate("Glass (ef=400)\n3.320 QPS @ 99.06%", (0.9906, 3319.7), textcoords="offset points", xytext=(-100, -35),
                arrowprops=dict(arrowstyle="->", color="#E63946", lw=1.3), fontsize=9, color="#E63946", fontweight="bold")
    ax.annotate("Run 6 (ef=200)\n5.127 QPS @ 97.68% (+19.6% vs Glass)", (0.9768, 5126.8), textcoords="offset points", xytext=(-80, 20),
                arrowprops=dict(arrowstyle="->", color="#2A9D8F", lw=1.3), fontsize=9, color="#2A9D8F", fontweight="bold")
    ax.annotate("Run 6 (ef=600)\n2.266 QPS @ 99.80% (+28.4% vs Glass)", (0.9980, 2265.5), textcoords="offset points", xytext=(-140, -35),
                arrowprops=dict(arrowstyle="->", color="#2A9D8F", lw=1.3), fontsize=9, color="#2A9D8F", fontweight="bold")

    output_path = "results/yandex-200-cosine/deg_vs_glass_yandex_top100.png"
    plt.savefig(output_path, bbox_inches="tight")
    print(f"Plot successfully saved at {output_path}")


if __name__ == "__main__":
    main()
