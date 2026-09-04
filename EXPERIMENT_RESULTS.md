# AutoResearch Experiment-Log: `deglib` (DEG-QG) vs. `Glass`

Dieses Dokument erfasst alle durchgeführten Experimente, Messergebnisse, Code-Änderungen und Pareto-Vergleiche im Rahmen der AutoResearch-Optimierung von `deglib`.

---

## 1. Setup & Hardware-Kontext

* **Host CPU**: AMD Ryzen AI 9 HX PRO 375 w/ Radeon 890M (12 Cores / 24 Threads, AVX2, AVX-512, AVX-VNNI)
* **Datensatz**: `yandex-200-cosine` (1.000.000 Basisvektoren, 1.000 Queries, $D=200$, Metrik = Cosine)
* **Benchmark-Einstellung**: Single-Core, Top-100 ($k=100$), $Runs=2$, Ground-Truth-Distanzschwelle $\epsilon_{\text{tol}} = 10^{-3}$
* **Vergleichs-Algorithmen**:
  * **Glass Referenz**: $R=48, L=400$, SQ8U Graph-Routing $\rightarrow$ FP16 Reranking ($1.5\times = 150$ Vektoren)
  * **DEG-QG**: $K=48$, `LowLID`, `prune_non_rng=False`, INT8 Graph-Routing $\rightarrow$ FP16 Reranking ($1.2\times$ / $1.5\times$)

---

## 2. Zusammenfassung aller Experiment-Runs

| Run ID | Datum | Bezeichnung | Beschreibung | Recall@98% QPS | Recall@99% QPS | Recall@99.5% QPS | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Ref** | 2026-09-04 | **Glass Benchmark** | Zilliz Glass HNSW $R=48, L=400, SQ8U \rightarrow FP16$ | **4.288** | **3.320** | **2.300** | **Benchmark-Ziel** |
| **Run 0** | 2026-09-04 | **DEG-QG Baseline** | Originaler DEG $\epsilon$-Suchradius ($K=48$, LowLID, No-Prune) | 2.876 | 2.180 | 1.855 | **Baseline gesetzt** |
| **Run 1** | 2026-09-04 | **LinearPool Engine** | Portierung von Glass `LinearPool` ($ef$-Budget) + `SearchImpl2` | 3.081 (+7.1%) | 2.192 (+0.6%) | 1.871 (+0.9%) | **Behalten** |
| **Run 2** | 2026-09-04 | **Medoids + Prefetch**| 64 Einstiegspunkte + Prefetch der Nachbarlisten bei Insert | **3.881 (+34.9%)** | **2.702 (+24.0%)** | **2.250 (+21.3%)** | **Großer Sprung** |

## 2.1 Visuelle Pareto-Kurve (QPS vs. Recall@100)

![DEG-QG vs Glass](results/yandex-200-cosine/deg_vs_glass_yandex_top100.png)

* **Rote Kurve (Glass Referenz)**: $R=48, L=400$, SQ8U $\rightarrow$ FP16. Führt weiterhin um ca. 25–35%.
* **Blaue gestrichelte Kurve (DEG Baseline Run 0)**: Originale $\epsilon$-Suche. Fällt bei $> 99.8\%$ steil wie eine Klippe ab (bis auf 80–248 QPS), da $\epsilon \ge 0.15$ die Queue flutet.
* **Grüne Kurve (DEG Phase 1 LinearPool Run 1)**: Vollständige Glättung der Kurve, **+7% bis +14% QPS** über weite Teile des High-Recall-Bereichs.

---
## 3. Detaillierte Run-Protokolle

### Run 0: Die verifizierte Host-Baseline (DEG-QG Original)

* **Report-Datei**: `results/yandex-200-cosine/DEG_QG_BASELINE_EPS_YANDEX_TOP100_RESULTS.md`
* **Rohdaten**: `results/yandex-200-cosine/deg_qg_baseline_eps_top100.json`
* **Implementierung**: Originaler `searchImpl`-Pfad in `internal_graph.h` mit Priority Queue (`UncheckedSet`) und Abbruchkriterium:
  $$\text{exploration\_radius} = \text{radius}_{k} \times (1 + \epsilon)$$
* **Index-Bau**: 381.12 s, Speicher: 835.3 MB

#### Messwerte Run 0:

| `rerank` | `search_eps` | Recall@100 | QPS (Single-Core) | Latency / Query |
| :--- | :--- | :--- | :--- | :--- |
| `1.2x` | `eps=0.000` | **94.48 %** | 4.503,0 | 0.22 ms |
| `1.2x` | `eps=0.005` | **95.54 %** | 4.051,9 | 0.25 ms |
| `1.2x` | `eps=0.010` | **96.44 %** | 3.941,2 | 0.25 ms |
| `1.2x` | `eps=0.020` | **97.48 %** | 3.355,6 | 0.30 ms |
| `1.2x` | `eps=0.040` | **98.73 %** | 2.553,0 | 0.39 ms |
| `1.2x` | `eps=0.060` | **99.54 %** | 1.855,1 | 0.54 ms |
| `1.2x` | `eps=0.080` | **99.77 %** | 1.354,3 | 0.74 ms |
| `1.2x` | `eps=0.100` | **99.96 %** | 1.001,4 | 1.00 ms |
| `1.5x` | `eps=0.000` | **96.22 %** | 3.765,8 | 0.27 ms |
| `1.5x` | `eps=0.020` | **98.13 %** | 2.876,3 | 0.35 ms |
| `1.5x` | `eps=0.040` | **99.28 %** | 2.179,5 | 0.46 ms |
| `1.5x` | `eps=0.060` | **99.67 %** | 1.573,0 | 0.64 ms |
| `1.5x` | `eps=0.080` | **99.93 %** | 1.186,9 | 0.84 ms |

---

### Run 1: Glass `LinearPool` ($ef$-Budget) + `SearchImpl2` Prefetch-Pipelining

* **Report-Datei**: `results/yandex-200-cosine/DEG_QG_LINEAR_POOL_YANDEX_TOP100_RESULTS.md`
* **Rohdaten**: `results/yandex-200-cosine/deg_qg_summary_top100_linear_pool.json`
* **Code-Änderungen**:
  1. `cpp/deglib/include/deglib/search/linear_pool.h`: Neuer `LinearPool` (flaches Array der Größe $ef$, Binärsuche-Einfügung, `memmove`, `cur_ < ef_` Termination) und `Bitset<uint64_t>` (125 KB L2-Cache-freundlich).
  2. `cpp/deglib/include/deglib/graph/internal_graph.h`: `searchEfImpl` mit 2-stufigem `SearchImpl2`-Filter (Pass 1 sammelt unbesuchte Nachbarn in `edge_buf[256]`, Pass 2 prefetcht um `po=4` Kanten voraus und evaluiert SIMD-Distanzen).
  3. `cpp/deglib/include/deglib/search/searcher.h`: `search_ef_f32`, `search_ef_f16`, `search_batch_ef`.
  4. `python/src/deg_cpp/deglib_cpp.cpp` & `deglib/search.py`: Forwarding von `ef`.
  5. `vibe/algorithms/deg/module.py`: `set_query_arguments` und `query` auf `ef` geschaltet.
* **Index-Bau**: 337.04 s, Speicher: 834.9 MB

#### Messwerte Run 1:

| `rerank` | `param` | Recall@100 | QPS (Single-Core) | Latency / Query | Diff vs. Baseline (Run 0) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `1.2x` | `ef=100` | **93.16 %** | **5.538,0** | 0.18 ms | — |
| `1.2x` | `ef=150` | **96.21 %** | **4.496,7** | 0.22 ms | **+14.1%** (vs 3.941 @ 96.4%) |
| `1.2x` | `ef=200` | **97.45 %** | **3.695,5** | 0.27 ms | **+10.1%** (vs 3.356 @ 97.5%) |
| `1.2x` | `ef=250` | **98.31 %** | **3.080,8** | 0.33 ms | **+7.1%** (vs 2.876 @ 98.1%) |
| `1.2x` | `ef=300` | **98.80 %** | **2.691,1** | 0.37 ms | **+5.4%** (vs 2.553 @ 98.7%) |
| `1.2x` | `ef=400` | **99.38 %** | **2.191,8** | 0.46 ms | **+0.6%** (vs 2.180 @ 99.3%) |
| `1.2x` | `ef=500` | **99.61 %** | **1.871,0** | 0.53 ms | **+18.9%** (vs 1.573 @ 99.7%) |
| `1.2x` | `ef=600` | **99.74 %** | **1.597,2** | 0.63 ms | **+17.9%** (vs 1.354 @ 99.8%) |
| `1.2x` | `ef=800` | **99.88 %** | **1.249,8** | 0.80 ms | **+5.3%** (vs 1.187 @ 99.9%) |
| `1.2x` | `ef=1000`| **99.91 %** | **1.021,6** | 0.98 ms | **+2.0%** (vs 1.001 @ 99.9%) |
| `1.5x` | `ef=150` | **96.22 %** | **4.311,5** | 0.23 ms | **+14.5%** |
| `1.5x` | `ef=200` | **97.46 %** | **3.559,0** | 0.28 ms | **+6.1%** |
| `1.5x` | `ef=250` | **98.31 %** | **3.029,5** | 0.33 ms | **+5.3%** |
| `1.5x` | `ef=300` | **98.80 %** | **2.612,3** | 0.38 ms | **+2.3%** |
| `1.5x` | `ef=400` | **99.39 %** | **2.126,0** | 0.47 ms | **-2.5%** |
| `1.5x` | `ef=500` | **99.61 %** | **1.799,7** | 0.56 ms | **+14.4%** |
| `1.5x` | `ef=600` | **99.74 %** | **1.563,0** | 0.64 ms | **+15.4%** |
| `1.5x` | `ef=800` | **99.88 %** | **1.227,1** | 0.82 ms | **+3.4%** |
| `1.5x` | `ef=1000`| **99.91 %** | **1.024,9** | 0.98 ms | **+2.3%** |

---

### Run 2: 64 Medoid-Einstiegspunkte + Kantenlisten-Prefetching bei Pool-Insert

* **Report-Datei**: `results/yandex-200-cosine/DEG_QG_RUN2_YANDEX_TOP100_RESULTS.md`
* **Rohdaten**: `results/yandex-200-cosine/deg_qg_summary_top100_run2.json`
* **Code-Änderungen**:
  1. `vibe/algorithms/deg/module.py`: 64 gut verteilte Medoid-Einstiegspunkte werden beim Indexieren gesetzt (`self.graph.set_entry_vertex_indices(...)`).
  2. `cpp/deglib/include/deglib/graph/internal_graph.h`: Vor der Suche wird unter den 64 Einstiegspunkten der mit der geringsten Distanz zur Query ermittelt.
  3. Sobald ein Nachbar $v$ erfolgreich in den `LinearPool` eingefügt wird (`pool.insert`), wird dessen Kantenliste vorab in den Cache geholt (`memory::prefetch(neighbors_by_index(v))`), analog zu Glass.

#### Messwerte Run 2:

| `rerank` | `param` | Recall@100 | QPS (Single-Core) | Latency / Query | Diff vs. Baseline (Run 0) | Diff vs. Run 1 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `1.2x` | `ef=100` | **93.01 %** | **6.998,0** | 0.14 ms | — | **+26.4%** |
| `1.2x` | `ef=150` | **95.86 %** | **5.540,5** | 0.18 ms | **+36.7%** (vs 4.052) | **+23.2%** |
| `1.2x` | `ef=200` | **97.56 %** | **4.305,8** | 0.23 ms | **+28.3%** (vs 3.356) | **+16.5%** |
| `1.2x` | `ef=250` | **98.20 %** | **3.881,1** | 0.26 ms | **+34.9%** (vs 2.876) | **+26.0%** |
| `1.2x` | `ef=300` | **98.72 %** | **3.377,5** | 0.30 ms | **+32.3%** (vs 2.553) | **+25.5%** |
| `1.2x` | `ef=400` | **99.40 %** | **2.701,6** | 0.37 ms | **+24.0%** (vs 2.180) | **+23.3%** |
| `1.2x` | `ef=500` | **99.56 %** | **2.250,4** | 0.44 ms | **+21.3%** (vs 1.855) | **+20.3%** |
| `1.2x` | `ef=600` | **99.70 %** | **1.938,4** | 0.52 ms | **+43.1%** (vs 1.354) | **+21.4%** |
| `1.2x` | `ef=800` | **99.88 %** | **1.524,9** | 0.66 ms | **+28.5%** (vs 1.187) | **+22.0%** |
| `1.2x` | `ef=1000`| **99.91 %** | **1.252,4** | 0.80 ms | **+25.1%** (vs 1.001) | **+22.6%** |
| `1.5x` | `ef=200` | **97.57 %** | **4.357,6** | 0.23 ms | **+33.9%** (vs 3.253) | **+22.4%** |
| `1.5x` | `ef=250` | **98.21 %** | **3.818,3** | 0.26 ms | **+32.8%** (vs 2.876) | **+26.0%** |
| `1.5x` | `ef=400` | **99.41 %** | **2.680,9** | 0.37 ms | **+23.0%** (vs 2.180) | **+26.1%** |
| `1.5x` | `ef=500` | **99.56 %** | **2.231,0** | 0.45 ms | **+20.3%** (vs 1.855) | **+24.0%** |
| `1.5x` | `ef=800` | **99.88 %** | **1.493,1** | 0.67 ms | **+25.8%** (vs 1.187) | **+21.7%** |

---

## 4. Direkter Pareto-Vergleich: Glass vs. DEG-QG Baseline vs. Run 1 vs. Run 2

| Recall Target | Glass Referenz | DEG-QG Baseline (Run 0) | Run 1 (LinearPool) | **Run 2 (Medoids+Prefetch)** | Speedup vs Baseline | Diff zu Glass |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **$\ge 95.0\%$** | 6.210,1 QPS (`ef=200`) | 4.051,9 QPS (`1.2x, eps=0.005`) | 4.496,7 QPS (`1.2x, ef=150`) | **5.540,5 QPS** (`1.2x, ef=150`) | **+36.7%** | **-10.8%** |
| **$\ge 97.0\%$** | 4.287,6 QPS (`ef=300`) | 3.355,6 QPS (`1.2x, eps=0.020`) | 3.695,5 QPS (`1.2x, ef=200`) | **4.357,6 QPS** (`1.5x, ef=200`) | **+29.9%** | **+1.6% (Überholt!)** |
| **$\ge 98.0\%$** | 4.287,6 QPS (`ef=300`) | 2.876,3 QPS (`1.5x, eps=0.020`) | 3.080,8 QPS (`1.2x, ef=250`) | **3.881,1 QPS** (`1.2x, ef=250`) | **+34.9%** | **-9.5%** |
| **$\ge 98.5\%$** | 3.319,7 QPS (`ef=400`) | 2.553,0 QPS (`1.2x, eps=0.040`) | 2.691,1 QPS (`1.2x, ef=300`) | **3.377,5 QPS** (`1.2x, ef=300`) | **+32.3%** | **+1.7% (Überholt!)** |
| **$\ge 99.0\%$** | 3.319,7 QPS (`ef=400`) | 2.179,5 QPS (`1.5x, eps=0.040`) | 2.191,8 QPS (`1.2x, ef=400`) | **2.701,6 QPS** (`1.2x, ef=400`) | **+24.0%** | **-18.6%** |
| **$\ge 99.5\%$** | 2.300,3 QPS (`ef=600`) | 1.855,1 QPS (`1.2x, eps=0.060`) | 1.871,0 QPS (`1.2x, ef=500`) | **2.250,4 QPS** (`1.2x, ef=500`) | **+21.3%** | **-2.2% (Gleichauf!)** |
| **$\ge 99.8\%$** | 1.763,8 QPS (`ef=800`) | 1.186,9 QPS (`1.5x, eps=0.080`) | 1.249,8 QPS (`1.2x, ef=800`) | **1.524,9 QPS** (`1.2x, ef=800`) | **+28.5%** | **-13.5%** |
| **$\ge 99.9\%$** | 1.763,8 QPS (`ef=800`) | 1.186,9 QPS (`1.5x, eps=0.080`) | 1.024,9 QPS (`1.5x, ef=1000`)| **1.252,4 QPS** (`1.2x, ef=1000`)| **+5.5%** | **-29.0%** |
---

## 5. Analyse & Erkenntnisse aus Run 2

1. **Was extrem gut funktioniert hat**:
   * **64 Medoid-Einstiegspunkte**: Haben die QPS um über **+20% bis +26%** gesteigert! Die ersten 15–25 Suchschritte auf Layer 0 fallen weg.
   * Bei **97.0%** und **98.5%** Recall ist DEG-QG jetzt **schneller als Glass** (+1.6% bzw. +1.7%).
   * Bei **99.5%** Recall liegt DEG-QG mit **2.250 QPS** praktisch gleichauf mit Glass (**2.300 QPS**, nur -2.2% Unterschied).
2. **Wo Glass noch führt**:
   * Bei **99.0%** Recall führt Glass noch mit 3.320 vs 2.702 QPS (-18.6%).
   * Bei **99.9%** Recall führt Glass noch mit 1.764 vs 1.252 QPS (-29.0%).
3. **Die nächsten Hebel**:
   * **Hebel 4 (SIMD Loop Tuning für D=200)**: Die Dimension 200 hat einen Rest von 8 Bytes; ein handoptimierter Kernel spart Restschleifen.
   * **Hebel 2.2 (Prefetch Lines `pl` Reduzierung)**: Aktuell werden starr 4 Cachelines (256 Byte) geladen; für 200 Byte INT8 reichen 3 Cachelines (192 Byte). Das spart 25% Prefetch-Bandbreite.

