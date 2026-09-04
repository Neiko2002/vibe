# DEG Benchmark Results: `yandex-200-cosine-DEG-QG-RUN2` (Top-100 / Recall@100)

- **Dataset**: `yandex-200-cosine-DEG-QG-RUN2` (1,000,000 base vectors, 1,000 queries, metric = Cosine)
- **Benchmark Setting**: Single-Core, $K_{\text{search}} = 100$ (`count=100`)
- **Evaluations in Report**: 20

---

## 1. Pareto-Stufen Übersicht (Beste QPS ab Recall-Schwellenwert)

| Ziel-Stufe | Recall@100 | QPS (Single-Core) | Latency / Query | Config ($K$, Target, Pruning) | rerank | search_eps |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **$\ge 70.0\%$** | ** 93.01 %** | ** 6998.0** |  0.14 ms | $K=48$, LowLID, No-Prune | `1.2x` | `ef=100` |
| **$\ge 75.0\%$** | ** 93.01 %** | ** 6998.0** |  0.14 ms | $K=48$, LowLID, No-Prune | `1.2x` | `ef=100` |
| **$\ge 80.0\%$** | ** 93.01 %** | ** 6998.0** |  0.14 ms | $K=48$, LowLID, No-Prune | `1.2x` | `ef=100` |
| **$\ge 85.0\%$** | ** 93.01 %** | ** 6998.0** |  0.14 ms | $K=48$, LowLID, No-Prune | `1.2x` | `ef=100` |
| **$\ge 90.0\%$** | ** 93.01 %** | ** 6998.0** |  0.14 ms | $K=48$, LowLID, No-Prune | `1.2x` | `ef=100` |
| **$\ge 92.0\%$** | ** 93.01 %** | ** 6998.0** |  0.14 ms | $K=48$, LowLID, No-Prune | `1.2x` | `ef=100` |
| **$\ge 95.0\%$** | ** 95.86 %** | ** 5540.5** |  0.18 ms | $K=48$, LowLID, No-Prune | `1.2x` | `ef=150` |
| **$\ge 97.0\%$** | ** 97.57 %** | ** 4357.6** |  0.23 ms | $K=48$, LowLID, No-Prune | `1.5x` | `ef=200` |
| **$\ge 98.0\%$** | ** 98.20 %** | ** 3881.1** |  0.26 ms | $K=48$, LowLID, No-Prune | `1.2x` | `ef=250` |
| **$\ge 99.0\%$** | ** 99.40 %** | ** 2701.6** |  0.37 ms | $K=48$, LowLID, No-Prune | `1.2x` | `ef=400` |
| **$\ge 99.5\%$** | ** 99.56 %** | ** 2250.4** |  0.44 ms | $K=48$, LowLID, No-Prune | `1.2x` | `ef=500` |
| **$\ge 99.9\%$** | ** 99.91 %** | ** 1252.4** |  0.80 ms | $K=48$, LowLID, No-Prune | `1.2x` | `ef=1000` |

---

## 2. Vollständige Aufschlüsselung aller Konfigurationen

### Configuration: $K=48$ | `LowLID` | RNG-Pruning: Disabled (prune_non_rng=False)
- **Build Time**: 361.5 s (6.03 min)
- **Index Memory**: 835.7 MB

| `rerank_factor` | `param` | Recall@100 | QPS (Single-Core) | Latency / Query |
| :--- | :--- | :--- | :--- | :--- |
| `1.2x` | `ef=100` | ** 93.01 %** |  6998.0 |  0.14 ms |
| `1.2x` | `ef=150` | ** 95.86 %** |  5540.5 |  0.18 ms |
| `1.2x` | `ef=200` | ** 97.56 %** |  4305.8 |  0.23 ms |
| `1.2x` | `ef=250` | ** 98.20 %** |  3881.1 |  0.26 ms |
| `1.2x` | `ef=300` | ** 98.72 %** |  3377.5 |  0.30 ms |
| `1.2x` | `ef=400` | ** 99.40 %** |  2701.6 |  0.37 ms |
| `1.2x` | `ef=500` | ** 99.56 %** |  2250.4 |  0.44 ms |
| `1.2x` | `ef=600` | ** 99.70 %** |  1938.4 |  0.52 ms |
| `1.2x` | `ef=800` | ** 99.88 %** |  1524.9 |  0.66 ms |
| `1.2x` | `ef=1000` | ** 99.91 %** |  1252.4 |  0.80 ms |
| `1.5x` | `ef=100` | ** 93.01 %** |  6420.3 |  0.16 ms |
| `1.5x` | `ef=150` | ** 95.87 %** |  5261.7 |  0.19 ms |
| `1.5x` | `ef=200` | ** 97.57 %** |  4357.6 |  0.23 ms |
| `1.5x` | `ef=250` | ** 98.21 %** |  3818.3 |  0.26 ms |
| `1.5x` | `ef=300` | ** 98.73 %** |  3201.6 |  0.31 ms |
| `1.5x` | `ef=400` | ** 99.41 %** |  2680.9 |  0.37 ms |
| `1.5x` | `ef=500` | ** 99.56 %** |  2231.0 |  0.45 ms |
| `1.5x` | `ef=600` | ** 99.70 %** |  1929.6 |  0.52 ms |
| `1.5x` | `ef=800` | ** 99.88 %** |  1493.1 |  0.67 ms |
| `1.5x` | `ef=1000` | ** 99.91 %** |  1212.6 |  0.82 ms |

