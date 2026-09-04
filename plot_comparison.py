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

    # 4. Load DEG Run 2 (Medoids + Edge Prefetch)
    with open("results/yandex-200-cosine/deg_qg_summary_top100_run2.json") as f:
        deg_r2_all = json.load(f)
    deg_r2 = [
        {"recall": d["recall_100"], "qps": d["qps"], "param": f"ef={d['ef']}"}
        for d in deg_r2_all
    ]

    # 5. Load DEG Run 3 (Auto Prefetch po=14, pl=4)
    with open("results/yandex-200-cosine/deg_qg_summary_top100_run3.json") as f:
        deg_r3_all = json.load(f)
    deg_r3 = [
        {"recall": d["recall_100"], "qps": d["qps"], "param": f"ef={d['ef']}"}
        for d in deg_r3_all
    ]

    glass_pareto = get_pareto_frontier(glass_r48)
    base_pareto = get_pareto_frontier(deg_base)
    lp_pareto = get_pareto_frontier(deg_lp)
    r2_pareto = get_pareto_frontier(deg_r2)
    r3_pareto = get_pareto_frontier(deg_r3)

    # Plot
    fig, ax = plt.subplots(figsize=(11, 7.5), dpi=300)

    # Styling
    styles = {
        "glass": {"color": "#E63946", "label": "Glass (HNSW R=48, SQ8U->FP16)", "marker": "o", "lw": 2.5, "ms": 7},
        "base": {"color": "#ADB5BD", "label": "DEG-QG Baseline (eps-Radius, K=48)", "marker": "s", "lw": 1.5, "ms": 4, "ls": ":"},
        "lp": {"color": "#6C757D", "label": "DEG-QG Run 1 (LinearPool ef, K=48)", "marker": "^", "lw": 1.6, "ms": 5, "ls": "--"},
        "r2": {"color": "#457B9D", "label": "DEG-QG Run 2 (64 Medoids + Edge Prefetch)", "marker": "v", "lw": 2.0, "ms": 6, "ls": "-."},
        "r3": {"color": "#2A9D8F", "label": "DEG-QG Run 3 (Auto Prefetch po=14, pl=4)", "marker": "D", "lw": 2.8, "ms": 7},
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

    # DEG Run 2 curve
    r2x = [p["recall"] for p in r2_pareto if p["recall"] >= 0.94]
    r2y = [p["qps"] for p in r2_pareto if p["recall"] >= 0.94]
    ax.plot(r2x, r2y, **styles["r2"])

    # DEG Run 3 curve
    r3x = [p["recall"] for p in r3_pareto if p["recall"] >= 0.94]
    r3y = [p["qps"] for p in r3_pareto if p["recall"] >= 0.94]
    ax.plot(r3x, r3y, **styles["r3"])

    ax.set_xlim(0.945, 1.002)
    ax.set_ylim(0, 8500)
    ax.set_xlabel("Recall@100", fontsize=13, fontweight="bold")
    ax.set_ylabel("QPS (Queries / Sekunde)", fontsize=13, fontweight="bold")
    ax.set_title("yandex-200-cosine Top-100 — QPS vs. Recall@100 (Linear Scale)",
                 fontsize=14, fontweight="bold", pad=15)
    ax.grid(True, which="both", ls=":", alpha=0.6)
    ax.legend(loc="upper right", fontsize=10, framealpha=0.95)

    # Annotations
    ax.annotate("Glass (ef=600)\n2.300 QPS @ 99.6%", (0.9962, 2300.3), textcoords="offset points", xytext=(-95, 20),
                arrowprops=dict(arrowstyle="->", color="#E63946", lw=1.3), fontsize=9, color="#E63946", fontweight="bold")
    ax.annotate("Run 3 (ef=500)\n2.328 QPS @ 99.56% (Überholt!)", (0.9956, 2327.9), textcoords="offset points", xytext=(-120, -35),
                arrowprops=dict(arrowstyle="->", color="#2A9D8F", lw=1.3), fontsize=9, color="#2A9D8F", fontweight="bold")
    ax.annotate("Run 3 (ef=200)\n4.626 QPS @ 97.6% (+7.9% vs Glass)", (0.9756, 4626.2), textcoords="offset points", xytext=(-30, 25),
                arrowprops=dict(arrowstyle="->", color="#2A9D8F", lw=1.3), fontsize=9, color="#2A9D8F", fontweight="bold")

    output_path = "results/yandex-200-cosine/deg_vs_glass_yandex_top100.png"
    plt.savefig(output_path, bbox_inches="tight")
    print(f"Plot successfully saved at {output_path}")


if __name__ == "__main__":
    main()
