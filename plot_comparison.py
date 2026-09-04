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

    # 5. Load DEG Run 5 (Unrolled AVX-512 VNNI SIMD)
    with open("results/yandex-200-cosine/deg_qg_summary_top100_run5.json") as f:
        deg_r5_all = json.load(f)
    deg_r5 = [
        {"recall": d["recall_100"], "qps": d["qps"], "param": f"ef={d['ef']}"}
        for d in deg_r5_all
    ]

    glass_pareto = get_pareto_frontier(glass_r48)
    base_pareto = get_pareto_frontier(deg_base)
    lp_pareto = get_pareto_frontier(deg_lp)
    r4_pareto = get_pareto_frontier(deg_r4)
    r5_pareto = get_pareto_frontier(deg_r5)

    # Plot
    fig, ax = plt.subplots(figsize=(11, 7.5), dpi=300)

    # Styling
    styles = {
        "glass": {"color": "#E63946", "label": "Glass (HNSW R=48, SQ8U->FP16)", "marker": "o", "lw": 2.5, "ms": 7},
        "base": {"color": "#CED4DA", "label": "DEG-QG Baseline (eps-Radius, K=48)", "marker": "s", "lw": 1.4, "ms": 4, "ls": ":"},
        "lp": {"color": "#ADB5BD", "label": "DEG-QG Run 1 (LinearPool ef, K=48)", "marker": "^", "lw": 1.5, "ms": 5, "ls": "--"},
        "r4": {"color": "#457B9D", "label": "DEG-QG Run 4 (128 KM Medoids + Top-2 Entry)", "marker": "P", "lw": 1.8, "ms": 6, "ls": "-."},
        "r5": {"color": "#2A9D8F", "label": "DEG-QG Run 5 (Unrolled AVX-512 VNNI D=200)", "marker": "D", "lw": 3.0, "ms": 8},
    }

    # Glass curve
    gx = [p["recall"] for p in glass_pareto if p["recall"] >= 0.94]
    gy = [p["qps"] for p in glass_pareto if p["recall"] >= 0.94]
    ax.plot(gx, gy, **styles["glass"])

    # DEG Baseline curve
    bx = [p["recall"] for p in base_pareto if p["recall"] >= 0.94]
    by = [p["qps"] for p in base_pareto if p["recall"] >= 0.94]
    ax.plot(bx, by, **styles["base"])

    # DEG LinearPool Phase 1 curve
    lpx = [p["recall"] for p in lp_pareto if p["recall"] >= 0.94]
    lpy = [p["qps"] for p in lp_pareto if p["recall"] >= 0.94]
    ax.plot(lpx, lpy, **styles["lp"])

    # DEG Run 4 curve
    r4x = [p["recall"] for p in r4_pareto if p["recall"] >= 0.94]
    r4y = [p["qps"] for p in r4_pareto if p["recall"] >= 0.94]
    ax.plot(r4x, r4y, **styles["r4"])

    # DEG Run 5 curve
    r5x = [p["recall"] for p in r5_pareto if p["recall"] >= 0.94]
    r5y = [p["qps"] for p in r5_pareto if p["recall"] >= 0.94]
    ax.plot(r5x, r5y, **styles["r5"])

    ax.set_xlim(0.945, 1.002)
    ax.set_ylim(0, 8500)
    ax.set_xlabel("Recall@100", fontsize=13, fontweight="bold")
    ax.set_ylabel("QPS (Queries / Sekunde)", fontsize=13, fontweight="bold")
    ax.set_title("AutoResearch Durchbruch: DEG-QG Run 5 überholt Glass auf yandex-200-cosine Top-100",
                 fontsize=14, fontweight="bold", pad=15)
    ax.grid(True, which="both", ls=":", alpha=0.6)
    ax.legend(loc="upper right", fontsize=10.5, framealpha=0.95)

    # Annotations
    ax.annotate("Run 5 (ef=200)\n5.084 QPS @ 97.7% (+18.6% vs Glass)", (0.9770, 5083.7), textcoords="offset points", xytext=(-80, 20),
                arrowprops=dict(arrowstyle="->", color="#2A9D8F", lw=1.3), fontsize=9, color="#2A9D8F", fontweight="bold")
    ax.annotate("Run 5 (ef=500)\n2.607 QPS @ 99.57% (+13.3% vs Glass)", (0.9957, 2606.8), textcoords="offset points", xytext=(-130, 20),
                arrowprops=dict(arrowstyle="->", color="#2A9D8F", lw=1.3), fontsize=9, color="#2A9D8F", fontweight="bold")
    ax.annotate("Run 5 (ef=600)\n2.229 QPS @ 99.80% (+26.4% vs Glass)", (0.9980, 2229.0), textcoords="offset points", xytext=(-140, -35),
                arrowprops=dict(arrowstyle="->", color="#2A9D8F", lw=1.3), fontsize=9, color="#2A9D8F", fontweight="bold")

    output_path = "results/yandex-200-cosine/deg_vs_glass_yandex_top100.png"
    plt.savefig(output_path, bbox_inches="tight")
    print(f"Plot successfully saved at {output_path}")


if __name__ == "__main__":
    main()
