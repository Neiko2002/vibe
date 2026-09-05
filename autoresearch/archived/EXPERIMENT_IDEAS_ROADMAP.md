# AutoResearch: Neue Experiment-Reihe & Optimierungs-Ideen

## 1. Ausgangslage & schonungslose Analyse

Unser Run 6 hat bewiesen:
1. **Ab Recall $\ge 97.0\%$**: DEG-QG schlägt Glass an fast allen Stufen (+4% bis +28% Vorsprung).
2. **Unterhalb von Recall $97.0\%$ (Bereich 94.0% bis 97.0%)**:
   * Glass erreicht bei **94.88% Recall** hervorragende **7.897 QPS** (Latenz: 0.126 ms).
   * DEG-QG erreicht bei **96.22% Recall** aktuell **6.399 QPS** (Latenz: 0.156 ms) und bei **94.74% Recall** **6.342 QPS** (Latenz: 0.158 ms).
   * **In diesem Bereich liegt Glass ca. 20% bis 24% vor DEG-QG!**

Um Glass **über das gesamte Spektrum von 90% bis 100% lückenlos zu dominieren**, müssen wir die verbleibenden 30 Mikrosekunden pro Query eliminieren.

---

## 2. Die 6 neuen Forschungs-Hypothesen

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        DIE 6 NEUEN EXPERIMENT-HYPOTHESEN                               │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ Exp A: 2-Layer Skip-Graph (HNSW-Style Greedy Walk statt 128-Medoid Scan)              │
│ Exp B: Contiguous Feature Storage (Beseitigung des 416-Byte Interleaved Layouts)       │
│ Exp C: Graph-Bauqualität mit extend_k=128 / extend_k=256 (Aufholen von L=400)         │
│ Exp D: 256-Bit AVX2-VNNI vs. 512-Bit AVX-512 VNNI (Taktverhalten auf AMD Zen 5)      │
│ Exp E: Adaptives Reranking (Skip oder 1.05x Reranking bei niedrigen ef-Werten)         │
│ Exp F: Früher Abbruch / Worst-Distance Branching in der inneren Distanzschleife        │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

### Experiment A: 2-Layer Skip-Graph (Greedy Walk statt linearem Medoid-Scan)

* **Hintergrund**:
  * In Run 4–6 scannen wir 128 Medoide linear. Das kostet 128 Distanzberechnungen ($128 \times 200$ Byte $= 25.6\text{ KB}$), bevor die Suche überhaupt startet!
  * Glass nutzt stattdessen die oberen HNSW-Level (Level $> 0$). Dort führt es einen **gierigen Abstieg ($ef=1$)** durch. Da jeder obere Level nur wenige Knoten hat, braucht Glass **nur 10 bis 15 Distanzberechnungen**, um direkt am Ziel-Cluster auf Layer 0 zu landen!
* **Idee**:
  * Wir bauen einen extrem schlanken **Level-1 Skip-Graphen** über $M=512$ oder $1.024$ Landmark-Knoten mit $K=8$.
  * Vor Layer 0: Ein gieriger Abstieg ($ef=1$, Pfadlänge $\le 8$ Hops) findet den Ziel-Cluster in nur 8–15 Distanzberechnungen.
* **Erwarteter Gewinn**: Ersparnis von ~100 Distanzberechnungen pro Query $\rightarrow$ **+15% bis +20% QPS** bei niedrigen $ef$-Werten (0.12 ms statt 0.15 ms)!

---

### Experiment B: Contiguous Feature Matrix (Beseitigung des 416-Byte Layouts)

* **Hintergrund**:
  * In `ReadOnlyGraph` speichert DEG jeden Knoten als 416 Bytes Block:
    `[200 Bytes Feature] [192 Bytes Kanten] [4 Bytes Label] [20 Bytes Padding]`
  * Wenn der Suchloop über die Nachbarn iteriert, lädt er die 200 Bytes Features von Knoten, die hunderte Bytes voneinander entfernt im RAM liegen. Dazwischen liegen jeweils 216 Bytes Kantenlisten und Metadaten, die im Distanzloop gar nicht gebraucht werden, aber die Cache-Lines füllen!
  * Glass trennt beides strikt: Alle Vektoren liegen in einer zusammenhängenden $N \times 200$ Byte Matrix, alle Kanten in einer separaten $N \times 192$ Byte Matrix.
* **Idee**:
  * Trennung von Feature-Speicher und Graph-Topologie in `ReadOnlyGraph`:
    1. Reines Vektor-Array `const int8_t* feature_matrix` ($1.000.000 \times 200$ Bytes).
    2. Reines Kanten-Array `const uint32_t* edge_matrix` ($1.000.000 \times 48 \times 4$ Bytes).
* **Erwarteter Gewinn**: 50% weniger Cache-Pollution während der Distanzauswertung, saubereres Hardware-Streaming der CPU.

---

### Experiment C: Graph-Bauqualität mit $efConstruction \ge 128$

* **Hintergrund**:
  * Glass baut den HNSW-Graphen mit $L=400$ ($efConstruction=400$). Jeder Knoten wählt seine Nachbarn aus einem Suchfenster von 400 Knoten.
  * DEG wurde mit Default `extend_k=64` gebaut. Ein Graph mit $extend\_k=128$ oder $256$ hat nachweislich signifikant kürzere Pfade und höhere Konnektivität, wodurch bei kleinerem $ef$ sofort höherer Recall erreicht wird.
* **Idee**:
  * Bau eines DEG-Graphen mit `extend_k=128, improve_k=48`.
* **Erwarteter Gewinn**: +1.5% bis +3.0% Recall bei identischem $ef$, wodurch die gesamte Kurve nach links oben wandert.

---

### Experiment D: 256-Bit AVX2-VNNI vs. 512-Bit AVX-512 VNNI

* **Hintergrund**:
  * Auf AMD Zen 5 (Ryzen AI 9) taktet die CPU bei intensiver 512-Bit ZMM-Nutzung unter bestimmten Bedingungen konservativer als bei 256-Bit YMM-Instruktionen.
  * Zudem sind 200 Dimensionen $= 6 \times 32 + 8$ Bytes. Mit 256-Bit Vektoren sind es genau 6 volle YMM-Register plus 8 Bytes Rest.
* **Idee**:
  * Implementierung eines unrolled AVX2-VNNI Kernels mit 6x `_mm256_dpbusd_epi32` im Vergleich zum 3x `_mm512_dpbusd_epi32` Kernel.
* **Erwarteter Gewinn**: Höherer CPU-Takt, eventuell schnellere Ausführungszyklen.

---

### Experiment E: Adaptiver Reranking-Faktor

* **Hintergrund**:
  * Das Reranking von 120 Vektoren in FP16 (`ExactRefiner`) kostet ca. $30\,\mu\text{s}$ pro Query.
  * Bei $ef \le 150$ macht das Reranking fast 25% der gesamten Query-Zeit aus!
  * Bei $ef=150$ ohne Reranking (`1.0x`) erreicht DEG bereits **95.25% Recall** bei **6.937 QPS** (Latenz 0.144 ms)!
* **Idee**:
  * Dynamisches `rerank_factor` je nach Ziel-Recall:
    * Bei $ef \le 120$: Reranking komplett überspringen (`1.0x`) $\rightarrow$ bis zu **8.800 QPS** bei Recall 93–95%!
    * Bei $ef \ge 200$: $1.15\times$ oder $1.2\times$ für $99\%+$ Recall.
* **Erwarteter Gewinn**: Massive Beschleunigung im Bereich 93%–96% Recall, wo Glass aktuell führt.

---

## 3. Priorisierte Ausführungs-Reihenfolge

1. **Sprint 1 (Exp E: Adaptiver Rerank)**: Sofort umsetzbar in Python/C++; testet, ob wir bei $Recall \approx 95\%$ mit $1.0\times$ Reranking Glass (7.897 QPS) direkt mit über 8.500 QPS schlagen.
2. **Sprint 2 (Exp A: 2-Layer Skip Graph)**: Bau eines schnellen Medoid-Hierarchie-Einstiegs, um die 128 sequenziellen Distanzberechnungen vor dem Graphstart auf 10–15 Hops zu reduzieren.
3. **Sprint 3 (Exp B: Contiguous Feature Storage)**: Entflechten des 416-Byte Node-Layouts in getrennte Vektor- und Kantenmatrizen.
4. **Sprint 4 (Exp C: Graph-Bau mit extend_k=128)**: Neuer Index-Bau mit höherer Kantenqualität.
