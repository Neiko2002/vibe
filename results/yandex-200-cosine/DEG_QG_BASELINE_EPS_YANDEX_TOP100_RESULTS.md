# DEG Benchmark Results: `yandex-200-cosine-DEG-QG-BASELINE-EPS` (Top-100 / Recall@100)

- **Dataset**: `yandex-200-cosine-DEG-QG-BASELINE-EPS` (1,000,000 base vectors, 1,000 queries, metric = Cosine)
- **Benchmark Setting**: Single-Core, $K_{\text{search}} = 100$ (`count=100`)
- **Evaluations in Report**: 26

---

## 1. Pareto-Stufen Übersicht (Beste QPS ab Recall-Schwellenwert)

| Ziel-Stufe | Recall@100 | QPS (Single-Core) | Latency / Query | Config ($K$, Target, Pruning) | rerank | search_eps |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **$\ge 70.0\%$** | ** 94.48 %** | ** 4503.0** |  0.22 ms | $K=48$, LowLID, No-Prune | `1.2x` | `eps=0.0` |
| **$\ge 75.0\%$** | ** 94.48 %** | ** 4503.0** |  0.22 ms | $K=48$, LowLID, No-Prune | `1.2x` | `eps=0.0` |
| **$\ge 80.0\%$** | ** 94.48 %** | ** 4503.0** |  0.22 ms | $K=48$, LowLID, No-Prune | `1.2x` | `eps=0.0` |
| **$\ge 85.0\%$** | ** 94.48 %** | ** 4503.0** |  0.22 ms | $K=48$, LowLID, No-Prune | `1.2x` | `eps=0.0` |
| **$\ge 90.0\%$** | ** 94.48 %** | ** 4503.0** |  0.22 ms | $K=48$, LowLID, No-Prune | `1.2x` | `eps=0.0` |
| **$\ge 92.0\%$** | ** 94.48 %** | ** 4503.0** |  0.22 ms | $K=48$, LowLID, No-Prune | `1.2x` | `eps=0.0` |
| **$\ge 95.0\%$** | ** 95.54 %** | ** 4051.9** |  0.25 ms | $K=48$, LowLID, No-Prune | `1.2x` | `eps=0.005` |
| **$\ge 97.0\%$** | ** 97.48 %** | ** 3355.6** |  0.30 ms | $K=48$, LowLID, No-Prune | `1.2x` | `eps=0.02` |
| **$\ge 98.0\%$** | ** 98.13 %** | ** 2876.3** |  0.35 ms | $K=48$, LowLID, No-Prune | `1.5x` | `eps=0.02` |
| **$\ge 99.0\%$** | ** 99.28 %** | ** 2179.5** |  0.46 ms | $K=48$, LowLID, No-Prune | `1.5x` | `eps=0.04` |
| **$\ge 99.5\%$** | ** 99.54 %** | ** 1855.1** |  0.54 ms | $K=48$, LowLID, No-Prune | `1.2x` | `eps=0.06` |
| **$\ge 99.9\%$** | ** 99.93 %** | ** 1186.9** |  0.84 ms | $K=48$, LowLID, No-Prune | `1.5x` | `eps=0.08` |
| **$\ge 100.0\%$** | **100.00 %** | **  248.3** |  4.03 ms | $K=48$, LowLID, No-Prune | `1.2x` | `eps=0.2` |

---

## 2. Vollständige Aufschlüsselung aller Konfigurationen

### Configuration: $K=48$ | `LowLID` | RNG-Pruning: Disabled (prune_non_rng=False)
- **Build Time**: 381.1 s (6.35 min)
- **Index Memory**: 835.3 MB

| `rerank_factor` | `param` | Recall@100 | QPS (Single-Core) | Latency / Query |
| :--- | :--- | :--- | :--- | :--- |
| `1.2x` | `eps=0.000` | ** 94.48 %** |  4503.0 |  0.22 ms |
| `1.2x` | `eps=0.005` | ** 95.54 %** |  4051.9 |  0.25 ms |
| `1.2x` | `eps=0.010` | ** 96.44 %** |  3941.2 |  0.25 ms |
| `1.2x` | `eps=0.020` | ** 97.48 %** |  3355.6 |  0.30 ms |
| `1.2x` | `eps=0.040` | ** 98.73 %** |  2553.0 |  0.39 ms |
| `1.2x` | `eps=0.060` | ** 99.54 %** |  1855.1 |  0.54 ms |
| `1.2x` | `eps=0.080` | ** 99.77 %** |  1354.3 |  0.74 ms |
| `1.2x` | `eps=0.100` | ** 99.96 %** |  1001.4 |  1.00 ms |
| `1.2x` | `eps=0.120` | ** 99.99 %** |   739.5 |  1.35 ms |
| `1.2x` | `eps=0.150` | **100.00 %** |   481.0 |  2.08 ms |
| `1.2x` | `eps=0.200` | **100.00 %** |   248.3 |  4.03 ms |
| `1.2x` | `eps=0.250` | **100.00 %** |   136.4 |  7.33 ms |
| `1.2x` | `eps=0.300` | **100.00 %** |    80.0 | 12.49 ms |
| `1.5x` | `eps=0.000` | ** 96.22 %** |  3765.8 |  0.27 ms |
| `1.5x` | `eps=0.005` | ** 96.85 %** |  3532.0 |  0.28 ms |
| `1.5x` | `eps=0.010` | ** 97.30 %** |  3253.2 |  0.31 ms |
| `1.5x` | `eps=0.020` | ** 98.13 %** |  2876.3 |  0.35 ms |
| `1.5x` | `eps=0.040` | ** 99.28 %** |  2179.5 |  0.46 ms |
| `1.5x` | `eps=0.060` | ** 99.67 %** |  1573.0 |  0.64 ms |
| `1.5x` | `eps=0.080` | ** 99.93 %** |  1186.9 |  0.84 ms |
| `1.5x` | `eps=0.100` | ** 99.97 %** |   873.6 |  1.14 ms |
| `1.5x` | `eps=0.120` | ** 99.99 %** |   664.8 |  1.50 ms |
| `1.5x` | `eps=0.150` | **100.00 %** |   436.8 |  2.29 ms |
| `1.5x` | `eps=0.200` | **100.00 %** |   228.7 |  4.37 ms |
| `1.5x` | `eps=0.250` | **100.00 %** |   127.0 |  7.87 ms |
| `1.5x` | `eps=0.300` | **100.00 %** |    75.6 | 13.23 ms |

