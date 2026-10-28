---
id: hsos-recherchequalitaet
recherchestand: 2026-10-28
nicht_als_fachwissen_indexieren: true
---

# Hochschule Osnabrück: Abdeckung und Quellenqualität

## Tatsächliche Abdeckung

Das offizielle A–Z-Verzeichnis umfasst beim Abruf 128 Einträge. Für **alle 128 Einträge** liegt eine eigene Markdown-Datei vor. Die Verzeichniszahl schließt Varianten, Teilstudiengänge und auslaufende Angebote ein.

| Prüfung / Inhalt | Ergebnis |
| --- | --- |
| studiengangsdateien | 128 |
| mit_curriculum | 127 |
| curriculum_zeilen | 1030 |
| mit_modulhandbuch_pdf | 91 |
| mit_html_schluesselmodulen | 104 |
| inhaltliche_markdown_dateien | 133 |
| rag_chunks | 1687 |
| quellenabrufe | 1431 |

Die Curriculumtabellen enthalten je nach Originalquelle einzelne Semester, Studienjahre oder ausdrücklich zusammengefasste Studienphasen. Eine Phasenübersicht ist keine vollständige semesterweise Modulmatrix. Die Schlüsselmodulzahl zählt HTML-Beschreibungen; in weiteren Angeboten werden Details durch PDF-Modulhandbücher nachgewiesen.

## Quellen und Nachweisführung

Die Recherche nutzt das offizielle Studienverzeichnis, die zugehörigen Profil- und Bewerbungsseiten, Studienverlaufsseiten, verlinkte Modulbeschreibungen, Modulhandbücher und Ordnungen. Für Besucherfragen kommen die gemeinsame ZSB, das HIT-Portal und das Studierendenwerk als zuständige Originalquellen hinzu.

Das Quellenmanifest in `_recherche/quellen_manifest.json` dokumentiert URL, Abrufdatum, HTTP-Status und gegebenenfalls Fehler. Unpassende oder fehlerhafte Hintergrundlinks wurden nicht als alleinige Nachweise für Fachinformationen verwendet. Ein erreichbarer Link belegt nicht automatisch die Gültigkeit jeder Information für jeden Einschreibejahrgang.

Die großen HTML-/PDF-Snapshots sind in einem temporären Cache außerhalb von `HS_DATA` aufbewahrt. Den Cachepfad dokumentiert `_recherche/cache_location.json`. Der RAG-Export enthält ausschließlich die aufbereiteten inhaltlichen Dokumente.

## Dokumentierte Quellenwidersprüche

- [Agrarsystemtechnologien (B.Sc.)](04_studiengaenge/agrarsystemtechnologien_b_sc.md): Die Überschrift der Bewerbungsseite nennt abweichend B.Eng.; A–Z-Verzeichnis und Studienprofil führen B.Sc. Außerdem enthält die Bewerbungsseite einen DoSV-Hinweis, obwohl die zentrale Tabelle für Wintersemester 2026/2027 keine DoSV-Teilnahme nennt. Verfahren vor einer neuen Bewerbung beim Studierendensekretariat prüfen.
- [Angewandte Geflügelwissenschaften (M.Sc.) (auslaufend)](04_studiengaenge/angewandte_gefluegelwissenschaften_m_sc_auslaufend.md): Der Verzeichniseintrag enthält keinen nutzbaren Studiengangs-Direktlink. Daher werden keine Inhalte der Hochschulstartseite als Studiengangsinformation übernommen.
- [Auditing, Finance and Taxation (M.A.), berufsbegleitend](04_studiengaenge/auditing_finance_and_taxation_m_a_berufsbegleitend.md): Der Verzeichniseintrag enthält keinen nutzbaren Studiengangs-Direktlink. Daher werden keine Inhalte der Hochschulstartseite als Studiengangsinformation übernommen.
- [Nachhaltige Dienstleistungs- und Ernährungswirtschaft (M.Sc.)](04_studiengaenge/nachhaltige_dienstleistungs_und_ernaehrungswirtschaft_m_sc.md): Das Profil nennt Münster als Standort, das A–Z-Verzeichnis Osnabrück. Das Kooperationsangebot und die konkreten Lehrorte auf der Fachseite beziehungsweise mit der Koordination klären.
- [Wirtschaftsinformatik (B.Sc.), Standort Lingen (Ems)](04_studiengaenge/wirtschaftsinformatik_b_sc_standort_lingen_ems.md): Das Profil enthält die widersprüchliche Formulierung „Bachelor of Arts (B.Sc.)“. Hier wird der im Studiengangstitel und A–Z-Verzeichnis angegebene Abschluss B.Sc. verwendet.
- [Wirtschaftsingenieurwesen (MBA), berufsbegleitend](04_studiengaenge/wirtschaftsingenieurwesen_mba_berufsbegleitend.md): Das A–Z-Verzeichnis ordnet das Angebot Lingen zu; das Profil nennt als Standort Osnabrück. Den Präsenzort vor einem Besuch mit der Studiengangskoordination klären.

Die ZSB-Seite `hit-2026` enthält im Text eine widersprüchliche Jahreszahl 2027 für die Programmverlinkung. Das Veranstaltungsdatum 19.11.2026 ist durch Hochschulankündigung und HIT-Portal übereinstimmend belegt. In den Besucherinformationen wird die widersprüchliche Verlinkungsfrist nicht fortgeschrieben.

## Verbleibende Datenlücken je Angebot

Diese Liste ist eine inhaltliche Offenlegung der Recherchegrenzen. Ein fehlender PDF-Link bedeutet, dass in den ausgewerteten Quellen kein eindeutig zugeordnetes öffentliches Modulhandbuch-PDF nachgewiesen wurde. Besonders duale Angebote verweisen teilweise auf die Anforderung beim Institut für Duale Studiengänge. Ein fehlender Nachweis wird nicht als „keine Voraussetzung“ oder „kein Modul vorhanden“ ausgelegt.

| Studiengang | Noch nicht als eigenständige Detaildaten erfasst |
| --- | --- |
| [Allgemeiner Maschinenbau (B.Sc.), Standort Lingen (Ems)](04_studiengaenge/allgemeiner_maschinenbau_b_sc_standort_lingen_ems.md) | Kein eindeutig zugeordnetes öffentliches Modulhandbuch-PDF |
| [Angewandte Geflügelwissenschaften (M.Sc.) (auslaufend)](04_studiengaenge/angewandte_gefluegelwissenschaften_m_sc_auslaufend.md) | Keine unmittelbar auslesbare semesterweise HTML-Modulliste; Kein eindeutig zugeordnetes öffentliches Modulhandbuch-PDF; Einzelmoduldetails nur über PDF oder Anfrage; keine auswertbaren HTML-Modulbeschreibungen; Berufsfeldliste nicht strukturiert extrahierbar |
| [Auditing, Finance and Taxation (M.A.), berufsbegleitend](04_studiengaenge/auditing_finance_and_taxation_m_a_berufsbegleitend.md) | Kein eindeutig zugeordnetes öffentliches Modulhandbuch-PDF |
| [Bauen - Umwelt - Management (M.Eng.)](04_studiengaenge/bauen_umwelt_management_m_eng.md) | Einzelmoduldetails nur über PDF oder Anfrage; keine auswertbaren HTML-Modulbeschreibungen |
| [Berufliche Bildung – Teilstudiengang Fahrzeugtechnik (B.Sc.)](04_studiengaenge/berufliche_bildung_teilstudiengang_fahrzeugtechnik_b_sc.md) | Kein eindeutig zugeordnetes öffentliches Modulhandbuch-PDF |
| [Berufliche Bildung – Teilstudiengang Informationstechnik (B.Sc.)](04_studiengaenge/berufliche_bildung_teilstudiengang_informationstechnik_b_sc.md) | Kein eindeutig zugeordnetes öffentliches Modulhandbuch-PDF |
| [Betriebswirtschaft und nachhaltiges Management (B.A.), dual, Standort Lingen (Ems)](04_studiengaenge/betriebswirtschaft_und_nachhaltiges_management_b_a_dual_standort_lingen_ems.md) | Kein eindeutig zugeordnetes öffentliches Modulhandbuch-PDF; Einzelmoduldetails nur über PDF oder Anfrage; keine auswertbaren HTML-Modulbeschreibungen |
| [Bioverfahrenstechnik in der Lebensmittelindustrie (B.Sc.)](04_studiengaenge/bioverfahrenstechnik_in_der_lebensmittelindustrie_b_sc.md) | Kein eindeutig zugeordnetes öffentliches Modulhandbuch-PDF |
| [Business Management (M.A.)](04_studiengaenge/business_management_m_a.md) | Kein eindeutig zugeordnetes öffentliches Modulhandbuch-PDF; Berufsfeldliste nicht strukturiert extrahierbar |
| [Dentaltechnologie (B.Sc.)](04_studiengaenge/dentaltechnologie_b_sc.md) | Kein eindeutig zugeordnetes öffentliches Modulhandbuch-PDF |
| [Design Entrepreneurship (M.A.)](04_studiengaenge/design_entrepreneurship_m_a.md) | Kein eindeutig zugeordnetes öffentliches Modulhandbuch-PDF; Einzelmoduldetails nur über PDF oder Anfrage; keine auswertbaren HTML-Modulbeschreibungen |
| [ETS - Chemische Prozesstechnik/Verfahrenstechnik (B.Eng.), dual, Standort Lingen (Ems)](04_studiengaenge/ets_chemische_prozesstechnik_verfahrenstechnik_b_eng_dual_standort_lingen_ems.md) | Kein eindeutig zugeordnetes öffentliches Modulhandbuch-PDF; Einzelmoduldetails nur über PDF oder Anfrage; keine auswertbaren HTML-Modulbeschreibungen |
| [ETS - Elektrotechnik (B.Eng.), dual, Standort Lingen (Ems)](04_studiengaenge/ets_elektrotechnik_b_eng_dual_standort_lingen_ems.md) | Kein eindeutig zugeordnetes öffentliches Modulhandbuch-PDF; Einzelmoduldetails nur über PDF oder Anfrage; keine auswertbaren HTML-Modulbeschreibungen |
| [ETS - Maschinenbau (B.Eng.), dual, Standort Lingen (Ems)](04_studiengaenge/ets_maschinenbau_b_eng_dual_standort_lingen_ems.md) | Kein eindeutig zugeordnetes öffentliches Modulhandbuch-PDF; Einzelmoduldetails nur über PDF oder Anfrage; keine auswertbaren HTML-Modulbeschreibungen |
| [ETS - Mechatronik (B.Eng.), dual, Standort Lingen (Ems)](04_studiengaenge/ets_mechatronik_b_eng_dual_standort_lingen_ems.md) | Kein eindeutig zugeordnetes öffentliches Modulhandbuch-PDF; Einzelmoduldetails nur über PDF oder Anfrage; keine auswertbaren HTML-Modulbeschreibungen |
| [ETS - Technische Informatik (B.Eng.), dual, Standort Lingen (Ems)](04_studiengaenge/ets_technische_informatik_b_eng_dual_standort_lingen_ems.md) | Kein eindeutig zugeordnetes öffentliches Modulhandbuch-PDF; Einzelmoduldetails nur über PDF oder Anfrage; keine auswertbaren HTML-Modulbeschreibungen |
| [Führung und Organisation (M.A.), dual, Standort Lingen (Ems)](04_studiengaenge/fuehrung_und_organisation_m_a_dual_standort_lingen_ems.md) | Kein eindeutig zugeordnetes öffentliches Modulhandbuch-PDF; Einzelmoduldetails nur über PDF oder Anfrage; keine auswertbaren HTML-Modulbeschreibungen; Berufsfeldliste nicht strukturiert extrahierbar |
| [Hebammenwissenschaft (B.Sc.), dual](04_studiengaenge/hebammenwissenschaft_b_sc_dual.md) | Kein eindeutig zugeordnetes öffentliches Modulhandbuch-PDF |
| [HELPP – Versorgungsforschung und -gestaltung (M.Sc.)](04_studiengaenge/helpp_versorgungsforschung_und_gestaltung_m_sc.md) | Kein eindeutig zugeordnetes öffentliches Modulhandbuch-PDF |
| [Informatik (B.Sc.)](04_studiengaenge/informatik_b_sc.md) | Kein eindeutig zugeordnetes öffentliches Modulhandbuch-PDF; Einzelmoduldetails nur über PDF oder Anfrage; keine auswertbaren HTML-Modulbeschreibungen |
| [Ingenieurwissenschaften (B.Sc.)](04_studiengaenge/ingenieurwissenschaften_b_sc.md) | Kein eindeutig zugeordnetes öffentliches Modulhandbuch-PDF; Einzelmoduldetails nur über PDF oder Anfrage; keine auswertbaren HTML-Modulbeschreibungen |
| [International Event Management Shanghai (B.A.)](04_studiengaenge/international_event_management_shanghai_b_a.md) | Kein eindeutig zugeordnetes öffentliches Modulhandbuch-PDF |
| [Internationale Ökonomie und Nachhaltigkeit (B.A.) (vormals Volkswirtschaftslehre)](04_studiengaenge/internationale_oekonomie_und_nachhaltigkeit_b_a_vormals_volkswirtschaftslehre.md) | Kein eindeutig zugeordnetes öffentliches Modulhandbuch-PDF |
| [Kommunikation und Management (M.A.), Standort Lingen (Ems)](04_studiengaenge/kommunikation_und_management_m_a_standort_lingen_ems.md) | Berufsfeldliste nicht strukturiert extrahierbar |
| [Land Use Transformation (M.Sc.)](04_studiengaenge/land_use_transformation_m_sc.md) | Einzelmoduldetails nur über PDF oder Anfrage; keine auswertbaren HTML-Modulbeschreibungen |
| [Landschaftsarchitektur (M.Eng.)](04_studiengaenge/landschaftsarchitektur_m_eng.md) | Einzelmoduldetails nur über PDF oder Anfrage; keine auswertbaren HTML-Modulbeschreibungen |
| [Landschaftsbau (B.Eng.)](04_studiengaenge/landschaftsbau_b_eng.md) | Einzelmoduldetails nur über PDF oder Anfrage; keine auswertbaren HTML-Modulbeschreibungen |
| [Landschaftsbau Dual (B.Eng.)](04_studiengaenge/landschaftsbau_dual_b_eng.md) | Einzelmoduldetails nur über PDF oder Anfrage; keine auswertbaren HTML-Modulbeschreibungen |
| [Landschaftsentwicklung (B.Eng.)](04_studiengaenge/landschaftsentwicklung_b_eng.md) | Berufsfeldliste nicht strukturiert extrahierbar |
| [Lehramt an berufsbildenden Schulen – Teilstudiengang Fahrzeugtechnik (M.Ed.)](04_studiengaenge/lehramt_an_berufsbildenden_schulen_teilstudiengang_fahrzeugtechnik_m_ed.md) | Kein eindeutig zugeordnetes öffentliches Modulhandbuch-PDF |
| [Lehramt an berufsbildenden Schulen – Teilstudiengang Informationstechnik (M.Ed.)](04_studiengaenge/lehramt_an_berufsbildenden_schulen_teilstudiengang_informationstechnik_m_ed.md) | Kein eindeutig zugeordnetes öffentliches Modulhandbuch-PDF |
| [Management betrieblicher Systeme – Betriebswirtschaft (B.A.), dual, Standort Lingen (Ems)](04_studiengaenge/management_betrieblicher_systeme_betriebswirtschaft_b_a_dual_standort_lingen_ems.md) | Kein eindeutig zugeordnetes öffentliches Modulhandbuch-PDF; Einzelmoduldetails nur über PDF oder Anfrage; keine auswertbaren HTML-Modulbeschreibungen |
| [Management betrieblicher Systeme – Wirtschaftsingenieurwesen (B.Eng.), dual, Standort Lingen (Ems)](04_studiengaenge/management_betrieblicher_systeme_wirtschaftsingenieurwesen_b_eng_dual_standort_lingen_ems.md) | Kein eindeutig zugeordnetes öffentliches Modulhandbuch-PDF; Einzelmoduldetails nur über PDF oder Anfrage; keine auswertbaren HTML-Modulbeschreibungen |
| [Multiprofessionelle Gesundheits- und Sozialversorgung (B.Sc.), dual, Standort Lingen (Ems)](04_studiengaenge/multiprofessionelle_gesundheits_und_sozialversorgung_b_sc_dual_standort_lingen_ems.md) | Kein eindeutig zugeordnetes öffentliches Modulhandbuch-PDF; Einzelmoduldetails nur über PDF oder Anfrage; keine auswertbaren HTML-Modulbeschreibungen |
| [Nachhaltige Dienstleistungs- und Ernährungswirtschaft (M.Sc.)](04_studiengaenge/nachhaltige_dienstleistungs_und_ernaehrungswirtschaft_m_sc.md) | Kein eindeutig zugeordnetes öffentliches Modulhandbuch-PDF; Einzelmoduldetails nur über PDF oder Anfrage; keine auswertbaren HTML-Modulbeschreibungen |
| [Nachhaltige Materialtechnologie und Produktentwicklung (B.Sc.)](04_studiengaenge/nachhaltige_materialtechnologie_und_produktentwicklung_b_sc.md) | Kein eindeutig zugeordnetes öffentliches Modulhandbuch-PDF |
| [Nachhaltige Materialtechnologie und Produktentwicklung im Praxisverbund (B.Sc.)](04_studiengaenge/nachhaltige_materialtechnologie_und_produktentwicklung_im_praxisverbund_b_sc.md) | Kein eindeutig zugeordnetes öffentliches Modulhandbuch-PDF |
| [Pflege (B.Sc.), dual, Standort Lingen (Ems)](04_studiengaenge/pflege_b_sc_dual_standort_lingen_ems.md) | Einzelmoduldetails nur über PDF oder Anfrage; keine auswertbaren HTML-Modulbeschreibungen |
| [Physiotherapy (B.Sc.)](04_studiengaenge/physiotherapy_b_sc.md) | Kein eindeutig zugeordnetes öffentliches Modulhandbuch-PDF |
| [Soziale Arbeit: Teilhabe zukunftsorientiert gestalten (M.A.) (vormals Soziale Arbeit: Lokale Gestaltung sozialer Teilhabe)](04_studiengaenge/soziale_arbeit_teilhabe_zukunftsorientiert_gestalten_m_a_vormals_soziale_arbeit_lokale_gestaltung_sozialer_teilhabe.md) | Kein eindeutig zugeordnetes öffentliches Modulhandbuch-PDF |
| [Taxation (LL.M.)](04_studiengaenge/taxation_ll_m.md) | Kein eindeutig zugeordnetes öffentliches Modulhandbuch-PDF |
| [Technologieanalyse, -engineering und -management (M.Eng.), dual, Standort Lingen (Ems)](04_studiengaenge/technologieanalyse_engineering_und_management_m_eng_dual_standort_lingen_ems.md) | Kein eindeutig zugeordnetes öffentliches Modulhandbuch-PDF; Einzelmoduldetails nur über PDF oder Anfrage; keine auswertbaren HTML-Modulbeschreibungen; Berufsfeldliste nicht strukturiert extrahierbar |
| [Theaterpädagogik (B.A.), Standort Lingen (Ems)](04_studiengaenge/theaterpaedagogik_b_a_standort_lingen_ems.md) | Kein eindeutig zugeordnetes öffentliches Modulhandbuch-PDF |
| [Wirtschaftsinformatik und nachhaltige IT (B.Sc.), dual, Standort Lingen (Ems)](04_studiengaenge/wirtschaftsinformatik_und_nachhaltige_it_b_sc_dual_standort_lingen_ems.md) | Kein eindeutig zugeordnetes öffentliches Modulhandbuch-PDF; Einzelmoduldetails nur über PDF oder Anfrage; keine auswertbaren HTML-Modulbeschreibungen |
| [Wirtschaftsingenieurwesen und nachhaltige Entwicklung (B.Eng.), dual, Standort Lingen (Ems)](04_studiengaenge/wirtschaftsingenieurwesen_und_nachhaltige_entwicklung_b_eng_dual_standort_lingen_ems.md) | Kein eindeutig zugeordnetes öffentliches Modulhandbuch-PDF; Einzelmoduldetails nur über PDF oder Anfrage; keine auswertbaren HTML-Modulbeschreibungen |

## Technische Prüfung

Alle 128 Studiengangs-IDs und Dateipfade sind eindeutig. Pflichtabschnitte, lokale Verlinkungen der Inhaltsdateien, Tabellen-Spaltenzahlen, Primärquellen und verwendete Modulhandbuch-PDFs wurden automatisch geprüft. Die Hauptquellen und eingebundenen Modulhandbuch-PDFs wurden erfolgreich abgerufen. Zusätzliche Modul- und Amtsblattlinks können aus den Originalseiten übernommene weiterführende Links sein; nicht jeder einzelne dieser Hintergrundlinks wurde separat abgerufen.

## Aktualisierung

Fristen und Eignungsprüfungstermine vor jeder neuen Bewerbungsphase überprüfen. Den Veranstaltungskalender vor einem Besuch aktualisieren. Für Curricula und Modulhandbücher Studienordnung und Einschreibejahrgang berücksichtigen. Statistiken, Semesterbeiträge und historische NC-Daten behalten ihren angegebenen Bezugszeitraum.

Quelle der Abdeckungsreferenz: [Studiengänge A–Z der Hochschule Osnabrück](https://www.hs-osnabrueck.de/studium/studienangebot/studiengaenge-a-z/), Abruf 28.10.2026.
