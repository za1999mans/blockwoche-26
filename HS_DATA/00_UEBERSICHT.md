# Wissensbasis Hochschule Osnabrück: Dateiübersicht

Recherche- und Quellenstand: **28. Oktober 2026**. Diese Wissensbasis dient der Studienorientierung und Beratung beim Hochschulinfotag.

| Datei / Ordner | Inhalt |
| --- | --- |
| [01_ueber_die_hochschule.md](01_ueber_die_hochschule.md) | Hochschulprofil, Zahlen mit Bezugssemester, Fakultäten und Kontakte |
| [02_bewerbung_und_fristen.md](02_bewerbung_und_fristen.md) | Bewerbungswege, Hochschulstart, reguläre und abweichende Fristen, Zugang und Sprache |
| [03_campus_und_standorte.md](03_campus_und_standorte.md) | Westerberg, Caprivi, Haste und Lingen; Gebäude, Ausstattung, Anreise und Pläne |
| [04_studiengaenge/00_index.md](04_studiengaenge/00_index.md) | Verlinkter Index aller **128 einzelnen Studiengangsdateien** |
| `04_studiengaenge/*.md` | Je ein Dokument pro offiziellem A–Z-Eintrag mit Basisdaten, Curriculum, Schlüsselmodulen, Zugang, Berufsfeldern und Quellen |
| [05_tag_der_offenen_tuer_faq.md](05_tag_der_offenen_tuer_faq.md) | HIT am 19.11.2026, Besuchsplanung, Beratung, Wohnen, BAföG und Semesterbeiträge |
| [06_nc_auswahlgrenzen.md](06_nc_auswahlgrenzen.md) | Historische NC-Tabellen mit aufbereiteten Werten und sechs PDF-Direktquellen |
| [07_recherchequalitaet.md](07_recherchequalitaet.md) | Tatsächliche Abdeckung, Quellenkonflikte und verbleibende Informationslücken |
| [studiengaenge_manifest.json](studiengaenge_manifest.json) | Maschinenlesbare Zuordnung von Studiengang, Datei, Quellen, Abschluss und Campus |
| `_rag/chunks.jsonl` | Vorbereitete Textabschnitte mit Kontext, Dokument-ID und Quellen für den RAG-Import |
| `_recherche/` | Skripte und Recherchenachweise; kein inhaltlicher RAG-Korpus |

Beispiele für einzelne Studiengangsdokumente:

- [Agrarsystemtechnologien (B.Sc.)](04_studiengaenge/agrarsystemtechnologien_b_sc.md)
- [Informatik (B.Sc.), achtsemestriges Modell](04_studiengaenge/informatik_b_sc.md)
- [Betriebswirtschaft und Management (B.A.), Osnabrück](04_studiengaenge/betriebswirtschaft_und_management_b_a.md)
- [Soziale Arbeit (B.A.)](04_studiengaenge/soziale_arbeit_b_a.md)
- [Land Use Transformation (M.Sc.)](04_studiengaenge/land_use_transformation_m_sc.md)

## RAG-Import

Für den Import stehen die Abschnitte in `_rag/chunks.jsonl` bereit. Jeder Datensatz enthält Text, Dokumenttitel, Studiengangskontext, Abschnitt, Quelldatei, Quellen-URLs und Recherchestand. Das Projekt enthält jetzt einen persistenten SQLite-Vektorspeicher, eine Suchanbindung und eine Streamlit-Chatoberfläche. Import und Start beschreibt [README_RAG.md](../README_RAG.md). Ob der lokale Import vollständig abgeschlossen ist, zeigt `poetry run python index_hs_data.py status`; die Markdown-Dateien allein erzeugen noch keinen Index.

Alternativ nur die inhaltlichen Markdown-Dateien `01_*.md`, `02_*.md`, `03_*.md`, `04_studiengaenge/*.md` außer `00_index.md`, `05_*.md` und `06_*.md` einlesen. `00_UEBERSICHT.md`, `07_recherchequalitaet.md`, JSON-Dateien und `_recherche/` nicht als fachliche Antworten indexieren. Den vorgefertigten Chunkexport und dieselben Markdown-Inhalte nicht gleichzeitig doppelt importieren.

Die Markdown-Dateien enthalten YAML-Metadaten, klare Überschriften und Quellen in den Abschnitten. Beim eigenen Chunking Dokumenttitel, Studiengang, Abschluss, Standort und Quellen-URL als Metadaten an jeden Chunk weiterreichen. Tabellen mit wiederholter Kopfzeile nach Zeilen teilen, damit Semester, Modulart und Modulbezeichnungen zusammenbleiben.

## Auskunftsregeln für den Chatbot

- Konkrete Hochschulquellen aus dem gefundenen Abschnitt nennen.
- Gleichnamige Angebote nach Stadt, Campus, Abschluss und Studienmodell unterscheiden.
- Auslaufende Angebote nicht als aktuell offen bewerben.
- Bewerbungsfristen nur mit Zielsemester und Bewerbungsweg ausgeben; vergangene Verlängerungen nicht fortschreiben.
- Historische NC-Werte ausdrücklich als Ergebnisse des genannten Semesters erklären.
- Fehlende Angaben und dokumentierte Quellenwidersprüche offen benennen und die passende Fachberatung verlinken.
- Zahlen, Beiträge, Termine und Curricula gelten für ihren dokumentierten Bezugszeitraum beziehungsweise Einschreibejahrgang.

Quellenbasis für die Abdeckungsprüfung: [Offizielles Studienverzeichnis der Hochschule Osnabrück](https://www.hs-osnabrueck.de/studium/studienangebot/studiengaenge-a-z/). Die 128 Einträge umfassen Varianten, Teilstudiengänge und auslaufende Angebote; sie sind keine Zahl gleichzeitig offener Bewerbungsverfahren.
