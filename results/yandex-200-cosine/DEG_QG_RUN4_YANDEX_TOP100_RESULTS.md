# DEG Benchmark Results: `yandex-200-cosine-DEG-QG-RUN4` (Top-100 / Recall@100)

- **Dataset**: `yandex-200-cosine-DEG-QG-RUN4` (1,000,000 base vectors, 1,000 queries, metric = Cosine)
- **Benchmark Setting**: Single-Core, $K_{\text{search}} = 100$ (`count=100`)
- **Evaluations in Report**: 20

---

## 1. Pareto-Stufen Übersicht (Beste QPS ab Recall-Schwellenwert)

| Ziel-Stufe | Recall@100 | QPS (Single-Core) | Latency / Query | Config ($K$, Target, Pruning) | rerank | search_eps |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **$\ge 70.0\%$** | ** 93.42 %** | ** 6944.4** |  0.14 ms | $K=48$, LowLID, No-Prune | `1.2x` | `ef=100` |
| **$\ge 75.0\%$** | ** 93.42 %** | ** 6944.4** |  0.14 ms | $K=48$, LowLID, No-Prune | `1.2x` | `ef=100` |
| **$\ge 80.0\%$** | ** 93.42 %** | ** 6944.4** |  0.14 ms | $K=48$, LowLID, No-Prune | `1.2x` | `ef=100` |
| **$\ge 85.0\%$** | ** 93.42 %** | ** 6944.4** |  0.14 ms | $K=48$, LowLID, No-Prune | `1.2x` | `ef=100` |
| **$\ge 90.0\%$** | ** 93.42 %** | ** 6944.4** |  0.14 ms | $K=48$, LowLID, No-Prune | `1.2x` | `ef=100` |
| **$\ge 92.0\%$** | ** 93.42 %** | ** 6944.4** |  0.14 ms | $K=48$, LowLID, No-Prune | `1.2x` | `ef=100` |
| **$\ge 95.0\%$** | ** 96.23 %** | ** 5457.6** |  0.18 ms | $K=48$, LowLID, No-Prune | `1.2x` | `ef=150` |
| **$\ge 97.0\%$** | ** 97.70 %** | ** 4590.2** |  0.22 ms | $K=48$, LowLID, No-Prune | `1.2x` | `ef=200` |
| **$\ge 98.0\%$** | ** 98.42 %** | ** 3943.3** |  0.25 ms | $K=48$, LowLID, No-Prune | `1.2x` | `ef=250` |
| **$\ge 99.0\%$** | ** 99.31 %** | ** 2762.9** |  0.36 ms | $K=48$, LowLID, No-Prune | `1.2x` | `ef=400` |
| **$\ge 99.5\%$** | ** 99.57 %** | ** 2307.3** |  0.43 ms | $K=48$, LowLID, No-Prune | `1.2x` | `ef=500` |
| **$\ge 99.9\%$** | ** 99.91 %** | ** 1285.1** |  0.78 ms | $K=48$, LowLID, No-Prune | `1.2x` | `ef=1000` |

---

## 2. Vollständige Aufschlüsselung aller Konfigurationen

### Configuration: $K=48$ | `LowLID` | RNG-Pruning: Disabled (prune_non_rng=False)
- **Build Time**: 2.8 s (0.05 min)
- **Index Memory**: 858.3 MB

| `rerank_factor` | `param` | Recall@100 | QPS (Single-Core) | Latency / Query |
| :--- | :--- | :--- | :--- | :--- |
| `1.2x` | `ef=100` | ** 93.42 %** |  6944.4 |  0.14 ms |
| `1.2x` | `ef=150` | ** 96.23 %** |  5457.6 |  0.18 ms |
| `1.2x` | `ef=200` | ** 97.70 %** |  4590.2 |  0.22 ms |
| `1.2x` | `ef=250` | ** 98.42 %** |  3943.3 |  0.25 ms |
| `1.2x` | `ef=300` | ** 98.72 %** |  3347.7 |  0.30 ms |
| `1.2x` | `ef=400` | ** 99.31 %** |  2762.9 |  0.36 ms |
| `1.2x` | `ef=500` | ** 99.57 %** |  2307.3 |  0.43 ms |
| `1.2x` | `ef=600` | ** 99.80 %** |  1933.6 |  0.52 ms |
| `1.2x` | `ef=800` | ** 99.89 %** |  1563.0 |  0.64 ms |
| `1.2x` | `ef=1000` | ** 99.91 %** |  1285.1 |  0.78 ms |
| `1.5x` | `ef=100` | ** 93.42 %** |  6494.5 |  0.15 ms |
| `1.5x` | `ef=150` | ** 96.23 %** |  5397.4 |  0.19 ms |
| `1.5x` | `ef=200` | ** 97.70 %** |  4359.8 |  0.23 ms |
| `1.5x` | `ef=250` | ** 98.42 %** |  3826.0 |  0.26 ms |
| `1.5x` | `ef=300` | ** 98.73 %** |  3321.6 |  0.30 ms |
| `1.5x` | `ef=400` | ** 99.32 %** |  2658.4 |  0.38 ms |
| `1.5x` | `ef=500` | ** 99.57 %** |  2241.1 |  0.45 ms |
| `1.5x` | `ef=600` | ** 99.81 %** |  1947.3 |  0.51 ms |
| `1.5x` | `ef=800` | ** 99.89 %** |  1539.7 |  0.65 ms |
| `1.5x` | `ef=1000` | ** 99.91 %** |  1264.7 |  0.79 ms |

