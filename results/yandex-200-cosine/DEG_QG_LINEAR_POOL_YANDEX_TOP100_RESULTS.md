# DEG Benchmark Results: `yandex-200-cosine-DEG-QG-LINEAR-POOL` (Top-100 / Recall@100)

- **Dataset**: `yandex-200-cosine-DEG-QG-LINEAR-POOL` (1,000,000 base vectors, 1,000 queries, metric = Cosine)
- **Benchmark Setting**: Single-Core, $K_{\text{search}} = 100$ (`count=100`)
- **Evaluations in Report**: 20

---

## 1. Pareto-Stufen Übersicht (Beste QPS ab Recall-Schwellenwert)

| Ziel-Stufe | Recall@100 | QPS (Single-Core) | Latency / Query | Config ($K$, Target, Pruning) | rerank | search_eps |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **$\ge 70.0\%$** | ** 93.16 %** | ** 5538.0** |  0.18 ms | $K=48$, LowLID, No-Prune | `1.2x` | `ef=100` |
| **$\ge 75.0\%$** | ** 93.16 %** | ** 5538.0** |  0.18 ms | $K=48$, LowLID, No-Prune | `1.2x` | `ef=100` |
| **$\ge 80.0\%$** | ** 93.16 %** | ** 5538.0** |  0.18 ms | $K=48$, LowLID, No-Prune | `1.2x` | `ef=100` |
| **$\ge 85.0\%$** | ** 93.16 %** | ** 5538.0** |  0.18 ms | $K=48$, LowLID, No-Prune | `1.2x` | `ef=100` |
| **$\ge 90.0\%$** | ** 93.16 %** | ** 5538.0** |  0.18 ms | $K=48$, LowLID, No-Prune | `1.2x` | `ef=100` |
| **$\ge 92.0\%$** | ** 93.16 %** | ** 5538.0** |  0.18 ms | $K=48$, LowLID, No-Prune | `1.2x` | `ef=100` |
| **$\ge 95.0\%$** | ** 96.21 %** | ** 4496.7** |  0.22 ms | $K=48$, LowLID, No-Prune | `1.2x` | `ef=150` |
| **$\ge 97.0\%$** | ** 97.45 %** | ** 3695.5** |  0.27 ms | $K=48$, LowLID, No-Prune | `1.2x` | `ef=200` |
| **$\ge 98.0\%$** | ** 98.31 %** | ** 3080.8** |  0.32 ms | $K=48$, LowLID, No-Prune | `1.2x` | `ef=250` |
| **$\ge 99.0\%$** | ** 99.38 %** | ** 2191.8** |  0.46 ms | $K=48$, LowLID, No-Prune | `1.2x` | `ef=400` |
| **$\ge 99.5\%$** | ** 99.61 %** | ** 1871.0** |  0.53 ms | $K=48$, LowLID, No-Prune | `1.2x` | `ef=500` |
| **$\ge 99.9\%$** | ** 99.91 %** | ** 1024.9** |  0.98 ms | $K=48$, LowLID, No-Prune | `1.5x` | `ef=1000` |

---

## 2. Vollständige Aufschlüsselung aller Konfigurationen

### Configuration: $K=48$ | `LowLID` | RNG-Pruning: Disabled (prune_non_rng=False)
- **Build Time**: 337.0 s (5.62 min)
- **Index Memory**: 834.8 MB

| `rerank_factor` | `param` | Recall@100 | QPS (Single-Core) | Latency / Query |
| :--- | :--- | :--- | :--- | :--- |
| `1.2x` | `ef=100` | ** 93.16 %** |  5538.0 |  0.18 ms |
| `1.2x` | `ef=150` | ** 96.21 %** |  4496.7 |  0.22 ms |
| `1.2x` | `ef=200` | ** 97.45 %** |  3695.5 |  0.27 ms |
| `1.2x` | `ef=250` | ** 98.31 %** |  3080.8 |  0.32 ms |
| `1.2x` | `ef=300` | ** 98.80 %** |  2691.1 |  0.37 ms |
| `1.2x` | `ef=400` | ** 99.38 %** |  2191.8 |  0.46 ms |
| `1.2x` | `ef=500` | ** 99.61 %** |  1871.0 |  0.53 ms |
| `1.2x` | `ef=600` | ** 99.74 %** |  1597.2 |  0.63 ms |
| `1.2x` | `ef=800` | ** 99.88 %** |  1249.8 |  0.80 ms |
| `1.2x` | `ef=1000` | ** 99.91 %** |  1021.6 |  0.98 ms |
| `1.5x` | `ef=100` | ** 93.16 %** |  5273.5 |  0.19 ms |
| `1.5x` | `ef=150` | ** 96.22 %** |  4311.5 |  0.23 ms |
| `1.5x` | `ef=200` | ** 97.46 %** |  3559.0 |  0.28 ms |
| `1.5x` | `ef=250` | ** 98.31 %** |  3029.5 |  0.33 ms |
| `1.5x` | `ef=300` | ** 98.80 %** |  2612.3 |  0.38 ms |
| `1.5x` | `ef=400` | ** 99.39 %** |  2126.0 |  0.47 ms |
| `1.5x` | `ef=500` | ** 99.61 %** |  1799.7 |  0.56 ms |
| `1.5x` | `ef=600` | ** 99.74 %** |  1563.0 |  0.64 ms |
| `1.5x` | `ef=800` | ** 99.88 %** |  1227.1 |  0.81 ms |
| `1.5x` | `ef=1000` | ** 99.91 %** |  1024.9 |  0.98 ms |

