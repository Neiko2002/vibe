# Master-Testplan: Systematische Überprüfung & Bereinigung aller AutoResearch-Optimierungen

Dieses Dokument definiert den verbindlichen Ablauf zur wissenschaftlichen Überprüfung und Bereinigung aller im Rahmen der AutoResearch-Session eingebrachten Code- und Konfigurationsänderungen.

---

## 1. Kontext & Ausgangsbasis

In den bisherigen Sessions wurden zahlreiche Heuristiken, SIMD-Kernel und Gitteranpassungen vorgenommen. Wie im Dokument [`AUTORESEARCH_TEILAENDERUNGEN.md`](AUTORESEARCH_TEILAENDERUNGEN.md) forensisch dargelegt wurde, basieren viele der gemeldeten Rekorde auf Scheineffekten (z. B. feinstufige Zwischengitterpunkte wie `ef=845` oder Micro-Optimierungen an Codestellen, die $<1\%$ der Gesamtlaufzeit ausmachen).

### Die verifizierte Ausgangsbasis
Als neutrale Referenz für diesen Testplan dient der bereinigte Status-Quo-Vergleich:
* **Report:** [`PARETO_BASELINE_COMPARISON.md`](PARETO_BASELINE_COMPARISON.md)
* **Plot:** [`deg_vs_glass_pareto_baseline.png`](deg_vs_glass_pareto_baseline.png)
* **Suchgitter:** 45 wohlverteilte Punkte (`ef = [60..1000]`, `rerank = [1.0, 1.15, 1.35]`), frei von Ballungen im 95%-Bereich.

### Historische Testreihen & Alt-Pläne (Archiv)
Alle früheren, teilweise verworfenen oder durch Fehlschläge geprägten Pläne und Logs wurden zur Entlastung des Arbeitsbereichs in den Unterordner [`archived/`](archived/) verschoben:
* [`archived/AUTORESEARCH_PLAN_DEG_VS_GLASS.md`](archived/AUTORESEARCH_PLAN_DEG_VS_GLASS.md): Ursprünglicher Phase-1-Plan.
* [`archived/AUTORESEARCH_PLAN_PHASE2.md`](archived/AUTORESEARCH_PLAN_PHASE2.md): Phase-2-Plan (Kantenmatrix, hierarchisches Routing), der aufgrund von Pareto-Verschlechterungen in Commit `37ddba2` zurückgerollt wurde.
* [`archived/AUTORESEARCH_PLAN_BEATING_GLASS_HIGH_RECALL.md`](archived/AUTORESEARCH_PLAN_BEATING_GLASS_HIGH_RECALL.md): High-Recall-Fokusplan für Recall-Raten $>99\%$.
* [`archived/EXPERIMENT_RESULTS.md`](archived/EXPERIMENT_RESULTS.md): Historisches Gesamt-Log der Runs 0 bis 24.
* [`archived/EXPERIMENT_IDEAS_ROADMAP.md`](archived/EXPERIMENT_IDEAS_ROADMAP.md): Sammlung früherer Ideen und Ansätze.

---

## 2. Test-Methodik: Das Ablation-Prinzip (Top-Down)

Um zweifelsfrei nachzuweisen, ob eine Änderung im aktuellen Gesamtgefüge **überhaupt noch eine messbare Wirkung hat**, wenden wir primär das **Ablation-Verfahren (gezielter Rückbau)** an:

### Vorgehensweise je Test
1. **Ausgangspunkt:** Der aktuelle Stand (`HEAD` in beiden Repos).
2. **Intervention:** Wir deaktivieren bzw. entfernen im C++-Code genau **eine einzige Teiländerung**.
3. **Re-Build:** Schneller C++ Inplace-Build (`setup.py build_ext --inplace`).
4. **Benchmark:** Ausführen des standardisierten Benchmarks:
   ```bash
   uv run python evaluate_pareto_baseline.py
   ```
   (Dauer: ca. 45 Sekunden mit geladenem Graph-Cache).
5. **Differenz-Messung:** Vergleich der resultierenden Pareto-Front gegen die Ausgangsbasis (`PARETO_BASELINE_COMPARISON.md`).

### Signifikanz- und Entscheidungskriterien

| Messergebnis ($\Delta \text{QPS}$ bei identischem Recall) | Bewertung | Konsequenz |
| :--- | :--- | :--- |
| **$< -1.5\%$** (Code wird ohne Feature messbar langsamer) | **Echtes Feature** | Feature wird beibehalten und dokumentiert. |
| **$\pm 1.0\%$** (Innerhalb der thermischen Messvarianz) | **Wirkungslos / Toter Code** | **Vollständiges Löschen des Codes!** Codebasis wird bereinigt. |
| **$> +1.0\%$** (Code wird ohne Feature sogar *schneller*) | **Verdeckte Regression** | **Sofortiges Entfernen / Revert.** |

---

## 3. Strukturierter Test-Ablauf in 4 Blöcken

### Block A: Verdächtige Micro-Optimierungen (Höchste Bereinigungspriorität)

Diese Änderungen stehen unter dringendem Verdacht, reine Schein-Optimierungen abseits des Hauptengpasses zu sein.

#### Test A1: Bitset `test_and_set` (Run 24, Commit `d9b89555`)
* **Hypothese:** `vis.test_and_set(v)` spart keine Zyklen gegenüber separatem `check_visited(v)` gefolgt von `set_visited(v)`, da das 125-KB-Bitset im L2-Cache liegt und der Compiler redundante Adressberechnungen ohnehin wegoptimiert.
* **Test:** Ersetzen von `if (!pool.test_and_set_visited(v))` durch die klassische Abfrage:
  ```cpp
  if (pool.check_visited(v)) continue;
  pool.set_visited(v);
  ```
* **Erwartung:** $\Delta \text{QPS} \approx 0\%$. Bei Bestätigung: `test_and_set` aus `Bitset` und `LinearPool` rückstandsfrei löschen.

#### Test A2: Dual-Accumulator VNNI Loop (`sum02` / `sum13`) (Run 19, Commit `13ad187e`)
* **Hypothese:** Die Graphentraversierung ist speicherbandbreiten- und latenzlimitiert (Cache-Misses beim Laden der Vektoren). Die Entkopplung der VNNI-Instruktionen in zwei Akkumulatoren bringt auf Zen 5 keinen Gewinn, da die Ausführungseinheiten auf Daten warten.
* **Test:** Rückbau auf einen einzelnen Akkumulator `sum` mit 4 sequentiellen `_mm512_dpbusd_epi32`.
* **Erwartung:** $\Delta \text{QPS} \approx 0\%$. Bei Bestätigung: Vereinfachung des SIMD-Codes auf Standard-Akkumulation.

#### Test A3: SIMD Medoid Scan (Run 19, Commit `13ad187e`)
* **Hypothese:** 128 Einstiegsmedoide werden genau **einmal** pro Query gescannt ($<0,5\%$ der Queryzeit). Ob diese Distanzen skalar oder per AVX-512 VNNI berechnet werden, hat keinen messbaren Einfluss auf den Gesamtdurchsatz.
* **Test:** Ersatz des ungerollten VNNI-Medoid-Scans durch die generische skalare Einstiegssuche.
* **Erwartung:** $\Delta \text{QPS} < 0,3\%$. Bei Bestätigung: Entfernung des redundanten Medoid-SIMD-Blocks in `searchEfImpl`.

#### Test A4: 4-Way FP16 Batch Reranker (Run 16, Commit `4408f665`)
* **Hypothese:** Das Reranking betrifft nur $100 \times 1.35 = 135$ Vektoren am Ende der Suche. Über $95\%$ der Zeit entfallen auf das Graph-Routing. Der 4-fach ungerollte F16C-Reranker spart maximal $2\text{ µs}$ pro Query.
* **Test:** Deaktivieren der 4-Way-Schleife in `ExactRefiner::refine`, Rückfall auf die sequentielle FP16-Distanz.
* **Erwartung:** $\Delta \text{QPS} < 0,5\%$. Bei Bestätigung: Löschen von 150 Zeilen komplexem Vektor-Casting in `searcher.h`.

#### Test A5: Top-2 Medoid Einstiegspunkte (Run 4, Commit `0fc602e9`)
* **Hypothese:** Das Einfügen von zwei Startmedoiden in den Pool bringt bei DEG (dank weitreichender Kanten) keinen Recall-Vorteil gegenüber dem besten Medoid, erzeugt aber doppelten Initialisierungs-Overhead.
* **Test:** Pool nur mit `ep1` initialisieren (`ep2` ignorieren).
* **Erwartung:** Identischer Recall bei leicht höherem oder gleichem QPS. Bei Bestätigung: Entfernen der `ep2`-Verwaltung.

---

### Block B: Software-Prefetching Analyse

Moderne AMD Zen-5-Kerne verfügen über extrem leistungsfähige Hardware-Prefetcher. Software-Prefetching (`_mm_prefetch`) kann Hardware-Streaming stören oder nutzlos sein.

#### Test B1: Vektor-Lookahead Prefetching (`po=14`, `pl=3`) vs. `po=0`
* **Test:** `set_prefetch(0, 0)` setzen (vollständiges Abschalten der `_mm_prefetch`-Befehle in der Distanzschleife).
* **Erkenntnisziel:** Messung des realen Nutzens des Vektor-Prefetchings. Falls Zen 5 ohne Software-Prefetching gleich schnell ist, entfällt der gesamte Prefetch-Overhead samt Auto-Tuner.

#### Test B2: Kantenlisten-Prefetching bei `pool.insert`
* **Test:** Auskommentieren von `memory::prefetch(graph.getNeighborIndices(v))` beim Einfügen in den `LinearPool`.
* **Erkenntnisziel:** Prüfen, ob das spekulative Laden der Nachbarn tatsächlich Cache-Treffer erzeugt oder bis zur tatsächlichen Expansion längst wieder verdrängt wird.

---

### Block C: Speicherlayout & Tail-Handling

#### Test C1: 256B Aligned Contiguous Features vs. 200B Unaligned (Run 7, Commit `18fbb2ac`)
* **Hintergrund:** Run 7 vergrößerte den Speicherbedarf pro Knoten von 200 auf 256 Bytes ($+28\%$ RAM-Bedarf), um 64-Byte-Aligned Loads zu ermöglichen und den 8-Byte-Rest per vollem ZMM-Befehl zu laden.
* **Test:** Vergleich des 256B-Paddings gegen 200B unaligned Speicher mit maskiertem Load.
* **Erkenntnisziel:** Rechtfertigt der geringe Geschwindigkeitsvorteil den Mehrverbrauch von rund $56\text{ MB}$ Speicher im L3/RAM?

---

### Block D: Kern-Architektur (Bottom-Up Verifikation gegen `main`)

#### Test D1: Isolierter Nutzen von `LinearPool` ($ef$-Budget)
* **Test:** Clean Branch auf `main` (`47f8c244`), nur `LinearPool` + `Bitset` ohne jede weitere Heuristik einspielen.
* **Erkenntnisziel:** Nachweis des wahren Fundaments: Wie viel Prozent des gesamten Leistungssprungs entfällt allein auf den Wechsel von $\epsilon$-Radius zu $ef$-Pool?

---

## 4. Ausführungs- und Protokoll-Matrix

Für jeden durchgeführten Test wird folgendes standardisiertes Protokoll ausgefüllt:

| Test ID | Beschreibung | $\Delta$ QPS @ 95% | $\Delta$ QPS @ 98% | $\Delta$ QPS @ 99% | $\Delta$ QPS @ 99.9% | Urteil | Maßnahme |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **A1** | Bitset `test_and_set` entfernt | *TBD* | *TBD* | *TBD* | *TBD* | *TBD* | *TBD* |
| **A2** | Dual-Accumulator entfernt | *TBD* | *TBD* | *TBD* | *TBD* | *TBD* | *TBD* |
| **A3** | SIMD Medoid Scan entfernt | *TBD* | *TBD* | *TBD* | *TBD* | *TBD* | *TBD* |
| **A4** | 4-Way FP16 Reranker entfernt | *TBD* | *TBD* | *TBD* | *TBD* | *TBD* | *TBD* |
| **A5** | Top-2 Entrypoints entfernt | *TBD* | *TBD* | *TBD* | *TBD* | *TBD* | *TBD* |
| **B1** | Vektor-Prefetch deaktiviert (`po=0`) | *TBD* | *TBD* | *TBD* | *TBD* | *TBD* | *TBD* |
| **B2** | Edge-Prefetch deaktiviert | *TBD* | *TBD* | *TBD* | *TBD* | *TBD* | *TBD* |
| **C1** | 200B unaligned vs. 256B aligned | *TBD* | *TBD* | *TBD* | *TBD* | *TBD* | *TBD* |

---

## 5. Bereinigungsziel

Das Ziel dieses Plans ist eine **radikale Bereinigung der Codebasis**:
* Entfernung aller wirkungslosen Spezialpfade und Schein-Optimierungen.
* Beibehaltung ausschließlich derjenigen Mechanismen, die auf Zen 5 einen belegbaren, signifikanten Speedup liefern.
* Ein schlanker, robuster C++-Core ohne unnötige Verzweigungen oder fragwürdige Heuristiken.
