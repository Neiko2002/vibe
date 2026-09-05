# Detaillierte Analyse aller AutoResearch-Teiländerungen (Audit & Isolationsplan)

Dieses Dokument analysiert und zerlegt systematisch alle Änderungen, die während der AutoResearch-Experimente in die Repositories eingebracht wurden. Ziel ist es, jede einzelne Teiländerung präzise einem Commit zuzuordnen, den realen Nutzen kritisch zu hinterfragen und einen sauberen Isolations- und Messplan ausgehend vom originalen `main`-Branch zu definieren.

---

## 1. Problemstellung & Ausgangslage

In den letzten Commits wurden zahlreiche Optimierungen, Heuristiken, SIMD-Kernel und Konfigurationsänderungen iterativ implementiert. Das Diagramm `deg_vs_glass_yandex_top100.png` und die zugehörigen JSON-/MD-Dateien (`deg_qg_autoresearch_latest.json`, `EXPERIMENT_RESULTS.md`) suggerieren kontinuierliche Rekordsprünge (bis zu $4.508,9\text{ QPS}$ Pareto-Schnitt bzw. $1.713,4\text{ QPS}$ bei $99,9\%\text{ Recall}$).

**Die Realität:**
Viele dieser Änderungen haben in der Praxis **keinen messbaren Einfluss** auf die tatsächliche Suchleistung oder basieren auf Scheineffekten:
1. **Grid-Resolution-Artefakt:** Wenn neue Zwischenwerte für `ef` (z. B. $825, 835, 840, 845, 850$) oder `rerank_size_factor` (z. B. $1.35\times$) in `config.yml` aufgenommen werden, landet ein Datenpunkt zufällig knapp über der $99,90\%$-Schwelle (z. B. $99,901\%$) mit kleinerem $ef$-Budget als zuvor ($ef=900 \rightarrow 99,93\%$). Das sieht im Pareto-Schnitt wie ein Rekordgewinn aus, ist aber **reine Hyperparameter-Punktwahl und kein Code-/Algorithmen-Speedup**.
2. **Amdahl's Law auf Nicht-Engpässen:**
   - *SIMD Medoid Scan:* Es gibt nur 128 Medoide, die **einmalig** zu Beginn der Query geprüft werden. Das Sparen von wenigen Mikrosekunden bei 128 Distanzen ist bei Queries, die tausende Graphknoten evaluieren, im Grundrauschen der CPU-Messung unauffindbar ($<0,5\%$).
   - *4-Way FP16 Reranker:* Das Reranking betrifft nur $k \times 1.35 = 135$ Vektoren am Ende der Suche. Über $95\%$ der Query-Zeit entfallen auf die INT8-Graph-Traversierung.
3. **Memory-Bound Bottleneck vs. ALU-Tricks:**
   - Im Graphen dominieren unvorhersehbare RAM-/LLC-Latenzen (Cache Misses beim Zugriff auf Nachbarlisten und Vektoren im 1-GB-Index). CPU-interne Optimierungen wie duale VNNI-Akkumulatoren oder Bitset-Micro-Inlining werden von den Speicherwartezyklen (Memory Stalls) vollständig geschluckt.
4. **Gebündelte Commits:** Mehrere Features wurden gleichzeitig in einem einzigen Commit abgeladen (z. B. `d47d4b17` mit 8 gleichzeitigen Mechanismen), wodurch unklar ist, welche Komponente tatsächlich gewirkt hat.

---

## 2. Repo-Architektur & Commit-Zuordnung

Die Änderungen verteilen sich auf **zwei getrennte Repositories**:
1. **`vibe` (Python-Benchmark-Harness)**: `C:/Lang/python/vibe`
   - Branch: `autoresearch/session-20260904`
   - Basis-Commit auf `main`: `1d1eb3d` (bzw. `89dd5cf`)
   - Enthält: Algorithmen-Wrapper (`vibe/algorithms/deg/module.py`), Suchgitter (`config.yml`), Runner-Skripte (`run_benchmark_autoresearch.py`, `autoresearch.sh`), Ergebnisdateien (`.json`, `.md`) und Plotter (`plot_comparison.py`).
2. **`DynamicExplorationGraph` (C++ Engine / `deglib`)**: `C:/Lang/cpp/DynamicExplorationGraph`
   - Branch: `autoresearch/yandex-top100-vs-glass`
   - Basis-Commit auf `main`: `47f8c244` (Release v0.2.5)
   - Enthält: Core-C++-Header (`internal_graph.h`, `linear_pool.h`, `searcher.h`, `readonly_graph.h`) und Pybind11-Bindings (`deglib_cpp.cpp`, `search.py`).

---

## 3. Vollständige Liste aller Teiländerungen je Commit

Nachfolgend ist **jede einzelne Teiländerung** aufgeschlüsselt. Auch wenn ein Commit mehrere Änderungen gleichzeitig enthielt, ist hier jede Teilkomponente isoliert aufgeführt.

---

### Phase 1 & 2: Basismechanismen bis Run 7

#### Commit `d47d4b17` (deglib) / `5dfac3e` (vibe) — *Run 2: LinearPool, Medoids & Prefetching*

Dieser Commit war der größte "Mega-Commit" und enthielt **8 gleichzeitige Teiländerungen**:

* **Teiländerung 1.1: `LinearPool` Datenstruktur ($ef$-Budget-Suche)**
  * **Repo / Commit:** `DynamicExplorationGraph` @ `d47d4b17`, `vibe` @ `5dfac3e`
  * **Dateien:** `cpp/deglib/include/deglib/search/linear_pool.h`, `vibe/algorithms/deg/module.py`
  * **Was wurde geändert:** Ersatz der ursprünglichen explorationsradiusbasierten Priority Queue (`UncheckedSet` mit $\epsilon$-Abbruchkriterium $\text{radius}_k \times (1+\epsilon)$) durch ein festes flaches Array der Größe $ef$. Einfügung via binärer Suche (`std::lower_bound` bzw. `find_bsearch`) und `memmove`. Terminierung, wenn Zeiger $cur \ge ef$.
  * **Theoretischer Zweck:** Deterministisches Suchbudget ($ef$) analog zu HNSW/Glass, kein "Klippenabsturz" bei hohen Recall-Anforderungen.
  * **Reale Auswirkung:** **Sehr hoch (Fundamentaler Architekturwechsel).** Dies war die Hauptursache für den ersten großen Sprung von Run 0 zu Run 1/2.
  * **Isolations-Test:** Alleinige Einführung von `LinearPool` auf `main` ohne Multi-Medoide und ohne Prefetching.

* **Teiländerung 1.2: 64-Bit Word `Bitset` als Visited-List**
  * **Repo / Commit:** `DynamicExplorationGraph` @ `d47d4b17`
  * **Dateien:** `cpp/deglib/include/deglib/search/linear_pool.h`
  * **Was wurde geändert:** Kompaktes Bitset (`Bitset<uint64_t>`, $125\text{ KB}$ für 1 Million Vektoren), das vollständig in den L2-Cache passt, anstelle von `std::vector<bool>` oder Hashsets.
  * **Theoretischer Zweck:** Vermeidung von Cache-Misses beim Nachschlagen besuchter Knoten.
  * **Reale Auswirkung:** **Moderat positiv.** Reduziert Speicherbandbreite gegenüber Byte-Arrays.

* **Teiländerung 1.3: Multi-Medoid-Einstiegssuche (`find_entry_vertex`)**
  * **Repo / Commit:** `DynamicExplorationGraph` @ `d47d4b17`
  * **Dateien:** `cpp/deglib/include/deglib/graph/internal_graph.h`
  * **Was wurde geändert:** Anstatt immer bei Knoten 0 oder einem einzelnen Medoid zu starten, durchläuft `find_entry_vertex` ein Array von Einstiegspunkten (`entry_vertex_indices`) und wählt den distanzmäßig nächsten Medoid als Startpunkt für den Pool.
  * **Theoretischer Zweck:** Bessere Startposition im Graphen, weniger Hops zur Zielregion.
  * **Reale Auswirkung:** **Fraglich / Gering.** Bei DEG existieren weitreichende "Long-Range Edges". Ob die Suche bei Knoten 0 oder einem Medoid startet, spart oft nur 2–3 Hops.
  * **Isolations-Test:** `LinearPool` mit fixem Startknoten 0 vs. `LinearPool` mit Medoid-Array vergleichen.

* **Teiländerung 1.4: 2-Stufige Nachbarschleife in `searchEfImpl`**
  * **Repo / Commit:** `DynamicExplorationGraph` @ `d47d4b17`
  * **Dateien:** `cpp/deglib/include/deglib/graph/internal_graph.h`
  * **Was wurde geändert:** Aufteilung der Nachbarverarbeitung in zwei Pässe:
    - Pass 1: Filtert bereits besuchte Nachbarn heraus und sammelt unbesuchte IDs im lokalen Puffer `edge_buf[256]`.
    - Pass 2: Führt Distanzberechnungen und Pool-Einfügungen durch.
  * **Theoretischer Zweck:** Entkopplung von Kontrollfluss/Bitset-Prüfung und Distanzberechnung zur besseren Vektorisierung und Prefetching.
  * **Reale Auswirkung:** **Moderat.** Schafft die Voraussetzung für softwaregesteuertes Prefetching.

* **Teiländerung 1.5: Lookahead-Prefetching von Feature-Vektoren (`po=4`)**
  * **Repo / Commit:** `DynamicExplorationGraph` @ `d47d4b17`
  * **Dateien:** `cpp/deglib/include/deglib/graph/internal_graph.h`
  * **Was wurde geändert:** In Pass 2 der Nachbarschleife wird der Vektor des Knotens $i + po$ via `memory::prefetch(graph.getFeatureVector(v_future))` vorab geladen, bevor er $po$ Iterationen später berechnet wird.
  * **Theoretischer Zweck:** Überlappen von RAM-Latenzen mit SIMD-Berechnungen.
  * **Reale Auswirkung:** **Unklar / Hardware-abhängig.** Moderne CPUs (Zen 5) besitzen aggressive Hardware-Prefetcher; statisches `po=4` kann Cache-Lines verdrängen oder ignoriert werden.

* **Teiländerung 1.6: Prefetching der Nachbarliste bei Pool-Insert**
  * **Repo / Commit:** `DynamicExplorationGraph` @ `d47d4b17`
  * **Dateien:** `cpp/deglib/include/deglib/graph/internal_graph.h`
  * **Was wurde geändert:** Wenn ein Kandidat $v$ erfolgreich in den `LinearPool` eingefügt wird (`pool.insert(v, dist)`), wird sofort seine Kantenliste geladen: `memory::prefetch(graph.getNeighborIndices(v))`.
  * **Theoretischer Zweck:** Wenn dieser Kandidat später aus dem Pool als bester unbesuchter Knoten expandiert wird, sollen seine Kanten bereits im L1/L2-Cache liegen.
  * **Reale Auswirkung:** **Wahrscheinlich gering.** Zwischen dem Einfügen und der tatsächlichen Expansion vergehen oft viele Zyklen, oder andere Speicherzugriffe verdrängen die Kantenzeile wieder.

* **Teiländerung 1.7: C++ API-Erweiterung für `ef`-Suche**
  * **Repo / Commit:** `DynamicExplorationGraph` @ `d47d4b17`
  * **Dateien:** `cpp/deglib/include/deglib/search/searcher.h`, `python/src/deg_cpp/deglib_cpp.cpp`, `python/src/deglib/search.py`
  * **Was wurde geändert:** Bereitstellung von `search_ef_f32`, `search_ef_f16` und `search_batch_ef` im `Searcher` und Pybind11-Wrapper.
  * **Theoretischer Zweck:** Notwendige Schnittstellenerweiterung für Python.
  * **Reale Auswirkung:** Reine Schnittstelle (kein Performance-Effekt an sich).

* **Teiländerung 1.8: Suchgitter-Umstellung in VIBE auf `ef`**
  * **Repo / Commit:** `vibe` @ `5dfac3e`
  * **Dateien:** `vibe/algorithms/deg/config.yml`, `vibe/algorithms/deg/module.py`
  * **Was wurde geändert:** Konfiguration einer neuen Run-Gruppe `linear_pool` mit Parametern `ef: [100, 150, 200, 250, 300, 400, 500, 600, 800, 1000]`.
  * **Theoretischer Zweck:** Nutzung der neuen C++ `ef`-Schnittstelle im VIBE-Benchmark.

---

#### Commit `d1b1090a` (deglib) / `6680dc4` (vibe) — *Run 3: Dynamische Prefetch-Steuerung & Auto-Tuner*

* **Teiländerung 2.1: Dynamische Parameter `po` und `pl` in C++**
  * **Repo / Commit:** `DynamicExplorationGraph` @ `d1b1090a`
  * **Dateien:** `cpp/deglib/include/deglib/graph/internal_graph.h`, `searcher.h`, `deglib_cpp.cpp`
  * **Was wurde geändert:** Ersetzung harter Konstanten durch veränderbare Klassenvariablen `po_` (Prefetch-Offset, z. B. 4..16) und `pl_` (Prefetch-Cachelines, z. B. 2..4) mit Getter/Setter `set_prefetch(po, pl)`.
  * **Theoretischer Zweck:** CPU-spezifische Anpassung der Vorlade-Distanz.

* **Teiländerung 2.2: Prefetch Auto-Tuner in Python (`Searcher.optimize`)**
  * **Repo / Commit:** `DynamicExplorationGraph` @ `d1b1090a`, Aufruf in `vibe` @ `6680dc4`
  * **Dateien:** `python/src/deglib/search.py`, `vibe/algorithms/deg/module.py:207-214`
  * **Was wurde geändert:** Vor dem eigentlichen Benchmark führt `fit()` einen Micro-Benchmark über 100 Trainingsqueries durch, probiert Kombinationen von `try_pos=[4,6,8,10,12,14,16]` und `try_pls=[2,3,4]` durch und setzt die schnellste Kombination (`po=14, pl=4`).
  * **Reale Auswirkung:** **Nahezu null.** Die Latenzunterschiede zwischen den `po`/`pl`-Kombinationen lagen im Bereich von wenigen Prozentpunkten und schwankten durch thermisches Throttling und Hintergrundprozesse.

---

#### Commit `0fc602e9` (deglib) / `6680dc4` (vibe) — *Run 4: Top-2 Entrypoints & 128 K-Means Medoide*

* **Teiländerung 3.1: Python K-Means 128 Medoid-Generator**
  * **Repo / Commit:** `vibe` @ `6680dc4`
  * **Dateien:** `vibe/algorithms/deg/module.py:16-34`, `191-196`
  * **Was wurde geändert:** In `fit()` werden mittels K-Means (15 Iterationen auf 30.000 Samples) 128 Cluster-Zentren bestimmt und deren nächste Datenpunkte als Medoide im Graphen hinterlegt (`graph.set_entry_vertex_indices(...)`).
  * **Theoretischer Zweck:** Gleichmäßige Verteilung von Einstiegspunkten über den Vektorraum.
  * **Reale Auswirkung:** **Fraglich.** Kostet zusätzliche Build-Zeit (~2-3s). DEG hat ohnehin eine zufällige oder hierarchische Vernetzung.

* **Teiländerung 3.2: Top-2 Einstiegspunkte in `LinearPool` einfügen**
  * **Repo / Commit:** `DynamicExplorationGraph` @ `0fc602e9`
  * **Dateien:** `cpp/deglib/include/deglib/graph/internal_graph.h:464-486`
  * **Was wurde geändert:** Beim Durchsuchen der 128 Medoide werden die **zwei** nächsten Medoide (`ep1`, `ep2`) ermittelt und beide in den `LinearPool` eingefügt (zuvor nur `ep1`).
  * **Theoretischer Zweck:** Erhöhung der Diversität beim Start der Graph-Suche, um lokale Minima zu vermeiden.
  * **Reale Auswirkung:** **Sehr gering bis negativ.** Fügt zusätzliche Distanzberechnungen und Pool-Inserts hinzu; der zweite Medoid wird oft sofort wieder verworfen.

---

#### Commit `df273b65` (deglib) / `090adc1` (vibe) — *Run 5: Unrolled AVX-512 VNNI D=200 Fastpath*

* **Teiländerung 4.1: Query-Register Caching (`q0`, `q1`, `q2`, `q_tail`)**
  * **Repo / Commit:** `DynamicExplorationGraph` @ `df273b65`
  * **Dateien:** `cpp/deglib/include/deglib/graph/internal_graph.h:510-530`
  * **Was wurde geändert:** Für $D=200$ (INT8) wird der Query-Vektor vor der Suchschleife einmalig in 3 ZMM-Register (`q0`, `q1`, `q2` je 64 Bytes) und ein 64-Bit-Register (`q_tail`) geladen.
  * **Theoretischer Zweck:** Kein wiederholtes Laden des Query-Vektors aus dem L1-Cache bei jeder Kantenberechnung.
  * **Reale Auswirkung:** **Positiv.** Spart Lade-Befehle und Register-Moves in der innersten Schleife.

* **Teiländerung 4.2: Inlined AVX-512 VNNI Dot-Product (`_mm512_dpbusd_epi32`)**
  * **Repo / Commit:** `DynamicExplorationGraph` @ `df273b65`
  * **Dateien:** `cpp/deglib/include/deglib/graph/internal_graph.h:545-580`
  * **Was wurde geändert:** Für $D=200$ wird der generische `COMPARATOR`-Aufruf (Funktionszeiger / Virtual Dispatch) durch 3 ungerollte `_mm512_dpbusd_epi32`-Befehle plus skalare 8-Byte-Restschleife direkt in `searchEfImpl` ersetzt.
  * **Theoretischer Zweck:** Beseitigung jeglichen Funktionsaufruf-Overheads und maximale Befehlsauslastung.
  * **Reale Auswirkung:** **Sehr hoch.** War einer der Hauptgründe für die Durchsatzsteigerung in Run 5.

---

#### Commit `9809e310` (deglib) / `cb1483c` (vibe) — *Run 6: Vektorisierter Tail & 4 Cachelines Prefetch*

* **Teiländerung 5.1: Vektorisierte 8-Byte-Restberechnung für D=200**
  * **Repo / Commit:** `DynamicExplorationGraph` @ `9809e310`
  * **Dateien:** `cpp/deglib/include/deglib/graph/internal_graph.h:514, 566-574`
  * **Was wurde geändert:** Die verbleibenden 8 Bytes von $D=200$ ($3 \times 64 = 192$ Bytes $+ 8$ Bytes) wurden von einer skalaren Schleife auf `_mm_loadu_si64`, `_mm_cvtepi8_epi16` und `_mm_madd_epi16` umgestellt.
  * **Theoretischer Zweck:** Vermeidung von Pipeline-Stalls durch skalare Verzweigungen im Tail.
  * **Reale Auswirkung:** **Gering.** 8 Bytes skalar auszuführen kostet auf Out-of-Order-Kernen ohnehin nur 2–3 Zyklen.

* **Teiländerung 5.2: Expliziter Prefetch der 4. Cacheline (`n_ptr + 192`)**
  * **Repo / Commit:** `DynamicExplorationGraph` @ `9809e310`
  * **Dateien:** `cpp/deglib/include/deglib/graph/internal_graph.h:578`
  * **Was wurde geändert:** Hinzufügen von `_mm_prefetch(n_ptr + 192, _MM_HINT_T0)`, um alle 4 Cachelines (0, 64, 128, 192) des 200-Byte-Vektors explizit vorzuladen.
  * **Theoretischer Zweck:** Verhindert Cache-Miss beim Lesen der letzten 8 Bytes des Vektors.
  * **Reale Auswirkung:** **Vernachlässigbar.** Hardware-Prefetcher laden benachbarte Cachelines meist automatisch mit.

---

#### Commit `18fbb2ac` (deglib) / `47459dd` (vibe) — *Run 7: 256B Contiguous Features & Adaptives Rerank*

* **Teiländerung 6.1: 256-Byte Aligned Contiguous Feature Speicher in `ReadOnlyGraph`**
  * **Repo / Commit:** `DynamicExplorationGraph` @ `18fbb2ac`
  * **Dateien:** `cpp/deglib/include/deglib/graph/readonly_graph.h:75-77, 132-155, 179-195`
  * **Was wurde geändert:** In `ReadOnlyGraph` wird ein zusammenhängender Puffer `contiguous_features_` angelegt, in dem jeder Vektor auf $256\text{ Bytes}$ gepaddet wird (`contiguous_stride_ = 256`).
  * **Theoretischer Zweck:** Ermöglicht voll ausgerichtete 512-Bit-Loads und verhindert Pufferüberläufe beim Laden von 64 Bytes für den 8-Byte-Rest.
  * **Reale Auswirkung:** **Mäßig.** Erhöht den Speicherverbrauch um $28\%$ ($200\text{ B} \rightarrow 256\text{ B}$ pro Knoten), verbessert aber die Speicherzugriffs-Ausrichtung.

* **Teiländerung 6.2: Vollständige Eliminierung des Tails im VNNI-Kernel**
  * **Repo / Commit:** `DynamicExplorationGraph` @ `18fbb2ac`
  * **Dateien:** `cpp/deglib/include/deglib/graph/internal_graph.h:510-530, 555-575`
  * **Was wurde geändert:** Dank des 256-Byte-Paddings wird der 4. Block einfach als 4. voller ZMM-Load (`_mm512_loadu_si512`) mit einem 4. `_mm512_dpbusd_epi32` ausgeführt. Die Dummy-Werte werden in der Query auf 0 maskiert.
  * **Theoretischer Zweck:** Einheitlicher 4-fach ungerollter VNNI-Pfad ohne jegliche Sonderbehandlung für den Rest.
  * **Reale Auswirkung:** **Gering.** Code-Vereinfachung, aber kaum Durchsatzunterschied zu Run 6.

* **Teiländerung 6.3: Adaptives / Reduziertes Reranking (`rerank_size_factor: [1.0, 1.1]`)**
  * **Repo / Commit:** `vibe` @ `47459dd`
  * **Dateien:** `vibe/algorithms/deg/config.yml`
  * **Was wurde geändert:** Aufnahme von `1.0` und `1.1` in die Rerank-Faktoren.
  * **Theoretischer Zweck:** Erhöhung des QPS bei niedrigen bis mittleren Recalls ($<98\%$), wo exaktes FP16-Reranking von 150 Vektoren überflüssig ist.
  * **Reale Auswirkung:** **Reines Konfigurations-Tuning.** Erklärt die hohen QPS-Werte bei Recall $90-95\%$ im Plot, ist aber keine Code-Verbesserung.

---

### Phase 3: Die neueren Commits (Run 16 bis 24)

Hier befinden sich die jüngsten Commits, die zu den "All-Time-Records" geführt haben sollen:

#### Commit `4408f665` (deglib) / `fd167a2` (vibe) — *Run 16: AVX-512 F16C 4-Way Batch Reranker*

* **Teiländerung 7.1: 4-Way Vektorisierter FP16 Reranker in `ExactRefiner::refine`**
  * **Repo / Commit:** `DynamicExplorationGraph` @ `4408f665`, `vibe` @ `fd167a2`
  * **Dateien:** `cpp/deglib/include/deglib/search/searcher.h:126-285`
  * **Was wurde geändert:** Im FP16-Reranker werden jeweils 4 Kandidaten-Vektoren (`v0`, `v1`, `v2`, `v3`) parallel geladen, per F16C (`_mm512_cvtph_ps` / `_mm256_cvtph_ps`) in Float konvertiert und gleichzeitig mit dem Query-Vektor multipliziert.
  * **Theoretischer Zweck:** Beschleunigung der FP16-Nachfilterung um Faktor 2–4.
  * **Reale Auswirkung:** **NAHEZU NULL (Schein-Optimierung!).**
    * *Begründung:* Bei $k=100$ und Rerank-Faktor $1.35$ werden exakt $135$ Vektoren rerankt.
    * Eine FP16-Distanz für $D=200$ dauert ca. $40\text{ ns}$. $135 \times 40\text{ ns} \approx 5,4\text{ µs}$.
    * Selbst wenn man diesen Schritt um den Faktor 2 beschleunigt, spart man $\approx 2,7\text{ µs}$.
    * Eine Query bei $ef=850$ dauert insgesamt $\approx 600\text{ µs}$ ($1.660\text{ QPS}$).
    * $2,7\text{ µs}$ Ersparnis bei $600\text{ µs}$ entsprechen **$< 0,45\%$** — das liegt weit unter der thermischen Messvarianz der CPU!

---

#### Commit `8bb8f02` (vibe) — *Run 17: Rerank 1.35x & ef=850*

* **Teiländerung 8.1: Aufnahme von `rerank=1.35x` und `ef=850` in `config.yml`**
  * **Repo / Commit:** `vibe` @ `8bb8f02`
  * **Dateien:** `vibe/algorithms/deg/config.yml`
  * **Was wurde geändert:** Reine YAML-Änderung: `rerank_size_factor` um `1.35` ergänzt, `ef` um `850` ergänzt.
  * **Theoretischer Zweck:** Den "Sweet Spot" für $99,90\%$ Recall treffen.
  * **Reale Auswirkung:** **100% Gitter-Artefakt.** Kein einziger C++-Befehl wurde geändert. Der Sprung von $1.576\text{ QPS}$ auf $1.662\text{ QPS}$ bei $99,9\%$ Recall entstand ausschließlich dadurch, dass $ef=850$ gewählt wurde statt $ef=900$.

---

#### Commit `13ad187e` (deglib) / `0ee1557` (vibe) — *Run 19: SIMD Medoid Scan & Dual-Accumulator VNNI*

Dieser Commit enthielt **drei gleichzeitige Teiländerungen**:

* **Teiländerung 9.1: AVX-512 VNNI SIMD Scan für 128 Medoide**
  * **Repo / Commit:** `DynamicExplorationGraph` @ `13ad187e`
  * **Dateien:** `cpp/deglib/include/deglib/graph/internal_graph.h:504-545`
  * **Was wurde geändert:** Die initiale Suche nach dem nächsten Einstiegspunkt scannt die 128 Medoide nicht mehr mit skalaren Aufrufen, sondern mit ungerollten AVX-512 VNNI Dot-Products und Prefetching des nächsten Medoids.
  * **Theoretischer Zweck:** Schnellere Initialisierung der Suche.
  * **Reale Auswirkung:** **NAHEZU NULL.** 128 Vektoren zu scannen passiert genau 1x pro Query. Ob das $4\text{ µs}$ oder $12\text{ µs}$ dauert, macht bei einer $600\text{ µs}$-Query weniger als $1\%$ Unterschied.

* **Teiländerung 9.2: Dual-Accumulator VNNI Loop (`sum02` und `sum13`)**
  * **Repo / Commit:** `DynamicExplorationGraph` @ `13ad187e`
  * **Dateien:** `cpp/deglib/include/deglib/graph/internal_graph.h:585-605`
  * **Was wurde geändert:** Im VNNI-Kernel wird die Akkumulation in zwei unabhängige Register `sum02` (Chunks 0 und 2) und `sum13` (Chunks 1 und 3) aufgeteilt, um Read-After-Write (RAW) Latenzen auf den FMA/VNNI-Pipes der CPU zu vermeiden.
  * **Theoretischer Zweck:** Erhöhung des Instruction-Level Parallelism (ILP) auf Zen 5 Kernen.
  * **Reale Auswirkung:** **Fraglich / Minimal.** Da der Durchsatz der Schleife durch Speicherlatenzen (Laden der Knotenvektoren aus dem L3/RAM) limitiert ist ("Memory-Bound"), wartet die CPU ohnehin auf Daten. Die 4 VNNI-Befehle sind nicht der Flaschenhals.

* **Teiländerung 9.3: Aligned 512-Bit Loads (`_mm512_load_si512`)**
  * **Repo / Commit:** `DynamicExplorationGraph` @ `13ad187e`
  * **Dateien:** `cpp/deglib/include/deglib/graph/internal_graph.h:582-585`
  * **Was wurde geändert:** Ersetzung von `_mm512_loadu_si512` (unaligned) durch `_mm512_load_si512` (aligned) für alle 4 Chunks.
  * **Theoretischer Zweck:** Vermeidung von Unaligned-Load-Strafen.
  * **Reale Auswirkung:** **Null.** Auf modernen x86-64 Architekturen (Zen 4/5, Intel Golden Cove) haben unaligned Loads, die keine Page-Grenze überschreiten, identische Latenz und Durchsatz wie aligned Loads.

---

#### Commits `9031f2c` & `5593c27` (vibe) — *Runs 20 & 21: Breiteres Rerank-Grid & ef=845*

* **Teiländerung 10.1: Feinstufige ef-Werte (`825, 835, 840, 845, 850, 875`)**
  * **Repo / Commit:** `vibe` @ `9031f2c`, `5593c27`
  * **Dateien:** `vibe/algorithms/deg/config.yml`
  * **Was wurde geändert:** Hinzufügen weiterer Zwischenwerte für `ef`, speziell `845`.
  * **Theoretischer Zweck:** Noch präzisere Punktlandung auf Recall $99,900\%$.
  * **Reale Auswirkung:** **100% Gitter-Artefakt.** `ef=845` erreichte $99,901\%$ Recall bei $1.694,8\text{ QPS}$. Das ist ein reiner Auswertungs-Effekt ohne jede Code-Änderung.

---

#### Commit `d9b89555` (deglib) / `617c3a8` (vibe) — *Run 24: Bitset `test_and_set`*

* **Teiländerung 11.1: Atomares / Inlined `Bitset::test_and_set`**
  * **Repo / Commit:** `DynamicExplorationGraph` @ `d9b89555`, `vibe` @ `617c3a8`
  * **Dateien:** `cpp/deglib/include/deglib/search/linear_pool.h:47-54`, `internal_graph.h:564-568, 644-648`
  * **Was wurde geändert:** Zusammenfassung von `if (pool.check_visited(v)) continue; pool.set_visited(v);` zu einer einzigen Methode:
    ```cpp
    [[nodiscard]] inline bool test_and_set(uint32_t i) noexcept {
        Block mask = Block(1) << (i & (block_size - 1));
        Block& word = data[i / block_size];
        if (word & mask) return true;
        word |= mask;
        return false;
    }
    ```
  * **Theoretischer Zweck:** Beseitigung eines doppelten Array-Zugriffs (`data[i / 64]`) und einer doppelten Bitmasken-Berechnung.
  * **Reale Auswirkung:** **Fraglich / Vernachlässigbar ($<1\%$).**
    * *Begründung:* Bei modernem C++ mit Compiler-Optimierung (`-O3`) und L1-Cache-Hit des Bitsets eliminierte der Optimizer die redundanten Adressberechnungen meist ohnehin (Common Subexpression Elimination).
    * Der im Commit behauptete Sprung auf $1.713\text{ QPS}$ (+18 QPS) liegt voll im Rahmen der üblichen Run-to-Run-Streuung ($1-2\%$).

---

## 4. Zusammenfassende Klassifizierungs-Matrix aller Teiländerungen

| ID | Teiländerung | Repo | Commit | Primäre Auswirkung | Realer Nutzen |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **T1.1** | `LinearPool` ($ef$-Budget-Suche) | deglib | `d47d4b17` | Algorithmus | **Sehr hoch (Fundament)** |
| **T1.2** | 64-Bit Word `Bitset` | deglib | `d47d4b17` | Speicherlayout | **Moderat positiv** |
| **T1.3** | Multi-Medoid Einstiegssuche | deglib | `d47d4b17` | Heuristik | **Gering / Fraglich** |
| **T1.4** | 2-Stufige Nachbarschleife | deglib | `d47d4b17` | Schleifenstruktur | **Moderat (ermöglicht Prefetch)** |
| **T1.5** | Feature Lookahead Prefetch (`po=4`) | deglib | `d47d4b17` | Hardware-Prefetch | **Gering / Unklar** |
| **T1.6** | Edge Prefetch bei Pool-Insert | deglib | `d47d4b17` | Hardware-Prefetch | **Sehr gering** |
| **T2.1** | Dynamisches `po`/`pl` | deglib | `d1b1090a` | Tuning | **Keine (reine Parametrisierung)** |
| **T2.2** | Prefetch Auto-Tuner (`optimize`) | deglib / vibe | `d1b1090a` / `6680dc4` | Heuristik | **Vernachlässigbar** |
| **T3.1** | K-Means 128 Medoide | vibe | `6680dc4` | Build-Heuristik | **Gering / Fraglich** |
| **T3.2** | Top-2 Einstiegspunkte | deglib | `0fc602e9` | Heuristik | **Nahezu null / eher Overhead** |
| **T4.1** | Query Register Caching (`q0..q2`) | deglib | `df273b65` | SIMD / Register | **Positiv** |
| **T4.2** | Inlined AVX-512 VNNI Kernel D=200 | deglib | `df273b65` | SIMD / Inlining | **Sehr hoch (Großer Sprung)** |
| **T5.1** | Vektorisierter 8-Byte Tail | deglib | `9809e310` | SIMD | **Sehr gering** |
| **T5.2** | 4. Cacheline Prefetch (`+192`) | deglib | `9809e310` | Hardware-Prefetch | **Vernachlässigbar** |
| **T6.1** | 256B Aligned Contiguous Features | deglib | `18fbb2ac` | Speicherlayout | **Moderat** |
| **T6.2** | Volle Tail-Eliminierung (4x VNNI) | deglib | `18fbb2ac` | SIMD | **Gering** |
| **T6.3** | Reduziertes Rerank (`1.0x, 1.1x`) | vibe | `47459dd` | Gitter-Tuning | **Schein-Gewinn (Gitter-Tuning)** |
| **T7.1** | 4-Way FP16 Batch Reranker | deglib | `4408f665` | SIMD / Rerank | **Schein-Gewinn (<0,5% Query-Zeit)** |
| **T8.1** | Rerank 1.35x & ef=850 | vibe | `8bb8f02` | Gitter-Tuning | **100% Gitter-Artefakt** |
| **T9.1** | SIMD Scan für 128 Medoide | deglib | `13ad187e` | SIMD / Entry | **Schein-Gewinn (<0,5% Query-Zeit)** |
| **T9.2** | Dual-Accumulator VNNI (`sum02/13`)| deglib | `13ad187e` | CPU-Pipeline | **Vernachlässigbar (Memory-bound)** |
| **T9.3** | Aligned Loads `_mm512_load_si512` | deglib | `13ad187e` | Instruktion | **Null (kein Effekt auf Zen 5)** |
| **T10.1**| Feinstes ef-Gitter (z. B. `ef=845`) | vibe | `9031f2c` / `5593c27` | Gitter-Tuning | **100% Gitter-Artefakt** |
| **T11.1**| Bitset `test_and_set` | deglib | `d9b89555` | Inlining | **Vernachlässigbar / Rauschen** |

---

## 5. Isolations- & Testplan: Was bringt jede Änderung alleine ausgehend von `main`?

Um wissenschaftlich sauber nachzuweisen, was jede Änderung tatsächlich wert ist, müssen wir vom sauberen `main`-Branch starten:
* `DynamicExplorationGraph`: Branch `main` (Commit `47f8c244`, Release v0.2.5)
* `vibe`: Branch `main` (Commit `1d1eb3d` bzw. `89dd5cf`)

### Test-Bedingungen (Invariante Referenz)
Damit keine Gitter-Artefakte die Ergebnisse verfälschen, muss bei **allen Tests ein festes, standardisiertes Testgitter** verwendet werden:
* **Datensatz**: `yandex-200-cosine` (1M Vektoren, 1.000 Queries, $D=200$, Top-100)
* **Graph**: Identischer vorberechneter FP32-Graph ($K=48$, `LowLID`, `prune_non_rng=False`)
* **Standardisiertes ef-Gitter**: `ef = [100, 150, 200, 250, 300, 400, 500, 600, 800, 1000]`
* **Standardisierter Rerank-Faktor**: fest `1.2x` und `1.5x` (keine willkürlichen Zwischenwerte wie 1.35x während der Isolation!)

---

### Schritt-für-Schritt Isolations-Experimente

#### Experiment 0: Baseline Verifikation auf `main`
* **Zustand:** Unmodifizierter `main`-Branch (`47f8c244` in deglib, `1d1eb3d` in vibe).
* **Messung:** Originale $\epsilon$-Suche (`search_eps: [0.0..0.1]`).
* **Erwartung:** Exakte Bestätigung der Run-0-Baseline ($2.876\text{ QPS} @ 98\%$, $2.180\text{ QPS} @ 99\%$, $1.855\text{ QPS} @ 99,5\%$, $1.001\text{ QPS} @ 99,96\%$).

---

#### Experiment 1: Solitärer `LinearPool` (T1.1 + T1.2)
* **Basis:** `main`
* **Änderung:** Ausschließlich `LinearPool` und `Bitset` implementieren.
  * **NICHT einbauen:** Keine Multi-Medoide (immer Start bei Knoten 0), kein Prefetching (`po=0`, kein Edge-Prefetch), Standard-Distanzaufrufe über den generischen Comparator.
* **Erkenntnisziel:** Wie viel bringt der Übergang von $\epsilon$-Radius auf festes $ef$-Budget alleine?

---

#### Experiment 2: Solitäre Multi-Medoid-Einstiegspunkte (T1.3 & T3.1)
* **Basis:** Experiment 1 (`LinearPool`)
* **Test A:** Start bei Knoten 0 vs. Start bei 128 zufälligen Medoiden vs. Start bei 128 K-Means Medoiden.
* **Erkenntnisziel:** Verbessert das K-Means-Medoid-Array die Recall/QPS-Kurve überhaupt messbar gegenüber einem festen Startknoten oder zufälligen Medoiden?

---

#### Experiment 3: Solitäre Top-2 Einstiegspunkte (T3.2)
* **Basis:** Experiment 2 (mit 128 Medoiden)
* **Test:** Top-1 Startmedoid vs. Top-2 Startmedoide im Pool.
* **Erkenntnisziel:** Bringt der zweite Einstiegspunkt mehr Recall pro Zeiteinheit oder ist er reiner Overhead?

---

#### Experiment 4: Solitäres Prefetching (T1.5 vs T1.6 vs Hardware-Prefetch)
* **Basis:** Experiment 1 (`LinearPool`)
* **Varianten:**
  1. Kein Software-Prefetching (rein CPU-Hardware-Prefetcher).
  2. Nur Feature-Prefetching (`po=4, 8, 14`).
  3. Nur Edge-Prefetching bei Pool-Insert.
  4. Beide kombiniert.
* **Erkenntnisziel:** Hat Software-Prefetching auf AMD Zen 5 überhaupt einen positiven Effekt, oder ist es neutral/kontraproduktiv?

---

#### Experiment 5: Solitärer Unrolled AVX-512 VNNI D=200 Kernel (T4.1 + T4.2)
* **Basis:** Experiment 1 (`LinearPool`)
* **Änderung:** Inlining der 3 ZMM-Query-Register und der ungerollten `_mm512_dpbusd_epi32`-Befehle in die Nachbarschleife.
* **Erkenntnisziel:** Isoliert den reinen SIMD-Rechenzeitgewinn gegenüber dem generischen Distanz-Funktionsaufruf.

---

#### Experiment 6: Solitäre 256B Aligned Features & Tail-Eliminierung (T6.1 + T6.2)
* **Basis:** Experiment 5 (VNNI Kernel)
* **Test:** 200B unaligned Features mit 8B Vektor-Tail vs. 256B gepaddete contiguous Features mit 4. VNNI-Block.
* **Erkenntnisziel:** Rechtfertigt der Geschwindigkeitsvorteil den $28\%$ höheren Speicherverbrauch?

---

#### Experiment 7: Solitärer 4-Way FP16 Batch Reranker (T7.1)
* **Basis:** Experiment 1 oder Experiment 6
* **Test:** Skalarer FP16-Reranker vs. 4-Way AVX-512 F16C Batch-Reranker bei fixem $k=100$ und Rerank-Faktor $1.5\times$.
* **Erkenntnisziel:** Quantifizierung des realen Zeitgewinns. (Hypothese: $< 0,5\%$ der Gesamtqueryzeit).

---

#### Experiment 8: Solitärer SIMD Medoid Scan (T9.1)
* **Basis:** Experiment 6
* **Test:** Skalare Schleife über 128 Medoide vs. SIMD-vektorisierter AVX-512 Scan.
* **Erkenntnisziel:** Beweis, ob der Medoid-Scan auf Gesamtsystemebene überhaupt messbar ist.

---

#### Experiment 9: Solitäre Dual-Accumulator VNNI Loop (T9.2)
* **Basis:** Experiment 6
* **Test:** Ein einziger `sum`-Akkumulator vs. getrennte `sum02` / `sum13`-Akkumulatoren.
* **Erkenntnisziel:** Zeigen, ob Zen 5 durch Register-Spaltung gewinnt oder ob Memory-Stalls den Durchsatz dominieren.

---

#### Experiment 10: Solitäres Bitset `test_and_set` (T11.1)
* **Basis:** Experiment 6
* **Test:** `check_visited()` gefolgt von separatem `set_visited()` vs. atomares `test_and_set()`.
* **Erkenntnisziel:** Beweis, ob der Run-24-Gewinn realer Natur oder reine Messfluktuation war.

---

## 6. Fazit & Empfehlung

Von den insgesamt **23 identifizierten Teiländerungen** lassen sich die realen Leistungsbringer auf eine sehr kleine Kernmenge reduzieren:
1. **`LinearPool` ($ef$-Suche) mit Bitset** (Architekturwechsel weg von $\epsilon$-Radius).
2. **Inlined unrolled AVX-512 VNNI D=200 Kernel** (drastische Beschleunigung der innersten Distanzschleife).
3. **256B Contiguous Aligned Feature Memory** (vollständige Eliminierung von Tail-Code).

Fast alle anderen Änderungen (SIMD Medoid Scan, 4-Way FP16 Reranker, Dual-Akkumulatoren, Bitset `test_and_set`, Prefetch Auto-Tuner, Top-2 Entrypoints) sind entweder **mikroskopische Optimierungen abseits des Hauptengpasses** oder **reine Schein-Gewinne durch gezielte Wahl von Zwischengitterpunkten (`ef=845`, `rerank=1.35x`)**.

Mit dem obigen Isolationsplan kann nun jede Teiländerung solitär von `main` ausgehend auf Herz und Nieren geprüft werden.
