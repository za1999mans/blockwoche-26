"""Validiert den Markdown-Korpus und erzeugt Chunks ohne externe Abhängigkeiten."""
from pathlib import Path
from urllib.parse import urlparse, unquote
import hashlib, json, re
from research_hs import ROOT, CACHE, DATE

DATA=ROOT.parent
manifest=json.loads((DATA/'studiengaenge_manifest.json').read_text())
byfile={r['datei']:r for r in manifest}
errors=[]
files=[DATA/f'{i:02d}_{s}.md' for i,s in [(1,'ueber_die_hochschule'),(2,'bewerbung_und_fristen'),(3,'campus_und_standorte'),(5,'tag_der_offenen_tuer_faq'),(6,'nc_auswahlgrenzen')]]+[DATA/r['datei'] for r in manifest]
required=['Studiengangs-Basisdaten','Profil & Inhalte','Modulübersicht & Curricula','Zulassung & Fristen','Berufsperspektiven','Direktlinks & Quellen']
if len(manifest)!=128:errors.append(f'Erwartet: 128 Studiengangseinträge; vorhanden: {len(manifest)}')
if len({r['id'] for r in manifest})!=len(manifest):errors.append('Doppelte Studiengangs-IDs')
if len(set(r['datei'] for r in manifest))!=len(manifest):errors.append('Doppelte Dateipfade')
source_records={}
for p in CACHE.glob('*.json'):
    r=json.loads(p.read_text())
    source_records[r['url']]=r
    if r.get('final_url'):source_records[r['final_url']]=r
for f in files:
    if not f.is_file():errors.append(f'Fehlende Datei: {f}');continue
    text=f.read_text()
    for label,url in re.findall(r'\[([^\]]*)\]\(([^)]+)\)',text):
        u=urlparse(url)
        if u.scheme in ['https','http','mailto'] or url.startswith('#'):continue
        target=(f.parent/unquote(u.path)).resolve()
        if not target.exists():errors.append(f'{f.name}: Interner Link fehlt: {url}')
    rec=byfile.get(str(f.relative_to(DATA)))
    if rec:
        for h in required:
            if f'## {h}\n' not in text:errors.append(f'{f.name}: Pflichtabschnitt fehlt: {h}')
        for u in [rec['quelle'],rec.get('modulhandbuch')]:
            if u and source_records.get(u,{}).get('status')!=200:errors.append(f'{f.name}: Hauptquelle nicht erfolgreich verifiziert: {u}')
        if 'auslaufend' in rec['studiengang'].lower() and 'auslaufend' not in text.lower():errors.append(f'{f.name}: Auslaufstatus fehlt')
    if re.search(r'\b(?:TODO|TBD|Lorem ipsum)\b',text,re.I):errors.append(f'{f.name}: Unaufgelöster Platzhalter')
    # Every Markdown table must have a stable column count within its contiguous block.
    expected=None
    for line in text.splitlines():
        if line.startswith('|'):
            count=len(re.findall(r'(?<!\\)\|',line))
            if expected is None:expected=count
            elif count!=expected:errors.append(f'{f.name}: Tabellenzeile mit abweichender Spaltenzahl')
        else:expected=None
if errors:
    (ROOT/'validation.json').write_text(json.dumps({'status':'failed','errors':errors},ensure_ascii=False,indent=2))
    raise SystemExit('\n'.join(errors[:25]))

chunks=[]
def emit(f,title,heading,content,metadata):
    if not content.strip():return
    body=f'# {title}\n\nAbschnitt: {heading}\n\n'+content.strip()
    local=sorted(set(re.findall(r'\]\((https?://[^)]+)\)',content)))
    sources=list(dict.fromkeys(([metadata.get('quelle')] if metadata.get('quelle') else [])+local+metadata.get('_section_sources',[])))
    chunks.append({'id':hashlib.sha256((str(f.relative_to(DATA))+heading+body).encode()).hexdigest()[:24],
        'text':body,'file':str(f.relative_to(DATA)),'document_title':title,'heading':heading,
        'institution':'Hochschule Osnabrück','studiengang':metadata.get('studiengang'),
        'abschluss':metadata.get('abschluss'),'campus':metadata.get('standort'),
        'status':metadata.get('status'),'source_urls':sources,'retrieved_at':DATE})

for f in files:
    raw=f.read_text();body=re.sub(r'^---\n.*?\n---\n','',raw,flags=re.S)
    title=next(t[2:] for t in body.splitlines() if t.startswith('# '))
    meta=byfile.get(str(f.relative_to(DATA)),{})
    sections=[];heading='Einleitung';buf=[]
    for line in body.splitlines():
        if line.startswith('## '):
            if buf:sections.append((heading,'\n'.join(buf)))
            heading=line[3:];buf=[]
        elif not line.startswith('# '):buf.append(line)
    if buf:sections.append((heading,'\n'.join(buf)))
    for heading,section in sections:
        sectionmeta={**meta,'_section_sources':sorted({u for u in re.findall(r'\]\((https?://[^)]+)\)',section) if '/module/' not in u})}
        # Split at paragraphs; keep table header and individual rows together.
        blocks=section.strip().split('\n\n');current=''
        for block in blocks:
            if block.startswith('|'):
                if current:emit(f,title,heading,current,sectionmeta);current=''
                tablelines=block.splitlines();header='\n'.join(tablelines[:2]);part=header
                for row in tablelines[2:]:
                    if len(part)+len(row)>3000 and part!=header:
                        emit(f,title,heading,part,sectionmeta);part=header
                    part+='\n'+row
                emit(f,title,heading,part,sectionmeta)
            elif len(current)+len(block)>3000:
                if current:emit(f,title,heading,current,sectionmeta)
                current=block
            else:current+=('\n\n' if current else '')+block
        if current:emit(f,title,heading,current,sectionmeta)
rag=DATA/'_rag';rag.mkdir(exist_ok=True)
(rag/'chunks.jsonl').write_text(''.join(json.dumps(c,ensure_ascii=False)+'\n' for c in chunks))
all_sources=[]
for u,r in sorted(source_records.items()):
    if u!=r['url']:continue
    all_sources.append({k:r[k] for k in ['url','final_url','title','accessed','status','content_type','error'] if k in r})
(ROOT/'quellen_manifest.json').write_text(json.dumps(all_sources,ensure_ascii=False,indent=2))
gaps=json.loads((ROOT/'luecken.json').read_text())
stats={'studiengangsdateien':len(manifest),'mit_curriculum':sum(bool(r['curriculum_zeilen']) for r in manifest),'curriculum_zeilen':sum(r['curriculum_zeilen'] for r in manifest),'mit_modulhandbuch_pdf':sum(bool(r['modulhandbuch']) for r in manifest),'mit_html_schluesselmodulen':sum(bool(r['schluesselmodule']) for r in manifest),'inhaltliche_markdown_dateien':len(files),'rag_chunks':len(chunks),'quellenabrufe':len(all_sources)}
report=['---\nid: hsos-recherchequalitaet\nrecherchestand: 2026-10-28\nnicht_als_fachwissen_indexieren: true\n---\n','# Hochschule Osnabrück: Abdeckung und Quellenqualität\n','## Tatsächliche Abdeckung\n',f'Das offizielle A–Z-Verzeichnis umfasst beim Abruf 128 Einträge. Für **alle 128 Einträge** liegt eine eigene Markdown-Datei vor. Die Verzeichniszahl schließt Varianten, Teilstudiengänge und auslaufende Angebote ein.\n','| Prüfung / Inhalt | Ergebnis |\n| --- | --- |']
for k,v in stats.items():report.append(f'| {k} | {v} |')
report+=['','Die Curriculumtabellen enthalten je nach Originalquelle einzelne Semester, Studienjahre oder ausdrücklich zusammengefasste Studienphasen. Eine Phasenübersicht ist keine vollständige semesterweise Modulmatrix. Die Schlüsselmodulzahl zählt HTML-Beschreibungen; in weiteren Angeboten werden Details durch PDF-Modulhandbücher nachgewiesen.\n','## Quellen und Nachweisführung\n','Die Recherche nutzt das offizielle Studienverzeichnis, die zugehörigen Profil- und Bewerbungsseiten, Studienverlaufsseiten, verlinkte Modulbeschreibungen, Modulhandbücher und Ordnungen. Für Besucherfragen kommen die gemeinsame ZSB, das HIT-Portal und das Studierendenwerk als zuständige Originalquellen hinzu.\n','Das Quellenmanifest in `_recherche/quellen_manifest.json` dokumentiert URL, Abrufdatum, HTTP-Status und gegebenenfalls Fehler. Unpassende oder fehlerhafte Hintergrundlinks wurden nicht als alleinige Nachweise für Fachinformationen verwendet. Ein erreichbarer Link belegt nicht automatisch die Gültigkeit jeder Information für jeden Einschreibejahrgang.\n','Die großen HTML-/PDF-Snapshots sind in einem temporären Cache außerhalb von `HS_DATA` aufbewahrt. Den Cachepfad dokumentiert `_recherche/cache_location.json`. Der RAG-Export enthält ausschließlich die aufbereiteten inhaltlichen Dokumente.\n','## Dokumentierte Quellenwidersprüche\n']
for r in manifest:
    for issue in r['quellenkonflikte']:report.append(f'- [{r["studiengang"]}]({r["datei"]}): {issue}')
report+=['','Die ZSB-Seite `hit-2026` enthält im Text eine widersprüchliche Jahreszahl 2027 für die Programmverlinkung. Das Veranstaltungsdatum 19.11.2026 ist durch Hochschulankündigung und HIT-Portal übereinstimmend belegt. In den Besucherinformationen wird die widersprüchliche Verlinkungsfrist nicht fortgeschrieben.\n','## Verbleibende Datenlücken je Angebot\n','Diese Liste ist eine inhaltliche Offenlegung der Recherchegrenzen. Ein fehlender PDF-Link bedeutet, dass in den ausgewerteten Quellen kein eindeutig zugeordnetes öffentliches Modulhandbuch-PDF nachgewiesen wurde. Besonders duale Angebote verweisen teilweise auf die Anforderung beim Institut für Duale Studiengänge. Ein fehlender Nachweis wird nicht als „keine Voraussetzung“ oder „kein Modul vorhanden“ ausgelegt.\n','| Studiengang | Noch nicht als eigenständige Detaildaten erfasst |\n| --- | --- |']
group={}
for g in gaps:group.setdefault((g['studiengang'],g['datei']),[]).append(g['punkt'])
for (name,fn),items in group.items():report.append(f'| [{name}](04_studiengaenge/{fn}) | {"; ".join(items)} |')
report+=['','## Technische Prüfung\n','Alle 128 Studiengangs-IDs und Dateipfade sind eindeutig. Pflichtabschnitte, lokale Verlinkungen der Inhaltsdateien, Tabellen-Spaltenzahlen, Primärquellen und verwendete Modulhandbuch-PDFs wurden automatisch geprüft. Die Hauptquellen und eingebundenen Modulhandbuch-PDFs wurden erfolgreich abgerufen. Zusätzliche Modul- und Amtsblattlinks können aus den Originalseiten übernommene weiterführende Links sein; nicht jeder einzelne dieser Hintergrundlinks wurde separat abgerufen.\n','## Aktualisierung\n','Fristen und Eignungsprüfungstermine vor jeder neuen Bewerbungsphase überprüfen. Den Veranstaltungskalender vor einem Besuch aktualisieren. Für Curricula und Modulhandbücher Studienordnung und Einschreibejahrgang berücksichtigen. Statistiken, Semesterbeiträge und historische NC-Daten behalten ihren angegebenen Bezugszeitraum.\n','Quelle der Abdeckungsreferenz: [Studiengänge A–Z der Hochschule Osnabrück](https://www.hs-osnabrueck.de/studium/studienangebot/studiengaenge-a-z/), Abruf 28.10.2026.']
(DATA/'07_recherchequalitaet.md').write_text('\n'.join(report)+'\n')
(ROOT/'validation.json').write_text(json.dumps({'status':'passed','recherchestand':DATE,'stats':stats,'errors':errors},ensure_ascii=False,indent=2))
print(json.dumps({'status':'passed',**stats},ensure_ascii=False))
