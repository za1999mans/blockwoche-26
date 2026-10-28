# Hochschul-Chatbot und persistenter Vektorindex

Die Datenquelle ist `HS_DATA/_rag/chunks.jsonl`: 1.687 vorbereitete Textabschnitte aus 133 Inhaltsdokumenten, einschließlich der 128 Studiengangsdateien. Der Import speichert die Texte, Metadaten und echten API-Embeddings dauerhaft in `data/hs_vector_index.sqlite3`.

Für diesen Datenumfang wird kein separater Datenbankserver benötigt: SQLite hält die Daten auf der Festplatte; NumPy berechnet die exakte Kosinusähnlichkeit mit den geladenen Vektoren im Arbeitsspeicher. Es wird keine SQLite-Vektorerweiterung und kein externer Vektordatenbankdienst vorausgesetzt.

## Starten

Alle Befehle im Projektordner ausführen. Die vorhandene Poetry-Umgebung enthält die benötigten Pakete.

```bash
# Import durchführen oder nach Änderungen fortsetzen
poetry run python index_hs_data.py index

# Status ohne API-Aufruf prüfen
poetry run python index_hs_data.py status

# Lokale Chatoberfläche starten
poetry run streamlit run hochschul_chatbot.py --server.address 127.0.0.1
```

Die Oberfläche ist anschließend normalerweise unter `http://localhost:8501` erreichbar. Sie bietet einen Gesprächsverlauf, Filter nach Standort, Abschluss und Studiengang sowie Quellen zu den Antworten. Der Index wird beim Start geladen; das Starten der Oberfläche erzeugt keine neuen Dokument-Embeddings.

## Mit Besuchern ins Gespräch kommen

Der Chat startet mit einer Begrüßung und anklickbaren Themen. Die Gesprächssteuerung unterscheidet Smalltalk, Orientierung, Rückfragen und fachliche Auskünfte. Beispielsweise wird „Hallo“ ohne Wissenssuche beantwortet. Bei „Wie viele Semester sind hier geplant?“ fragt der Bot nach dem Studiengang. Mehrdeutige Namen werden nach Abschluss oder Standort geklärt.

Die bestätigte Auswahl bleibt für Folgefragen erhalten. Sie wird ausschließlich aus Nutzerangaben und dem offiziellen Studiengangskatalog abgeleitet. Eine frühere Modellantwort oder ein zufälliger Suchtreffer bestimmt den Studiengang nicht. Die Suche bleibt quellenbasiert; die Antwort soll kurz und natürlich klingen und bei Bedarf eine einzelne passende Rückfrage stellen. Antwortbuttons helfen bei der nächsten Frage.

Ein typischer Ablauf:

1. „Hallo“ → freundliche Begrüßung und Frage nach dem Interesse.
2. „Wie viele Semester?“ → Rückfrage zum gewünschten Studiengang.
3. „Informatik“ → gegebenenfalls Bachelor/Master klären.
4. „Bachelor“ → die ursprüngliche Semesterfrage für das geklärte Angebot beantworten.
5. „Und welche Inhalte erwarten mich?“ → denselben Studiengang weiter besprechen.

## Fragen sprechen und Antworten anhören

Über das Mikrofon im Eingabefeld eine Frage aufnehmen, die Aufnahme stoppen und abschicken. Der Browser benötigt dazu die Mikrofonfreigabe. Die Frage wird transkribiert und durch dieselbe Gesprächs- und Wissenslogik verarbeitet. Bei gesprochenen Fragen wird die Antwort anschließend mit einer KI-Stimme vorgelesen.

Für getippte Fragen lässt sich „Antworten vorlesen“ in der Seitenleiste einschalten. Außerdem hat jede Botnachricht die Schaltfläche „Antwort anhören“. Bereits erzeugtes Audio bleibt für die Wiedergabe in der Sitzung gespeichert. Quellenmarkierungen und URLs werden beim Vorlesen ausgelassen; die Quellen bleiben im Text aufklappbar.

Die Spracheingabe arbeitet mit einzelnen Aufnahmen. Die Sprachausgabe verwendet die aktuelle Realtime-API als Vorlesestimme für die zuvor erzeugte Textantwort. Nutzeraufnahmen und Antwortaudio werden in der Oberfläche im Sitzungsspeicher verarbeitet und nicht als Audiodateien gespeichert. Für die Sprachfunktionen wird auch bei einem anderen Chatprovider `OPENAI_API_KEY` benötigt.

Optionale Spracheinstellungen: `HS_TRANSCRIPTION_MODEL` (Standard `gpt-transcribe`), `HS_VOICE_MODEL` (Standard `gpt-realtime-2.1-mini`) und `HS_VOICE` (Standard `marin`). Die vorhandenen Vektoren müssen für die Gesprächs- und Sprachfunktionen nicht neu erstellt werden.

Die Sprach-API-Anbindung orientiert sich an der [offiziellen Dokumentation zur Transkription](https://developers.openai.com/api/docs/guides/speech-to-text) und den [Realtime-Audioereignissen](https://developers.openai.com/api/docs/guides/realtime-conversations), geprüft am 28.10.2026.

## Konfiguration

Zugangsdaten bleiben ausschließlich in der lokalen `.env` oder in Umgebungsvariablen. Der Import verwendet `OPENAI_API_KEY`. Der Schlüssel wird nicht in der Datenbank, den Metadaten oder der Konsolenausgabe gespeichert.

Optionale Einstellungen:

| Variable | Standard | Bedeutung |
| --- | --- | --- |
| `HS_RAG_DB` | `data/hs_vector_index.sqlite3` im Projekt | Speicherort des Index |
| `HS_EMBEDDING_MODEL` | `text-embedding-3-small` | Modell für den nächsten Import |
| `HS_CHAT_PROVIDER` | `openai` | Anbieter für Antworten; der bestehende Wrapper unterstützt auch `deepseek` |
| `HS_CHAT_MODEL` | `gpt-4o-mini` | Modell für Antworten |

Dokument- und Fragevektoren verwenden immer dasselbe Embedding-Modell: Die Suche liest es aus dem gespeicherten Index. Eine Änderung des Chatmodells erfordert keine neuen Embeddings. Ein Wechsel des Embedding-Modells erfordert einen erneuten Import; alte Vektoren werden nicht mit neuen vermischt. Für `deepseek` muss der vorhandene Wrapper entsprechend mit `DEEPSEEK_API_KEY` und einem geeigneten `HS_CHAT_MODEL` konfiguriert werden. Die Embeddings werden weiterhin über OpenAI erzeugt.

## Importverhalten

- Vor dem ersten API-Aufruf werden JSON-Struktur, eindeutige IDs, Quellen und Eingabegrößen geprüft.
- Für die Embeddings werden Markdown-Linktexte verwendet; lange URL-Zeichenketten bleiben als Quellen erhalten, werden aber nicht mit eingebettet.
- Ein SHA-256-Hash des vorbereiteten Textes erkennt unveränderte Inhalte. Ein zweiter unveränderter Import benötigt keine Embedding-Aufrufe.
- Die API wird mit begrenzten Batches aufgerufen. Nach jedem erfolgreichen Batch werden die Vektoren gespeichert.
- Bei einem Abbruch bleiben fertige Batches für die Wiederaufnahme erhalten. Ein vorhandener vollständiger Index bleibt bis zum erfolgreichen Abschluss des Updates nutzbar.
- Gelöschte Chunks verschwinden beim erfolgreichen nächsten Import aus der aktiven Sammlung. Ihre alten Embeddings dürfen für spätere Wiederverwendung im Cache verbleiben.
- Geänderte Quellenmetadaten werden aktualisiert, ohne denselben Text erneut einzubetten.
- API-Fehler werden ohne rohe HTTP-Antworten oder Zugangsdaten ausgegeben. Bei ausgeschöpftem Kontingent muss zunächst die API-Abrechnung geklärt werden; ein vorhandener Schlüssel allein belegt kein verfügbares Kontingent.

Eine Planung ohne API-Aufruf und ohne Schreibzugriff:

```bash
poetry run python index_hs_data.py index --dry-run
```

Der Status unterscheidet einen vollständigen Index (`ready: true`) von einem begonnenen, noch unvollständigen Import. `source_changed` zeigt, ob die Chunk-Datei seit dem veröffentlichten Import verändert wurde.

## Suche und Antworten im Terminal

```bash
poetry run python index_hs_data.py search "Welche Inhalte hat Informatik?"

poetry run python index_hs_data.py search "Welche Module hat Wirtschaftsinformatik?" --campus Lingen --degree B.Sc.

poetry run python index_hs_data.py ask "Wann findet der Hochschulinfotag 2026 statt?"

poetry run python index_hs_data.py ask "Wie bewerbe ich mich für Soziale Arbeit?" --programme "Soziale Arbeit (B.A.)"
```

Eine neue Suchfrage benötigt nur ein Frage-Embedding. Wiederholte identische Fragen werden innerhalb derselben geladenen Indexinstanz zwischengespeichert. Die Antwortgenerierung ist ein separater Modellaufruf. `search` ruft kein Chatmodell auf.

Standardmäßig werden bis zu sechs Treffer mit Kosinusähnlichkeit von mindestens 0,25 verwendet; pro Dokument höchstens drei Abschnitte. Diese Schwelle ist eine einstellbare Heuristik, keine kalibrierte Wahrscheinlichkeit. `--top-k` und `--min-score` erlauben Anpassungen. Auslaufende Angebote sind standardmäßig ausgeschlossen und können im Terminal mit `--include-archived` einbezogen werden. Allgemeine Bewerbungs- und Campusdokumente werden auch bei Studiengangsfiltern berücksichtigt.

Der Chatbot wird angewiesen, ausschließlich die gefundenen Belege zu verwenden, Fristen mit Semester anzugeben und historische NC-Werte sowie auslaufende Angebote korrekt einzuordnen. Ohne ausreichende Suchtreffer wird kein Chatmodell aufgerufen; stattdessen erfolgt ein Hinweis auf die fehlenden Belege und die Studienberatung. Die Quellenanzeige verwendet die tatsächlich gespeicherten URLs.

## Daten aktualisieren

Nach Änderungen der Markdown-Inhalte zunächst den Chunk-Export aktualisieren. Die Vorbereitungsskripte benötigen ihren dokumentierten Recherchecache, sofern der gesamte Rechercheprozess erneut ausgeführt wird. Alternativ die betroffenen Chunk-Datensätze gezielt aktualisieren und danach den Import starten:

```bash
poetry run python index_hs_data.py index
```

Der Import liest ausdrücklich die JSONL-Datei; Änderungen allein an Markdown-Dateien werden nicht automatisch zu neuen Embeddings. Quellenstand und Datumsbezug bleiben entscheidend: Ein neu berechnetes Embedding aktualisiert keine abgelaufene Bewerbungsfrist.

## Prüfung und Dateien

```bash
poetry run python -m unittest discover -s tests -v
```

Die Offline-Tests prüfen unter anderem die dauerhafte Speicherung, Wiederverwendung unveränderter Inhalte, Metadatenupdates, entfernte Chunks, Modellwechsel, Dimensionsfehler, Wiederaufnahme nach Abbruch, Filter und den Verzicht auf freie Modellantworten ohne Suchbelege.

Die echte Integrationsprüfung benötigt API-Zugriff und prüft sechs Besucherfragen sowie optional eine Chatantwort:

```bash
poetry run python verify_hs_rag.py --answers
```

Der verbesserte Mehrschritt-Dialog und ein synthetischer Audio-Rundlauf lassen sich zusätzlich prüfen:

```bash
poetry run python verify_hs_dialogue.py --audio
```

Der Sprachtest erzeugt eine kurze deutsche Testfrage und transkribiert diese wieder. Er prüft die API-Anbindung; eine Aufnahme mit dem physischen Besuchermikrofon wird dadurch nicht getestet. Das Ergebnis steht lokal in `data/hs_dialogue_verification.json`.

Der lokale Prüfbericht steht danach in `data/hs_rag_verification.json`. Die erstmalige Prüfung fand die erwarteten Quellen für alle sechs Fragen und erzeugte eine passende Antwort zum Hochschulinfotag. Das ist ein Funktionstest, keine umfassende Bewertung aller möglichen Beratungsfragen.

| Datei | Aufgabe |
| --- | --- |
| `hs_rag.py` | Import, SQLite-Speicher, Vektorsuche und quellenbasierte Antworten |
| `hs_dialogue.py` | Begrüßung, Rückfragen, Interessenerkundung und Studiengangskontext |
| `hs_voice.py` | Transkription und natürlich gesprochene Antworten |
| `index_hs_data.py` | CLI für Import, Status, Suche und Antworten |
| `hochschul_chatbot.py` | Streamlit-Chatoberfläche |
| `tests/test_hs_rag.py` | Offline-Tests mit ausdrücklich simulierten Embeddings |
| `data/hs_vector_index.sqlite3` | Echter lokaler Index; über `.gitignore` ausgeschlossen |

Die Produktivdatenbank wird ausschließlich mit echten API-Embeddings aufgebaut. Die Testvektoren landen nur in temporären Testdatenbanken.

API-Referenz: [Offizielle OpenAI-Dokumentation zur Embedding-Erstellung und zu Eingabegrenzen](https://developers.openai.com/api/reference/python/resources/embeddings/methods/create), geprüft am 28.10.2026.
