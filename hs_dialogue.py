"""Gesprächsführung vor der Wissenssuche; Studiengänge kommen nur aus Nutzerangaben.

Begrüßungen und Rückfragen benötigen keine Dokumentensuche. Ein Suchtreffer oder
eine frühere Modellbehauptung wird niemals zum gewählten Studiengang erklärt.
"""
from dataclasses import dataclass, field
import re
import unicodedata


def normalized(text):
    text = unicodedata.normalize('NFKD', str(text).casefold().replace('ß', 'ss'))
    text = ''.join(c for c in text if not unicodedata.combining(c))
    return ' '.join(re.sub(r'[^a-z0-9]+', ' ', text).split())


def programme_catalog(chunks, include_archived=False):
    result = {}
    for chunk in chunks:
        name = chunk.get('studiengang')
        if name and (include_archived or 'auslaufend' not in (chunk.get('status') or '').casefold()):
            result[name] = {'name': name, 'degree': chunk.get('abschluss') or '',
                            'campus': chunk.get('campus') or ''}
    return list(result.values())


def aliases(name):
    core = re.split(r'\s*\(', name, maxsplit=1)[0].strip()
    variants = {normalized(core), normalized(name)}
    # Qualifying names such as "Technische Informatik" must outrank "Informatik".
    parts = re.split(r'\s+[–—-]\s+', core)
    if len(parts) > 1:
        variants.add(normalized(parts[-1]))
    if ':' in core:
        variants.add(normalized(core.split(':')[0]))
    key = normalized(core)
    if key.startswith('betriebswirtschaft und management'):
        variants.update({'bwl', 'betriebswirtschaft'})
    if key == 'soziale arbeit':
        variants.add('sozialarbeit')
    if key == 'allgemeiner maschinenbau':
        variants.add('maschinenbau')
    if key.startswith('ets '):
        variants.add('engineering technischer systeme ' + key[4:])
    return {v for v in variants if v}


def matching_programmes(text, catalog, all_matches=False):
    text = ' ' + normalized(text) + ' '
    scores = {}
    for item in catalog:
        matches = [len(alias) for alias in aliases(item['name']) if ' ' + alias + ' ' in text]
        if matches:
            scores[item['name']] = max(matches)
    if not scores:
        return []
    best = max(scores.values())
    return [item['name'] for item in catalog if item['name'] in scores and
            (all_matches or scores[item['name']] == best)]


def qualification(text):
    value = normalized(text)
    if re.search(r'\b(bachelor|b sc|bsc|b a|b eng|ll b)\b', value):
        return 'bachelor'
    if re.search(r'\b(master|m sc|msc|m a|m eng|m ed|mba|ll m)\b', value):
        return 'master'
    return None


def place(text):
    value = normalized(text)
    for label in ['Lingen', 'Osnabrück', 'Westerberg', 'Haste', 'Caprivi', 'China']:
        if re.search(r'\b' + normalized(label) + r'\b', value):
            return label
    return None


@dataclass
class TurnPlan:
    kind: str
    state: dict
    answer: str = ''
    query: str = ''
    suggestions: list[str] = field(default_factory=list)
    scope: dict = field(default_factory=dict)


TOPICS = ['Studiengänge entdecken', 'Bewerbung und Fristen', 'Campus kennenlernen']
INTERESTS = ['Technik und Informatik', 'Gesundheit und Soziales',
             'Wirtschaft und Management', 'Natur und Ernährung']
INTEREST_QUESTIONS = {
    'technik und informatik': ('Was reizt dich mehr: Software entwickeln, technische Dinge bauen oder beides verbinden?',
                             ['Software entwickeln', 'Technische Dinge bauen', 'Software und Technik verbinden']),
    'gesundheit und soziales': ('Was könntest du dir eher vorstellen: Menschen direkt unterstützen, therapeutisch arbeiten oder Abläufe im Gesundheitswesen gestalten?',
                               ['Menschen direkt unterstützen', 'Therapeutisch arbeiten', 'Gesundheitsversorgung organisieren']),
    'wirtschaft und management': ('Was interessiert dich besonders: mit Zahlen arbeiten, Unternehmen gestalten oder international zusammenarbeiten?',
                                 ['Mit Zahlen arbeiten', 'Unternehmen gestalten', 'International zusammenarbeiten']),
    'natur und ernahrung': ('Was spricht dich am meisten an: Umwelt und Landschaft, Ernährung oder Landwirtschaft?',
                           ['Umwelt und Landschaft', 'Ernährung und Lebensmittel', 'Landwirtschaft']),
}


def plan_turn(question, catalog, *, state=None, history=None, programme=None,
              campus=None, degree=None):
    question = question.strip()
    if not question or len(question) > 6000:
        raise ValueError('Bitte eine Frage mit 1 bis 6000 Zeichen eingeben.')
    known = {p['name']: p for p in catalog}
    old = state or {}
    current = {
        'programme': old.get('programme') if old.get('programme') in known else None,
        'candidates': [n for n in old.get('candidates', []) if n in known],
        'pending_question': str(old.get('pending_question') or '')[:2000],
        'interest': str(old.get('interest') or '')[:300],
        'comparison': [n for n in old.get('comparison', []) if n in known][:6],
    }
    if programme in known:
        current.update(programme=programme, candidates=[], pending_question='', comparison=[])
    text = normalized(question)
    if re.fullmatch(r'(hallo|hi|hey|moin|servus|guten tag|guten morgen|guten abend)( zusammen| nochmal| da)?', text):
        return TurnPlan('greeting', current,
                        'Hallo! Schön, dass du da bist. Hast du schon einen Studiengang im Blick '
                        'oder möchtest du erst einmal herausfinden, was zu dir passt?', suggestions=TOPICS)
    if re.fullmatch(r'(danke|dankeschon|vielen dank|super danke|danke dir|alles klar danke|perfekt danke|ok danke)( sehr)?', text):
        return TurnPlan('smalltalk', current, 'Gerne! Wenn du noch etwas wissen möchtest, bin ich für dich da.',
                        suggestions=followups(current['programme']))
    if re.fullmatch(r'(tschuss|tschau|ciao|auf wiedersehen|bis bald)', text):
        return TurnPlan('smalltalk', current, 'Mach’s gut und viel Erfolg bei deiner Studienwahl!')
    if re.fullmatch(r'(wie geht es dir|wie gehts dir|wie gehts|wer bist du|wie heisst du|was kannst du)', text):
        return TurnPlan('smalltalk', current,
                        'Ich bin dein digitaler Studienbegleiter für die Hochschule Osnabrück. '
                        'Wir können gemeinsam Studiengänge erkunden oder Fragen zur Bewerbung klären. '
                        'Was beschäftigt dich gerade?', suggestions=TOPICS)
    if text in {'studiengange entdecken', 'ich weiss es noch nicht', 'ich weiss nicht',
                'ich habe noch keinen studiengang', 'ich brauche orientierung', 'kannst du mir helfen'}:
        current.update(programme=None, candidates=[], pending_question='', comparison=[])
        return TurnPlan('orientation', current,
                        'Dann schauen wir gemeinsam, was zu dir passt. Welche Themen machen dir Spaß – '
                        'zum Beispiel in der Schule, bei der Arbeit oder in deiner Freizeit?', suggestions=INTERESTS)

    if text in INTEREST_QUESTIONS:
        reply, choices = INTEREST_QUESTIONS[text]
        current.update(programme=None, candidates=[], pending_question='', interest=question, comparison=[])
        return TurnPlan('orientation', current, reply, suggestions=choices)

    mentioned = matching_programmes(question, catalog, all_matches=True)
    if len(mentioned) > 1 and re.search(r'\b(unterschied|vergleichen|vergleich|zwischen)\b', text):
        current.update(programme=None, candidates=[], pending_question='', comparison=mentioned[:6])
        return TurnPlan('knowledge', current,
                        query=question, suggestions=['Welche Inhalte unterscheiden sich?', 'Welches passt zu meinen Interessen?'],
                        scope={'programme': None, 'campus': campus, 'degree': degree})

    explicit = matching_programmes(question, catalog)
    if current['comparison'] and not explicit:
        return TurnPlan('knowledge', current,
                        query='Vergleich: ' + ' und '.join(current['comparison']) + '\n' + question,
                        suggestions=['Welche Inhalte unterscheiden sich?', 'Welches passt zu meinen Interessen?'],
                        scope={'programme': None, 'campus': campus, 'degree': degree})
    selected_place = place(question) or campus
    selected_degree = qualification(question)
    if not selected_degree and degree:
        selected_degree = 'bachelor' if degree.startswith(('B.', 'LL.B')) else 'master'

    # Recover only an unambiguous USER choice, never a programme invented by the assistant.
    if not explicit and not current['programme'] and not current['candidates']:
        for message in reversed(history or []):
            if message.get('role') != 'user':
                continue
            previous = matching_programmes(message.get('content', ''), catalog)
            if previous:
                current['candidates'] = previous
                break
    candidates = explicit or current['candidates']
    if not candidates and current['programme']:
        if selected_degree or selected_place:
            base = current['programme'].split('(')[0].strip()
            candidates = matching_programmes(base, catalog)
        else:
            candidates = [current['programme']]
    before_filter = list(candidates)
    if selected_place:
        candidates = [n for n in candidates if normalized(selected_place) in normalized(known[n]['campus'])]
    if selected_degree:
        candidates = [n for n in candidates if (
            known[n]['degree'].startswith(('B.', 'LL.B')) if selected_degree == 'bachelor'
            else known[n]['degree'].startswith(('M.', 'MBA', 'LL.M')))]
    if degree:
        candidates = [n for n in candidates if known[n]['degree'] == degree]

    if len(candidates) > 1:
        current.update(programme=None, candidates=candidates,
                       pending_question=current['pending_question'] or question)
        degrees = {known[n]['degree'] for n in candidates}
        if any(d.startswith(('B.', 'LL.B')) for d in degrees) and any(d.startswith(('M.', 'MBA', 'LL.M')) for d in degrees):
            clarification = 'Meinst du einen Bachelor oder einen Master? Es gibt dazu mehrere Angebote.'
        elif len({known[n]['campus'] for n in candidates}) > 1:
            clarification = 'Welches Angebot meinst du? Die Standorte und Studienformen unterscheiden sich.'
        else:
            clarification = 'Dazu gibt es mehrere Studienangebote. Welches davon interessiert dich?'
        return TurnPlan('clarification', current, clarification, suggestions=candidates[:6])
    if before_filter and not candidates:
        current.update(programme=None, candidates=before_filter,
                       pending_question=current['pending_question'] or question)
        return TurnPlan('clarification', current,
                        'Die Angaben zu Studiengang, Abschluss und Standort passen noch nicht eindeutig zusammen. '
                        'Welches dieser Angebote meinst du?', suggestions=before_filter[:6])

    resolved = candidates[0] if candidates else None
    if resolved:
        current.update(programme=resolved, candidates=[], comparison=[])
    specifics = re.search(r'semester|studienzeit|wie lange|regelstudien|modul|studieninhalt|vorpraktik|eignungspruf|\bnc\b|zulassungsvoraus|zugangsvoraus|berufsperspektiv|welche berufe', text)
    general = re.search(r'was (ist|bedeutet)|allgemein|unterschied|ein semester|studiengange|studiengangsangebot', text)
    if specifics and not general and not resolved:
        current.update(candidates=[], pending_question=question)
        return TurnPlan('clarification', current,
                        'Für welchen Studiengang möchtest du das wissen? '
                        'Dann kann ich dir die passende Auskunft geben.',
                        suggestions=['Informatik', 'Soziale Arbeit', 'Betriebswirtschaft und Management'])

    pending = current.pop('pending_question', '')
    if re.search(r'\b(wie|wann|welche|welcher|welches|was|wo|kann|muss|brauche)\b', text):
        pending = ''
    current['pending_question'] = ''
    query = question
    if resolved:
        query = f'{resolved}\n{pending}\n{question}'.strip()
    elif text == 'bewerbung und fristen':
        query = 'Wie bewerbe ich mich an der Hochschule Osnabrück und welche Bewerbungsfristen gibt es?'
    elif text == 'campus kennenlernen':
        query = 'Welche Campus-Standorte hat die Hochschule Osnabrück und wie kann ich sie besuchen?'
    if current['interest'] and not resolved:
        query = f"Interesse: {current['interest']}\n{query}"
    return TurnPlan('knowledge', current, query=query[:6000], suggestions=followups(resolved),
                    scope={'programme': resolved, 'campus': selected_place, 'degree': degree})


def followups(programme):
    if programme:
        return ['Welche Inhalte erwarten mich?', 'Wie bewerbe ich mich?', 'Welche Berufe sind danach möglich?']
    return TOPICS
