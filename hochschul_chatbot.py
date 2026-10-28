"""Start: poetry run streamlit run hochschul_chatbot.py"""
from pathlib import Path
from urllib.parse import urlparse
import streamlit as st

from hs_dialogue import TOPICS
from hs_index_bundle import ensure_index
from hs_rag import (VectorIndex, answer_question, database_path, friendly_error,
                    load_environment)
from hs_voice import synthesize_reply, transcribe_recording

load_environment(secrets=st.secrets)
st.set_page_config(page_title='Dein Studienbegleiter · Hochschule Osnabrück', page_icon='🎓')
st.caption('DEIN STUDIENBEGLEITER · HOCHSCHULE OSNABRÜCK')
st.title('Finde deinen Studienweg.')
st.caption('Erzähl, was dich interessiert. Wir schauen gemeinsam, was zu dir passt.')
WELCOME = ('Hallo! Ich helfe dir, die Hochschule und ihre Studiengänge kennenzulernen. '
           'Hast du schon einen Studiengang im Blick oder möchtest du dich erst einmal umschauen?')


@st.cache_resource
def load_index(path: str, modified: int, dialogue_version: int):
    return VectorIndex(Path(path))


def queue_question(text):
    st.session_state.pending_message = text


def reset_conversation():
    st.session_state.messages = [{'role': 'assistant', 'content': WELCOME, 'suggestions': TOPICS}]
    st.session_state.dialogue_state = {}
    st.session_state.pop('pending_message', None)
    st.session_state.pop('play_audio', None)


def show_sources(sources):
    if not sources:
        return
    with st.expander('Zum Nachlesen: Quellen'):
        for source in sources:
            st.markdown(f"**[{source['number']}] {source['title']}** — {source['heading']}")
            st.caption(f"Quellenstand: {source.get('retrieved_at') or 'unbekannt'}")
            for url in list(dict.fromkeys(source['urls']))[:5]:
                label = urlparse(url).netloc.removeprefix('www.')
                st.markdown(f'[{label} · Originalseite öffnen]({url})')


db = database_path()
try:
    status = ensure_index(db)
    if not status['ready']:
        st.info('Die Studienberatung ist gerade nicht verfügbar. Bitte versuche es später erneut.')
        st.stop()
    index = load_index(str(db), db.stat().st_mtime_ns, 2)
except Exception as exc:
    st.error(friendly_error(exc))
    st.stop()
if status['source_changed']:
    st.warning('Die Informationen wurden inzwischen bearbeitet. Die Antworten verwenden noch den gespeicherten Stand.')
if st.session_state.get('dialogue_version') != 2:
    reset_conversation()
    st.session_state.dialogue_version = 2

with st.sidebar:
    st.subheader('Dein Besuch')
    auto_voice = st.toggle('Antworten vorlesen', value=False,
                           help='Bei einer gesprochenen Frage wird die Antwort auch vorgelesen.')
    st.caption('Du kannst unten per Mikrofon fragen. Die vorgelesenen Antworten verwenden eine KI-Stimme.')
    with st.expander('Studieninteresse eingrenzen'):
        campus = st.selectbox('Studienort', ['Alle', 'Osnabrück', 'Lingen', 'Haste', 'Westerberg', 'Caprivi', 'China'])
        degrees = sorted({c['abschluss'] for c in index.chunks if c.get('abschluss')})
        degree = st.selectbox('Abschluss', ['Alle'] + degrees)
        programmes = sorted({c['studiengang'] for c in index.chunks if c.get('studiengang')
                             and (campus == 'Alle' or campus.casefold() in (c.get('campus') or '').casefold())
                             and (degree == 'Alle' or degree == c.get('abschluss'))
                             and 'auslaufend' not in (c.get('status') or '').casefold()})
        programme = st.selectbox('Studiengang', ['Alle'] + programmes)
    if st.button('Neues Gespräch', use_container_width=True):
        reset_conversation()
        st.rerun()

active = st.session_state.dialogue_state.get('programme')
if active:
    st.caption(f'Im Gespräch: {active}')
play_audio = st.session_state.pop('play_audio', None)
for number, message in enumerate(st.session_state.messages):
    with st.chat_message(message['role'], avatar='🎓' if message['role'] == 'assistant' else None):
        st.markdown(message['content'])
        show_sources(message.get('sources', []))
        if message.get('voice_error'):
            st.caption(message['voice_error'])
        if message['role'] == 'assistant':
            if message.get('audio'):
                st.audio(message['audio'], format='audio/wav', autoplay=play_audio == number)
            elif st.button('Antwort anhören', icon='🔊', key=f'listen_{number}'):
                try:
                    with st.spinner('Ich lese dir die Antwort vor …'):
                        message['audio'] = synthesize_reply(message['content'])
                    st.audio(message['audio'], format='audio/wav', autoplay=True)
                except Exception as exc:
                    st.info(friendly_error(exc))

last = st.session_state.messages[-1] if st.session_state.messages else {}
suggestions = last.get('suggestions', []) if last.get('role') == 'assistant' else []
if suggestions:
    columns = st.columns(2 if len(suggestions) > 3 else len(suggestions))
    for i, suggestion in enumerate(suggestions):
        columns[i % len(columns)].button(suggestion, key=f'suggest_{len(st.session_state.messages)}_{i}',
                                        use_container_width=True, on_click=queue_question, args=(suggestion,))

submission = st.chat_input('Schreib mir oder frag per Mikrofon …', accept_audio=True, max_chars=6000)
question = st.session_state.pop('pending_message', None)
spoken = False
if not question and submission:
    if isinstance(submission, str):
        question = submission
    else:
        question = submission.text or ''
        recording = getattr(submission, 'audio', None)
        if recording is not None:
            try:
                with st.spinner('Einen Moment, ich höre mir deine Frage an …'):
                    transcript = transcribe_recording(recording.getvalue())
                question = (question + '\n' + transcript).strip()
                spoken = True
            except Exception as exc:
                st.error(friendly_error(exc))
                question = None

if question:
    history = list(st.session_state.messages)
    st.session_state.messages.append({'role': 'user', 'content': question})
    with st.chat_message('user'):
        st.markdown(question)
    with st.chat_message('assistant', avatar='🎓'):
        try:
            with st.spinner('Einen Moment …'):
                result = answer_question(question, index, history=history,
                                         dialogue_state=st.session_state.dialogue_state,
                                         campus=None if campus == 'Alle' else campus,
                                         degree=None if degree == 'Alle' else degree,
                                         programme=None if programme == 'Alle' else programme)
            st.session_state.dialogue_state = result['dialogue_state']
            reply = {'role': 'assistant', 'content': result['answer'], 'sources': result['sources'],
                     'suggestions': result['suggestions'], 'kind': result['kind']}
            st.session_state.messages.append(reply)
            st.markdown(reply['content'])
            if auto_voice or spoken:
                try:
                    with st.spinner('Ich lese dir die Antwort vor …'):
                        reply['audio'] = synthesize_reply(reply['content'])
                    st.session_state.play_audio = len(st.session_state.messages) - 1
                except Exception as exc:
                    reply['voice_error'] = friendly_error(exc)
            st.rerun()
        except Exception as exc:
            st.error(friendly_error(exc))
            st.session_state.messages.pop()
