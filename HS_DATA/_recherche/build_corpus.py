"""Erzeugt zitierbare Studiengangsdokumente aus den recherchierten Originalquellen.

Aufruf: python3 HS_DATA/_recherche/build_corpus.py
Keine Netzwerkzugriffe; keine Projekt-Abhängigkeiten.
"""
from pathlib import Path
import json, re, sys, unicodedata
from urllib.parse import urlparse
from research_hs import ROOT, CACHE, BASE, DATE, Node, cached, document, links, lines, parse

DATA = ROOT.parent
OUT = DATA/'04_studiengaenge'
OUT.mkdir(exist_ok=True)
INDEX = BASE+'/studium/studienangebot/studiengaenge-a-z/'
APPLY = BASE+'/studium/rund-ums-studium/bewerbung/'
NC = APPLY+'zulassungsfreie-und-zulassungsbeschraenkte-studiengaenge/'
PROGRAMS=json.loads((ROOT/'programs.json').read_text())
ENRICH=json.loads((ROOT/'enrichment.json').read_text()) if (ROOT/'enrichment.json').exists() else {}

def tidy(s):
    return re.sub(r'\s+',' ',re.sub(r't3://\S+','',s.replace('\xad','').replace('\u200b',''))).strip(' |\t\n')
def esc(s):return tidy(str(s)).replace('|','&#124;').replace('<','&lt;').replace('>','&gt;')
def slug(s):
    for a,b in [('ä','ae'),('ö','oe'),('ü','ue'),('Ä','Ae'),('Ö','Oe'),('Ü','Ue'),('ß','ss')]:s=s.replace(a,b)
    return re.sub(r'[^a-z0-9]+','_',unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower()).strip('_')
def link(label,url):return f'[{esc(label)}]({url})'
def unique(ls):return list(dict.fromkeys(ls))
def field(ll, labels):
    for key in labels:
        for i,t in enumerate(ll[:-1]):
            if tidy(t).lower().rstrip(':')==key.lower():
                value=tidy(ll[i+1])
                if value and len(value)<450:return value
    return ''
def words(s,n=20):return ' '.join(tidy(s).split()[:n])
def excerpt(s,n=20):
    t=words(s,n)
    return '„'+esc(t)+(' …' if len(t.split())<len(tidy(s).split()) else '')+'“'
def blocks(n):
    for c in n.children:
        if not isinstance(c,Node):continue
        if c.tag in ('h1','h2','h3','h4','h5','p','li'):
            if tidy(c.text()):yield c.tag,tidy(c.text()),c
        else:yield from blocks(c)
def sections(n, pattern):
    got=False;items=[];level=3
    for tag,t,el in blocks(n):
        if tag.startswith('h'):
            if re.search(pattern,t,re.I):got=True;level=int(tag[1]);continue
            if got and int(tag[1])<=level:got=False
        if got and tag in ('p','li') and len(t)>5:items.append((tag,t,el))
    return items

PHASE = re.compile(r'^(?:(?:\d+\.?\s*(?:und|bis|[-–])\s*)?\d+\.?\s*(?:Semester|Studienjahr)|Semester\s*\d+)(?:\s*\([^)]*\))?(?:\s*[-–]\s*(?:Pflicht|Wahlpflicht|Pflicht- und Wahlpflicht)module?)?\s*:?$',re.I)
def curriculum(r):
    """Keep published semester/year groupings; do not invent semester allocations."""
    n=document(r);ll=lines(r)
    all_links=links(n,r.get('final_url',r.get('url',BASE)))
    modulemap={tidy(x['label']):x['url'] for x in all_links if '/module/' in x['url']}
    if 'Modulbeschreibungen' in ll:ll=ll[ll.index('Modulbeschreibungen')+1:]
    rows=[];phase=None;kind='Veröffentlichte Module';bucket=[];track='';running_track=''
    def flush():
        nonlocal bucket
        if phase and bucket:rows.append({'phase':phase,'track':running_track,'kind':kind,'modules':unique(bucket),'url':r.get('url','')})
        bucket=[]
    for line in ll:
        t=tidy(line)
        if re.match(r'^Modulhandb.ch|^Module manual|^Kontakt$|^Contact$',t,re.I):flush();break
        if PHASE.match(t):
            flush();phase=t.rstrip(':');kind='Veröffentlichte Module';running_track=track;continue
        if re.match(r'^(?:Schwerpunkt |Vertiefung |Studienrichtung |Jazz [–-] Künstlerisches|Klassik [–-] Künstlerisches|Pop [–-] Künstlerisches|Option Integriertes|Variante \d)',t):
            flush();track=t;phase=None;continue
        if re.match(r'^(?:Pflichtmodule?|Wahlpflichtmodule?|Wahlmodule?|Pflichtunits?|Wahlpflichtunits?|Sondermodul)(?:\s*\([^)]*\))?\s*:?$',t,re.I):
            flush();kind=t.rstrip(':');continue
        if phase and t and t not in ['Vorherige Seite','Nächste Seite','Zum Vergrößern bitte anklicken.']:
            if len(t)<160 and not re.search(r'^(Studienverlaufsplan|Zum Vergrößern|Bitte |Im |Die |Das |Der |Diese |Für |Nach |An der |Es |Hier |Näheres |Weitere |Wir )',t):
                bucket.append(t)
    flush()
    # Avoid pages listing a global catalogue rather than the requested programme.
    return rows,modulemap

def latest_handbook(c):
    candidates=[]
    for x in c.get('handbooks',[]):
        if not cached(x['url']).get('pdf_path'):continue
        u=x['url']
        # Only known linked handbooks, the latest linked order/stand, without global archives.
        if '/Archiv/' in u:continue
        years=[int(y) for y in re.findall(r'(20\d{2})',u)]
        sto=re.search(r'StO(20\d{2})',u,re.I)
        dates=re.findall(r'(20\d{2})[-_](\d{2})[-_](\d{2})',u)
        score=(int(sto.group(1)) if sto else max(years,default=0),max(dates,default=('0','0','0')))
        candidates.append((score,x))
    return sorted(candidates,key=lambda v:v[0],reverse=True)[0][1] if candidates else None

DEGREES={'B.Sc.':'Bachelor of Science','B.A.':'Bachelor of Arts','B.Eng.':'Bachelor of Engineering','M.Sc.':'Master of Science','M.A.':'Master of Arts','M.Eng.':'Master of Engineering','M.Ed.':'Master of Education','MBA':'Master of Business Administration','LL.B.':'Bachelor of Laws','LL.M.':'Master of Laws'}

def describe(c, module_names):
    title=tidy(c['title']);desc=tidy(parse(c['description']).text())
    enriched=ENRICH.get(str(c['uid']),{}).get('profile')
    if enriched:return enriched
    s=f'{title} ist im Studienangebot der Hochschule Osnabrück als {desc[0].lower()+desc[1:]} verzeichnet.'
    if module_names:s+=' Zu den veröffentlichten Lehrthemen zählen '+', '.join(module_names[:7])+'.'
    elif 'Geflügel' in title:s+=' Das Angebot ist als auslaufend markiert; eine aktuelle Aufnahme ist durch den Verzeichniseintrag nicht belegt.'
    elif 'Informatik (B.Sc.)'==title:s+=' Das achtsemestrige Orientierungsmodell führt nach zwei Eingangssemestern zu einer Studienrichtung in Technischer Informatik, Medieninformatik oder Wirtschaftsinformatik.'
    return s

manifest=[];gaps=[]
for c in PROGRAMS:
    title=tidy(c['title']);filename=slug(title)+'.md';c['markdown_file']=filename
    invalid=urlparse(c['url']).path in ('','/')
    home={} if invalid else cached(c['url'])
    app={} if urlparse(c['application_url']).path in ('','/') else cached(c['application_url'])
    docs=[cached(x['url']) for x in c.get('detail_links',[]) if cached(x['url']).get('html')]
    home_n=document(home);ll=lines(home)
    # English microsites carry the substantive metadata for some programmes.
    for d in docs:
        if '/en/' in d.get('url','') and 'design-entrepreneurship' in d.get('url',''):
            ll+=lines(d)
    primary=INDEX if invalid else home.get('final_url',c['url'])
    status='auslaufend; keine aktuelle Erstaufnahme aus dem Verzeichnis ableitbar' if re.search('auslaufend',title,re.I) else 'im offiziellen A–Z-Verzeichnis geführt; Aufnahme semesterabhängig'
    degree=next((abbr for abbr in DEGREES if '('+abbr+')' in title),'')
    duration=field(ll,['Regelstudienzeit','Regelstudienzeit / Gesamtdauer','Standard period of study','Standard period','Duration of study'])
    if not duration:
        mt=re.search(r'\d+\s*Semester',parse(c['description']).text(),re.I);duration=mt.group(0) if mt else 'in den erfassten Quellen nicht eindeutig angegeben'
    studyform=field(ll,['Studienform','Type of study','Type of program','Study mode'])
    labels=c.get('labels',[])
    if not studyform:studyform='; '.join(x for x in labels if x in ['Vollzeit','Dual','Berufsbegleitend / Berufsintegrierend','Weiterbildung','Ausbildungsbegleitend/ Ausbildungsintegrierend','Praxisintegrierend'])
    if 'Vollzeit' in labels and 'vollzeit' not in studyform.lower():studyform+='; Vollzeit laut A–Z-Verzeichnis'
    location=field(ll,['Standort','Studienort','Location','Campus'])
    if not location:
        location='; '.join(x for x in labels if x in ['Osnabrück','Lingen','China'])
        if 'Angewandte Nutztier' in title or 'Angewandte Pflanzenwissenschaften' in title:location='Osnabrück, Campus Haste (Kontakt- und Fakultätszuordnung)'
    begin=field(ll,['Studienbeginn','Beginn','Studiengeginn','Start of study','Start of studies','Start']) or '; '.join(x for x in labels if x in ['Sommersemester','Wintersemester'])
    restriction=field(ll,['Zulassungsbeschränkung','Zulassunungsbeschränkung','Zulassungbeschränkung','Admission restrictions','Admission restriction','Restricted admission'])
    if not restriction:restriction='auf den erfassten Profilseiten nicht eindeutig als Basisdatum angegeben; Bewerbungsseite prüfen'
    rows=[];modmap={}
    for d in docs:
        rr,mm=curriculum(d)
        for row in rr:
            if row not in rows:rows.append(row)
        modmap.update(mm)
    module_names=unique(tidy(m) for row in rows for m in row['modules'] if len(m)<110)
    extra=ENRICH.get(str(c['uid']),{})
    if extra.get('rows'):
        rows=[dict(phase=p,track=tr,kind=k,modules=ms,url=extra['curriculum_source']) for p,tr,k,ms in extra['rows']]
        module_names=unique(tidy(m) for row in rows for m in row['modules'] if len(m)<110)
    if not module_names:module_names=unique(tidy(x['label']) for x in c.get('module_links',[]) if x['label'])
    handbook=latest_handbook(c)
    regulations=[x for x in c.get('regulations',[]) if urlparse(x['url']).netloc.endswith('hs-osnabrueck.de')]
    section_sources=[(tidy(x['label']) or 'Studienverlauf',x['url']) for x in c.get('detail_links',[]) if cached(x['url']).get('status')==200]
    data=[f'---\nid: hsos-studiengang-{c["uid"]}\ninstitution: Hochschule Osnabrück\nstudiengang: {json.dumps(title,ensure_ascii=False)}\nabschluss: {json.dumps(degree,ensure_ascii=False)}\nrecherchestand: {DATE}\nquelle: {primary}\nstatus: {json.dumps(status,ensure_ascii=False)}\n---\n',f'# Hochschule Osnabrück: {title}\n']
    data += ['## Studiengangs-Basisdaten\n',f'Studiengang: **{title}**, Hochschule Osnabrück. Quellenstand: 28.10.2026.\n','| Merkmal | Angabe |\n| --- | --- |',f'| Offizieller Verzeichniseintrag | {esc(title)} |',f'| Abschluss | {esc(DEGREES.get(degree,degree))} ({esc(degree)}) |',f'| Regelstudienzeit | {esc(duration)} |',f'| Campus / Studienort | {esc(location)} |',f'| Studienform | {esc(studyform)} |',f'| Studienbeginn | {esc(begin)} |',f'| Zulassungsbeschränkung laut Profil | {esc(restriction)} |',f'| Angebotsstatus | {esc(status)} |','',f'Quellen: {link("Offizielles Studienprofil",primary)}, {link("A–Z-Verzeichnis",INDEX)}.\n']
    # Document demonstrable conflicts; retain programme-specific metadata with provenance.
    issues=[]
    if 'Agrarsystemtechnologien' in title:issues.append('Die Überschrift der Bewerbungsseite nennt abweichend B.Eng.; A–Z-Verzeichnis und Studienprofil führen B.Sc. Außerdem enthält die Bewerbungsseite einen DoSV-Hinweis, obwohl die zentrale Tabelle für Wintersemester 2026/2027 keine DoSV-Teilnahme nennt. Verfahren vor einer neuen Bewerbung beim Studierendensekretariat prüfen.')
    if 'Wirtschaftsinformatik (B.Sc.), Standort Lingen' in title:issues.append('Das Profil enthält die widersprüchliche Formulierung „Bachelor of Arts (B.Sc.)“. Hier wird der im Studiengangstitel und A–Z-Verzeichnis angegebene Abschluss B.Sc. verwendet.')
    if 'Wirtschaftsingenieurwesen (MBA)' in title:issues.append('Das A–Z-Verzeichnis ordnet das Angebot Lingen zu; das Profil nennt als Standort Osnabrück. Den Präsenzort vor einem Besuch mit der Studiengangskoordination klären.')
    if 'Nachhaltige Dienstleistungs-' in title:issues.append('Das Profil nennt Münster als Standort, das A–Z-Verzeichnis Osnabrück. Das Kooperationsangebot und die konkreten Lehrorte auf der Fachseite beziehungsweise mit der Koordination klären.')
    if invalid:issues.append('Der Verzeichniseintrag enthält keinen nutzbaren Studiengangs-Direktlink. Daher werden keine Inhalte der Hochschulstartseite als Studiengangsinformation übernommen.')
    if issues:data+=['### Quellenhinweise zu diesem Studiengang\n']+['- '+i for i in issues]+['']
    data+=['## Profil & Inhalte\n',describe(c,module_names)+'\n']
    if module_names:data+=['Die Modulnamen dienen der fachlichen Orientierung; Pflicht- und Wahlbereiche sowie Varianten werden im folgenden Abschnitt getrennt ausgewiesen.\n']
    if section_sources:data += ['Quellen: '+', '.join(link(a,b) for a,b in section_sources[:3])+'.\n']
    else:data += [f'Quelle: {link("Studiengang im offiziellen Verzeichnis",primary)}.\n']
    data+=['## Modulübersicht & Curricula\n',f'Curriculum von **{title}** an der Hochschule Osnabrück. Semester- und Studienjahresangaben werden in der Gruppierung der Originalquelle wiedergegeben. Ein Studienjahr wird ohne eindeutige Quelle nicht auf einzelne Semester aufgeteilt.\n']
    if rows:
        data+=['| Semester / Studienjahr | Variante / Schwerpunkt | Modulart | Veröffentlichte Module |\n| --- | --- | --- | --- |']
        for row in rows:
            mods=row['modules']
            # Full named mandatory modules; an explicit selection in long elective catalogues.
            elective='wahl' in row['kind'].lower()
            selected=mods[:14] if elective else mods
            textmods='; '.join(link(m,modmap[m]) if m in modmap else esc(m) for m in selected)
            if len(selected)<len(mods):textmods+=f'; weitere {len(mods)-len(selected)} Optionen im verlinkten Studienverlauf (Auswahl dargestellt)'
            data.append(f'| {esc(row["phase"])} | {esc(row["track"]) or "Grundverlauf / siehe Quelle"} | {esc(row["kind"])} | {textmods} |')
        data+=['','„Veröffentlichte Module“ bedeutet, dass die Originalseite an dieser Stelle keine eindeutige Pflicht-/Wahlpflichtkennzeichnung enthält. Anzahl und Kombination der tatsächlich zu belegenden Wahlmodule richten sich nach der passenden Studienordnung.\n']
        if extra.get('curriculum_source'):data += [f'Zusätzlich ausgewertete Originalquelle: {link("Curriculum / Studienverlaufsquelle",extra["curriculum_source"])}.\n']
        if extra.get('curriculum_note'):data += [extra['curriculum_note']+'\n']
    else:
        data+=['Eine belastbare semesterweise HTML-Modulliste ist in den erfassten Quellen für dieses Angebot nicht vorhanden. Die folgenden veröffentlichten Studienverlaufs- und Modulunterlagen enthalten die fachliche Einordnung. Es werden keine Semesterzuordnungen erfunden.\n']
        gaps.append({'id':c['uid'],'studiengang':title,'punkt':'Keine unmittelbar auslesbare semesterweise HTML-Modulliste','datei':filename})
    if section_sources:data+=['Studienverlaufsquellen: '+', '.join(link(a,b) for a,b in section_sources[:4])+'.\n']
    if handbook:data += [f'Modulhandbuch: {link(handbook["label"] or "Offizielles Modulhandbuch (PDF)",handbook["url"])}. Der Link wurde erfolgreich abgerufen. Aus den verlinkten Fassungen wurde ein zuletzt datierter Stand gewählt; Gültigkeit für den eigenen Einschreibejahrgang prüfen.\n']
    else:
        texts=' '.join(' '.join(lines(d)) for d in docs)
        if 'betreuung-ids@hs-osnabrueck.de' in texts:
            data+=['Modulhandbuch / Jahresplanung: Die Hochschule nennt für dieses duale Angebot die Anforderung beim Institut für Duale Studiengänge unter **betreuung-ids@hs-osnabrueck.de**. Ein öffentlich abrufbarer Modulhandbuch-PDF-Link ist in den ausgewerteten Studiengangsquellen nicht belegt.\n']
        else:data+=['Modulhandbuch: Ein eindeutig passender, öffentlich abrufbarer PDF-Direktlink ist in den erfassten Studiengangsquellen nicht belegt. Die Studienverlaufsquelle und die Studiengangskoordination sind die nächsten Anlaufstellen.\n']
        gaps.append({'id':c['uid'],'studiengang':title,'punkt':'Kein eindeutig zugeordnetes öffentliches Modulhandbuch-PDF','datei':filename})
    if regulations:data+=['Prüfungs-/Studien-/Zulassungsordnungen: '+', '.join(link(x['label'] or 'Ordnung',x['url']) for x in regulations[:4])+'.\n']
    else:data += [f'Prüfungs- und Studienordnungen: {link("Amtliche Ordnungen der Hochschule",BASE+"/wir/organisation/amtsblatt/")}; Zuordnung zum Studiengang und zur eigenen Kohorte prüfen.\n']
    data+=['### Schlüsselmodule: Inhalte und Umfang\n']
    usable=[x for x in c.get('key_modules',[]) if cached(x['url']).get('text')]
    for x in c.get('module_links',[]):
        if len(usable)>=3:break
        if cached(x['url']).get('text') and x not in usable:usable.append(x)
    for x in usable[:3]:
        r=cached(x['url']);ml=lines(r)
        meta=[]
        for label, keys in [('Modulkennung',['Modulkennung','Modul-Code']),('ECTS',['ECTS-Leistungspunkte und Benotung','Leistungspunkte']),('Sprache',['Unterrichtssprache','Lehrsprache']),('Dauer',['Dauer des Moduls']),('Angebot',['Häufigkeit des Angebots des Moduls'])]:
            v=field(ml,keys)
            if v:meta.append(f'{label}: {esc(v)}')
        contents=''
        for key in ['Lehr-Lerninhalte','Lehrinhalte']:
            if key in ml:
                start=ml.index(key)+1;end=next((i for i in range(start,len(ml)) if ml[i] in ['Gesamtarbeitsaufwand','Arbeitsaufwand, Lehr- und Lernformen','Lehr- und Lernformen','Lernergebnisse','Lernergebnisse / Kompetenzziele']),min(start+16,len(ml)))
                contents=' '.join(ml[start:end]);break
        data += [f'#### {tidy(x["label"])}\n','; '.join(meta)+'.\n' if meta else 'Modul ist in der offiziellen Studienverlaufsquelle verlinkt.\n']
        if contents:data += ['Inhaltsauszug aus der Modulbeschreibung: '+excerpt(contents,23)+'.\n']
        data += [f'Vollständige Lehrinhalte, Kompetenzziele und Prüfungsformen: {link("offizielle Modulbeschreibung",x["url"])}.\n']
    if not usable:
        data += ['Detaillierte Einzelmodulbeschreibungen werden über das oben verlinkte Modulhandbuch beziehungsweise die angegebene Fachberatung nachgewiesen. Ungeprüfte Lernziele, ECTS-Werte und Prüfungsformen werden hier nicht ergänzt.\n']
        gaps.append({'id':c['uid'],'studiengang':title,'punkt':'Einzelmoduldetails nur über PDF oder Anfrage; keine auswertbaren HTML-Modulbeschreibungen','datei':filename})
    data+=['## Zulassung & Fristen\n',f'Zulassungsinformation für **{title}**, Hochschule Osnabrück. Angebotsstatus: **{status}**. Studienbeginn laut Profil/Verzeichnis: **{esc(begin)}**.\n']
    al=lines(app);at=' '.join(al)
    admission=[]
    # Extract facts with restrictive predicates; a missing phrase never becomes a negative requirement.
    language=[]
    for level in ['DSH 2/C1','DSH 1/B2','DSH-2','DSH-1','B2','C1','C2']:
        if re.search(r'(?<!\w)'+re.escape(level)+r'(?!\w)',at):language.append(level)
    if language:admission.append(('Sprachnachweise in der Bewerbungsquelle',', '.join(unique(language))+'; Sprache, Testalternativen und Ausnahmen auf der Bewerbungsseite prüfen'))
    if re.search(r'(?:kein|nicht erforderlich)[^.!?]{0,25}Vorpraktikum|Vorpraktikum ist nicht erforderlich|Vorpraktikum wird (?:zwar )?nicht gefordert',at,re.I):admission.append(('Vorpraktikum','laut Bewerbungsseite nicht erforderlich; eine Empfehlung kann trotzdem bestehen'))
    elif re.search(r'Vorpraktik|Vorpraktisch',at,re.I):admission.append(('Vorpraktikum','wird in der Bewerbungsquelle behandelt; konkrete Dauer, Tätigkeiten und Nachreichregel dort prüfen'))
    if re.search(r'Studienvertrag',at,re.I):admission.append(('Dualer Vertrag','Studienvertrag wird vorausgesetzt; Anerkennung des Praxis-/Ausbildungsbetriebs und Einreichungsweg beachten'))
    if re.search(r'Bitte registrier[^.]*nicht vorab',at,re.I):admission.append(('Reihenfolge im dualen Verfahren','zuerst Vertrags-/Unterlagenprüfung; Portalregistrierung erst nach Aufforderung'))
    if re.search(r'Eignungspr.fung|Aufnahmepr.fung|Eignungsfeststell',at,re.I):admission.append(('Eignungsverfahren','eigenes Verfahren in der Bewerbungsquelle genannt; Anmeldung, Unterlagen und Prüfungstermine getrennt prüfen'))
    if re.search(r'Berufserfahrung|Berufstätigkeit|Berufspraxis',at,re.I):admission.append(('Berufliche Vorbildung','Bewerbungsquelle enthält Anforderungen oder Auswahlkriterien zur Berufspraxis; erforderliche Dauer und Relevanz im Original prüfen'))
    if degree in ['M.Sc.','M.A.','M.Eng.','M.Ed.','MBA','LL.M.']:admission.append(('Masterzugang','passender erster Hochschulabschluss; fachliche Anforderungen, Noten-/ECTS-Regeln und Zusatznachweise aus der konkreten Zulassungsordnung'))
    else:admission.append(('Hochschulzugang','anerkannte Hochschulzugangsberechtigung; zusätzliche studiengangsbezogene Nachweise gesondert prüfen'))
    if re.search(r'Entsend|Einstellungsbehörde',at,re.I):admission.append(('Behördliches Verfahren','Entsendung beziehungsweise Verfahren der Einstellungsbehörde beachten'))
    # Numerical and explicitly named requirements remain tied to the original application page.
    numerical=unique(m.group(0) for m in re.finditer(r'(?:mindestens|wenigstens|minimum of|min\.)\s+\d+(?:[.,]\d+)?\s*(?:ECTS(?:-Punkte)?|Leistungspunkte|LP|credit points|Wochen|Monate|Jahre|Semester|years|months)',at,re.I))
    if numerical:admission.append(('Quantifizierte Anforderungen in der Bewerbungsquelle','; '.join(numerical[:8])+'; Zuordnung zum erforderlichen Nachweis im Original prüfen'))
    for label,value in extra.get('admission',[]):admission.append((label,value))
    data+=['| Punkt | Erfasste Information |\n| --- | --- |']+[f'| {esc(k)} | {esc(v)} |' for k,v in admission]+['']
    evidence=[]
    for text in al:
        if len(text)<35 or len(text)>2000:continue
        if re.search(r'Zulassungsfrei bedeutet|Zulassungsbeschränkt bedeutet|Online-Bewerbung|Wie funktioniert|Bewerbungszeitraum|Bewerbungsportal|angaben vollständig',text,re.I):continue
        score=sum(bool(re.search(p,text,re.I))*w for p,w in [(r'Vorpraktik|Ausbildungsvertrag|Studienvertrag|Entsendung',5),(r'Zugang|Zulassung|Abschluss|Hochschulzugangsberechtigung|Berufsausbildung',2),(r'mindest|mind\.|minimum|at least|\b[ABC][12]\b|DSH|\d+\s*(ECTS|Monate|Wochen|Jahre|%)',5)])
        if score>=5:evidence.append((score,text))
    if evidence and app.get('final_url')!=primary:
        best=max(evidence,key=lambda x:x[0])[1]
        data+=['Konkreter Nachweishinweis aus der Bewerbungsquelle (Auszug): '+excerpt(best,23)+'. Die verlinkte Quelle enthält den vollständigen Satz und mögliche Ausnahmen.\n']
    # Keep the relevant factual dates visible, always with year/status context.
    datelines=[]
    for i,t in enumerate(al):
        if re.search(r'(?:\d{1,2}\.\d{1,2}\.20\d{2}|\d{1,2}\.\s*(?:Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)|(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d)',t,re.I):
            if re.search(r'Sprechzeit|Orientierungswoche|Uhr|deutschlandstipendium',t,re.I):continue
            if len(t)<300:datelines.append(t)
    data += ['### Fristbezug und Bewerbungsweg\n']
    data += [f'Die regulären Hochschulfristen und die früheren Fristen über uni-assist stehen in {link("Bewerbung und Fristen", "../02_bewerbung_und_fristen.md")}. Die konkrete Bewerbungsseite kann abweichende Termine nennen; diese gehen der allgemeinen Regel vor. Daten mit 2025 oder Wintersemester 2026/2027 sind am Recherchestichtag keine kommenden Fristen.\n']
    if datelines:
        data+=['Auf der Bewerbungsseite gefundene Terminangaben (mit dem dortigen Semester-/Jahresbezug lesen):\n']+['- '+esc(t) for t in unique(datelines)[:7]]+['']
    if re.search('auslaufend',title,re.I):data+=['**Auslaufendes Angebot:** Aus alten Profil- oder Bewerbungsangaben wird keine aktuelle Bewerbungsmöglichkeit abgeleitet. Aufnahme direkt bei der Hochschule klären.\n']
    if not invalid and app.get('status')==200:data += [f'Zugangsvoraussetzungen, geforderte Unterlagen und konkrete Fristen: {link("Bewerbung für diesen Studiengang",app.get("final_url",c["application_url"]))}.\n']
    else:data += [f'Ein nutzbarer studiengangsspezifischer Bewerbungslink ist nicht nachgewiesen. Einstieg: {link("Hochschul-Bewerbungsinformationen",APPLY)}.\n']
    data += [f'Historische Auswahlgrenzen: {link("Offizielle NC-Tabellen",NC)} und {link("NC-Dokument dieser Wissensbasis","../06_nc_auswahlgrenzen.md")}. Ein vergangener NC ist keine verbindliche Zugangsvorgabe für ein zukünftiges Semester.\n']
    data+=['## Berufsperspektiven\n']
    careers=sections(home_n,r'^(?:Berufsperspektiven|Berufsfeld|Berufsaussicht|Career prospects|Professional Qualifications|WAS KANN ICH NACH)')
    for d in docs:
        if not careers:careers=sections(document(d),r'Berufsperspektiven|Berufsfeld|Berufsaussicht|Career prospects')
    bul=[t for tag,t,el in careers if tag=='li' and len(t)<250]
    if extra.get('careers'):
        data += [f'Für **{title}** nennt die Hochschule folgende fachlichen Tätigkeitsfelder beziehungsweise Anschlusswege:\n']+['- '+esc(t) for t in extra['careers']]+['']
    elif bul:
        data += [f'Die offizielle Seite von **{title}** nennt unter anderem folgende Tätigkeitsfelder beziehungsweise Anschlusswege:\n']+['- '+esc(t) for t in unique(bul)[:10]]+['']
    elif careers:
        candidates=[s for _,t,_ in careers for s in re.split(r'(?<=[.!?])\s+',t) if len(s)>30]
        def career_score(t):
            return sum(len(re.findall(p,t,re.I)) for p in ['Tätigkeit','Unternehmen','Industrie','Forschung','Entwicklung','Berufsfeld','arbeiten','Einrichtung','Schulen','Beratung','Management','Produktion','Praxis','Banken','Versicherung','Ingenieur','Software','öffentlichen'])
        best=max(candidates,key=career_score) if candidates else careers[0][1]
        data += ['Orientierung aus dem veröffentlichten Berufsprofil: '+excerpt(best,20)+'. Weitere Tätigkeitsfelder und Voraussetzungen erläutert die verlinkte Fachseite.\n']
    else:
        data += ['Eine eigenständige, eindeutig zugeordnete Berufsfeldliste konnte aus der erfassten Profilseite nicht belastbar extrahiert werden. Fachliche Einsatzgebiete und gegebenenfalls anschließende Master-, Lehramts- oder Anerkennungsschritte mit der Studiengangsfachberatung anhand des Studienprofils klären.\n']
        gaps.append({'id':c['uid'],'studiengang':title,'punkt':'Berufsfeldliste nicht strukturiert extrahierbar','datei':filename})
    data += [f'Quelle und Kontakt zur Fachberatung: {link("Studienprofil",primary)}.\n']
    data+=['## Direktlinks & Quellen\n',f'- {link("Offizielle Studiengangsseite" if not invalid else "Offizieller Verzeichniseintrag (kein nutzbarer Einzelprofil-Link)",primary)}']
    if not invalid and app.get('status')==200:data += [f'- {link("Studiengangsspezifische Bewerbung",app.get("final_url",c["application_url"]))}']
    data += ['- '+link(a,b) for a,b in section_sources[:5]]
    if handbook:data += ['- '+link('Modulhandbuch (direktes PDF)',handbook['url'])]
    data += ['- '+link(x['label'] or 'Ordnung',x['url']) for x in regulations[:4]]
    data += [f'- {link("Zuständige Sachbearbeitung: Studierendensekretariat",BASE+"/wir/organisation/organisationseinheiten/studierendensekretariat/")}',f'- {link("Online-Bewerbungsportal","https://studienorganisation.hs-osnabrueck.de/")}',f'- {link("A–Z-Verzeichnis als Abdeckungsreferenz",INDEX)}','',f'Abrufdatum der erfassten Quellen: **28.10.2026**. Zusammenstellung für Studienorientierung und RAG; Quellen und Studienordnung für den betreffenden Einschreibejahrgang entscheiden bei Abweichungen.\n']
    (OUT/filename).write_text('\n'.join(data))
    manifest.append({'id':c['uid'],'studiengang':title,'datei':'04_studiengaenge/'+filename,'status':status,'abschluss':degree,'standort':location,'regelstudienzeit':duration,'studienbeginn':begin,'quelle':primary,'bewerbung':app.get('final_url',c['application_url']) if not invalid else None,'modulhandbuch':handbook['url'] if handbook else None,'curriculum_zeilen':len(rows),'schluesselmodule':len(usable[:3]),'quellenkonflikte':issues,'recherchestand':DATE})

(ROOT/'programs.json').write_text(json.dumps(PROGRAMS,ensure_ascii=False,indent=2))
(DATA/'studiengaenge_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
(ROOT/'luecken.json').write_text(json.dumps(gaps,ensure_ascii=False,indent=2))
index=['# Hochschule Osnabrück: Studiengänge A–Z\n',f'Recherchestand: **28.10.2026**. Eigene Markdown-Datei für **{len(manifest)} von 128** Einträgen des offiziellen A–Z-Verzeichnisses. Studienrichtungen, Standorte, Studienmodelle und auslaufende Angebote bleiben getrennt auffindbar.\n',f'Quelle: {link("Offizielles Studienverzeichnis",INDEX)}.\n','| Studiengang / eigene Markdown-Datei | Abschluss | Standort laut Profil | Regelstudienzeit | Status |\n| --- | --- | --- | --- | --- |']
for r in manifest:index.append(f'| {link(r["studiengang"],Path(r["datei"]).name)} | {esc(r["abschluss"])} | {esc(r["standort"])} | {esc(r["regelstudienzeit"])} | {"auslaufend" if "auslaufend" in r["status"] else "im Verzeichnis"} |')
(OUT/'00_index.md').write_text('\n'.join(index)+'\n')
print(json.dumps({'studiengangsdateien':len(manifest),'curriculum_zeilen':sum(x['curriculum_zeilen'] for x in manifest),'mit_curriculum':sum(bool(x['curriculum_zeilen']) for x in manifest),'mit_modulhandbuch':sum(bool(x['modulhandbuch']) for x in manifest),'mit_schluesselmodulen':sum(bool(x['schluesselmodule']) for x in manifest),'luecken':len(gaps)},ensure_ascii=False))
