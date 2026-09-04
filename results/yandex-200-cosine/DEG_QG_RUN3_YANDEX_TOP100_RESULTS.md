# DEG Benchmark Results: `yandex-200-cosine-DEG-QG-RUN3` (Top-100 / Recall@100)

- **Dataset**: `yandex-200-cosine-DEG-QG-RUN3` (1,000,000 base vectors, 1,000 queries, metric = Cosine)
- **Benchmark Setting**: Single-Core, $K_{\text{search}} = 100$ (`count=100`)
- **Evaluations in Report**: 20

---

## 1. Pareto-Stufen Übersicht (Beste QPS ab Recall-Schwellenwert)

| Ziel-Stufe | Recall@100 | QPS (Single-Core) | Latency / Query | Config ($K$, Target, Pruning) | rerank | search_eps |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **$\ge 70.0\%$** | ** 93.01 %** | ** 6857.0** |  0.15 ms | $K=48$, LowLID, No-Prune | `1.2x` | `ef=100` |
| **$\ge 75.0\%$** | ** 93.01 %** | ** 6857.0** |  0.15 ms | $K=48$, LowLID, No-Prune | `1.2x` | `ef=100` |
| **$\ge 80.0\%$** | ** 93.01 %** | ** 6857.0** |  0.15 ms | $K=48$, LowLID, No-Prune | `1.2x` | `ef=100` |
| **$\ge 85.0\%$** | ** 93.01 %** | ** 6857.0** |  0.15 ms | $K=48$, LowLID, No-Prune | `1.2x` | `ef=100` |
| **$\ge 90.0\%$** | ** 93.01 %** | ** 6857.0** |  0.15 ms | $K=48$, LowLID, No-Prune | `1.2x` | `ef=100` |
| **$\ge 92.0\%$** | ** 93.01 %** | ** 6857.0** |  0.15 ms | $K=48$, LowLID, No-Prune | `1.2x` | `ef=100` |
| **$\ge 95.0\%$** | ** 95.86 %** | ** 5464.6** |  0.18 ms | $K=48$, LowLID, No-Prune | `1.2x` | `ef=150` |
| **$\ge 97.0\%$** | ** 97.56 %** | ** 4626.2** |  0.22 ms | $K=48$, LowLID, No-Prune | `1.2x` | `ef=200` |
| **$\ge 98.0\%$** | ** 98.21 %** | ** 3875.9** |  0.26 ms | $K=48$, LowLID, No-Prune | `1.5x` | `ef=250` |
| **$\ge 99.0\%$** | ** 99.40 %** | ** 2777.1** |  0.36 ms | $K=48$, LowLID, No-Prune | `1.2x` | `ef=400` |
| **$\ge 99.5\%$** | ** 99.56 %** | ** 2327.9** |  0.43 ms | $K=48$, LowLID, No-Prune | `1.2x` | `ef=500` |
| **$\ge 99.9\%$** | ** 99.91 %** | ** 1305.5** |  0.77 ms | $K=48$, LowLID, No-Prune | `1.2x` | `ef=1000` |

---

## 2. Vollständige Aufschlüsselung aller Konfigurationen

### Configuration: $K=48$ | `LowLID` | RNG-Pruning: Disabled (prune_non_rng=False)
- **Build Time**: 2.6 s (0.04 min)
- **Index Memory**: 830.9 MB

| `rerank_factor` | `param` | Recall@100 | QPS (Single-Core) | Latency / Query |
| :--- | :--- | :--- | :--- | :--- |
| `1.2x` | `ef=100` | ** 93.01 %** |  6857.0 |  0.15 ms |
| `1.2x` | `ef=150` | ** 95.86 %** |  5464.6 |  0.18 ms |
| `1.2x` | `ef=200` | ** 97.56 %** |  4626.2 |  0.22 ms |
| `1.2x` | `ef=250` | ** 98.20 %** |  3869.0 |  0.26 ms |
| `1.2x` | `ef=300` | ** 98.72 %** |  3466.9 |  0.29 ms |
| `1.2x` | `ef=400` | ** 99.40 %** |  2777.1 |  0.36 ms |
| `1.2x` | `ef=500` | ** 99.56 %** |  2327.9 |  0.43 ms |
| `1.2x` | `ef=600` | ** 99.70 %** |  2000.7 |  0.50 ms |
| `1.2x` | `ef=800` | ** 99.88 %** |  1579.1 |  0.63 ms |
| `1.2x` | `ef=1000` | ** 99.91 %** |  1305.5 |  0.77 ms |
| `1.5x` | `ef=100` | ** 93.01 %** |  6479.4 |  0.15 ms |
| `1.5x` | `ef=150` | ** 95.87 %** |  5388.0 |  0.19 ms |
| `1.5x` | `ef=200` | ** 97.57 %** |  4502.1 |  0.22 ms |
| `1.5x` | `ef=250` | ** 98.21 %** |  3875.9 |  0.26 ms |
| `1.5x` | `ef=300` | ** 98.73 %** |  3288.5 |  0.30 ms |
| `1.5x` | `ef=400` | ** 99.41 %** |  2694.7 |  0.37 ms |
| `1.5x` | `ef=500` | ** 99.56 %** |  2286.4 |  0.44 ms |
| `1.5x` | `ef=600` | ** 99.70 %** |  1975.4 |  0.51 ms |
| `1.5x` | `ef=800` | ** 99.88 %** |  1533.8 |  0.65 ms |
| `1.5x` | `ef=1000` | ** 99.91 %** |  1277.1 |  0.78 ms |

