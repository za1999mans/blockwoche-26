"""Start: poetry run streamlit run hochschul_chatbot.py"""
from pathlib import Path
import streamlit as st

from hs_rag import (VectorIndex, answer_question, database_path, friendly_error,
                    index_status, load_environment)

load_environment()
st.set_page_config(page_title="Studienberatung · Hochschule Osnabrück", page_icon="🎓")
st.title("Studieren an der Hochschule Osnabrück")
st.caption("Fragen zu Studiengängen, Bewerbung und Campus – mit Quellen aus der Hochschul-Wissensbasis.")


@st.cache_resource
def load_index(path: str, modified: int):
    return VectorIndex(Path(path))


def show_sources(sources):
    if not sources:
        return
    with st.expander("Quellen zur Antwort"):
        for source in sources:
            st.markdown(f"**[{source['number']}] {source['title']}** — {source['heading']}")
            st.caption(f"Quellenstand: {source.get('retrieved_at') or 'unbekannt'}")
            for url in source["urls"]:
                st.markdown(f"[Offizielle Quelle öffnen]({url})")


db = database_path()
try:
    status = index_status(db)
    if not status["ready"]:
        st.info("Die Wissensbasis wird noch vorbereitet. Bitte zuerst den Datenimport ausführen.")
        st.code("poetry run python index_hs_data.py index")
        st.stop()
    index = load_index(str(db), db.stat().st_mtime_ns)
except Exception as exc:
    st.error(friendly_error(exc))
    st.stop()
if status["source_changed"]:
    st.warning("Die Quelldaten wurden seit dem letzten Import geändert. Die Antworten verwenden den gespeicherten Stand.")

with st.sidebar:
    st.subheader("Studieninteresse")
    campus = st.selectbox("Studienort", ["Alle", "Osnabrück", "Lingen", "Haste", "Westerberg", "Caprivi", "China"])
    degrees = sorted({c['abschluss'] for c in index.chunks if c.get('abschluss')})
    degree = st.selectbox("Abschluss", ["Alle"] + degrees)
    programmes = sorted({c['studiengang'] for c in index.chunks if c.get('studiengang')
                         and (campus == 'Alle' or campus.casefold() in (c.get('campus') or '').casefold())
                         and (degree == 'Alle' or degree == c.get('abschluss'))
                         and 'auslaufend' not in (c.get('status') or '').casefold()})
    programme = st.selectbox("Studiengang", ["Alle"] + programmes)
    st.caption("Allgemeine Informationen zu Bewerbung und Campus werden zusätzlich berücksichtigt.")
    if st.button("Neues Gespräch"):
        st.session_state.messages = []
        st.rerun()

st.session_state.setdefault("messages", [])
for message in st.session_state.messages:
    with st.chat_message(message['role']):
        st.markdown(message['content'])
        show_sources(message.get('sources', []))

if question := st.chat_input("Zum Beispiel: Welche Inhalte hat Informatik und an welchem Campus studiere ich?"):
    with st.chat_message("user"):
        st.markdown(question)
    history = list(st.session_state.messages)
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("assistant"):
        try:
            with st.spinner("Passende Hochschulinformationen suchen …"):
                result = answer_question(question, index, history=history,
                                         campus=None if campus == 'Alle' else campus,
                                         degree=None if degree == 'Alle' else degree,
                                         programme=None if programme == 'Alle' else programme)
            st.markdown(result['answer'])
            show_sources(result['sources'])
            st.session_state.messages.append({"role": "assistant", "content": result['answer'],
                                              "sources": result['sources']})
        except Exception as exc:
            st.error(friendly_error(exc))
