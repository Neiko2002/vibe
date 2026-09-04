# DEG Benchmark Results: `yandex-200-cosine-DEG-QG-RUN5` (Top-100 / Recall@100)

- **Dataset**: `yandex-200-cosine-DEG-QG-RUN5` (1,000,000 base vectors, 1,000 queries, metric = Cosine)
- **Benchmark Setting**: Single-Core, $K_{\text{search}} = 100$ (`count=100`)
- **Evaluations in Report**: 20

---

## 1. Pareto-Stufen Übersicht (Beste QPS ab Recall-Schwellenwert)

| Ziel-Stufe | Recall@100 | QPS (Single-Core) | Latency / Query | Config ($K$, Target, Pruning) | rerank | search_eps |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **$\ge 70.0\%$** | ** 93.42 %** | ** 7820.4** |  0.13 ms | $K=48$, LowLID, No-Prune | `1.2x` | `ef=100` |
| **$\ge 75.0\%$** | ** 93.42 %** | ** 7820.4** |  0.13 ms | $K=48$, LowLID, No-Prune | `1.2x` | `ef=100` |
| **$\ge 80.0\%$** | ** 93.42 %** | ** 7820.4** |  0.13 ms | $K=48$, LowLID, No-Prune | `1.2x` | `ef=100` |
| **$\ge 85.0\%$** | ** 93.42 %** | ** 7820.4** |  0.13 ms | $K=48$, LowLID, No-Prune | `1.2x` | `ef=100` |
| **$\ge 90.0\%$** | ** 93.42 %** | ** 7820.4** |  0.13 ms | $K=48$, LowLID, No-Prune | `1.2x` | `ef=100` |
| **$\ge 92.0\%$** | ** 93.42 %** | ** 7820.4** |  0.13 ms | $K=48$, LowLID, No-Prune | `1.2x` | `ef=100` |
| **$\ge 95.0\%$** | ** 96.23 %** | ** 6349.6** |  0.16 ms | $K=48$, LowLID, No-Prune | `1.2x` | `ef=150` |
| **$\ge 97.0\%$** | ** 97.70 %** | ** 5083.7** |  0.20 ms | $K=48$, LowLID, No-Prune | `1.2x` | `ef=200` |
| **$\ge 98.0\%$** | ** 98.42 %** | ** 4422.6** |  0.23 ms | $K=48$, LowLID, No-Prune | `1.2x` | `ef=250` |
| **$\ge 99.0\%$** | ** 99.31 %** | ** 3029.5** |  0.33 ms | $K=48$, LowLID, No-Prune | `1.2x` | `ef=400` |
| **$\ge 99.5\%$** | ** 99.57 %** | ** 2606.8** |  0.38 ms | $K=48$, LowLID, No-Prune | `1.2x` | `ef=500` |
| **$\ge 99.9\%$** | ** 99.91 %** | ** 1433.9** |  0.70 ms | $K=48$, LowLID, No-Prune | `1.2x` | `ef=1000` |

---

## 2. Vollständige Aufschlüsselung aller Konfigurationen

### Configuration: $K=48$ | `LowLID` | RNG-Pruning: Disabled (prune_non_rng=False)
- **Build Time**: 2.7 s (0.05 min)
- **Index Memory**: 857.6 MB

| `rerank_factor` | `param` | Recall@100 | QPS (Single-Core) | Latency / Query |
| :--- | :--- | :--- | :--- | :--- |
| `1.2x` | `ef=100` | ** 93.42 %** |  7820.4 |  0.13 ms |
| `1.2x` | `ef=150` | ** 96.23 %** |  6349.6 |  0.16 ms |
| `1.2x` | `ef=200` | ** 97.70 %** |  5083.7 |  0.20 ms |
| `1.2x` | `ef=250` | ** 98.42 %** |  4422.6 |  0.23 ms |
| `1.2x` | `ef=300` | ** 98.72 %** |  3834.9 |  0.26 ms |
| `1.2x` | `ef=400` | ** 99.31 %** |  3029.5 |  0.33 ms |
| `1.2x` | `ef=500` | ** 99.57 %** |  2606.8 |  0.38 ms |
| `1.2x` | `ef=600` | ** 99.80 %** |  2229.0 |  0.45 ms |
| `1.2x` | `ef=800` | ** 99.89 %** |  1742.6 |  0.57 ms |
| `1.2x` | `ef=1000` | ** 99.91 %** |  1433.9 |  0.70 ms |
| `1.5x` | `ef=100` | ** 93.42 %** |  7140.9 |  0.14 ms |
| `1.5x` | `ef=150` | ** 96.23 %** |  5834.5 |  0.17 ms |
| `1.5x` | `ef=200` | ** 97.70 %** |  4985.2 |  0.20 ms |
| `1.5x` | `ef=250` | ** 98.42 %** |  4152.2 |  0.24 ms |
| `1.5x` | `ef=300` | ** 98.73 %** |  3721.5 |  0.27 ms |
| `1.5x` | `ef=400` | ** 99.32 %** |  3013.7 |  0.33 ms |
| `1.5x` | `ef=500` | ** 99.57 %** |  2519.2 |  0.40 ms |
| `1.5x` | `ef=600` | ** 99.81 %** |  2180.1 |  0.46 ms |
| `1.5x` | `ef=800` | ** 99.89 %** |  1715.4 |  0.58 ms |
| `1.5x` | `ef=1000` | ** 99.91 %** |  1407.4 |  0.71 ms |

