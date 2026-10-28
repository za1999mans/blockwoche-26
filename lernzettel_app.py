"""
Lernzettel Quiz-App
====================
Reads content from the 'Lernzettel' folder (subfolders = Bereiche),
generates AI-powered questions/answers/hints, and lets you practice.
"""

import streamlit as st
import json
import os
import uuid
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

import sys
sys.path.insert(0, str(Path(__file__).parent))
from ai_wrapper import AI, Docs, Config

# ─── PAGE CONFIG ──────────────────────────────────────────────
st.set_page_config(
    page_title="Lernzettel Quiz",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CSS ──────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;600;700;800&display=swap');

:root {
    --primary-gradient: linear-gradient(135deg, #7928CA 0%, #FF0080 100%);
    --blue-gradient: linear-gradient(135deg, #0070f3 0%, #00dfd8 100%);
    --glass-bg: rgba(255, 255, 255, 0.03);
    --glass-border: rgba(255, 255, 255, 0.1);
}

html, body, [class*="css"] { 
    font-family: 'Inter', sans-serif; 
}

h1, h2, h3, .outfit-text {
    font-family: 'Outfit', sans-serif !important;
}

.stApp {
    background: radial-gradient(circle at 50% 0%, #1a1a2e 0%, #0f0f1b 100%);
    color: #fafafa;
}

/* Sidebar Styling */
section[data-testid="stSidebar"] {
    background: rgba(10, 10, 20, 0.95) !important;
    border-right: 1px solid var(--glass-border) !important;
    backdrop-filter: blur(20px);
}

section[data-testid="stSidebar"] .stMarkdown h2 {
    background: var(--primary-gradient);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 800;
    font-size: 1.8rem;
    letter-spacing: -0.5px;
}

/* Question Card - Glassmorphism */
.question-card {
    background: rgba(255, 255, 255, 0.02);
    backdrop-filter: blur(10px);
    border: 1px solid var(--glass-border);
    border-radius: 24px;
    padding: 35px;
    margin-bottom: 25px;
    box-shadow: 0 10px 40px rgba(0,0,0,0.3), 0 0 20px rgba(0, 112, 243, 0.05);
    animation: slideUp 0.5s cubic-bezier(0.22, 1, 0.36, 1);
    position: relative;
    overflow: hidden;
}

.question-card::before {
    content: "";
    position: absolute;
    top: 0; left: 0; right: 0; height: 4px;
    background: var(--blue-gradient);
}

.question-card h3 { 
    color: #00dfd8; 
    font-size: 0.9rem; 
    text-transform: uppercase; 
    letter-spacing: 2px;
    margin-bottom: 15px; 
    font-weight: 700; 
}

.question-card p { 
    color: #ffffff; 
    font-size: 1.4rem; 
    line-height: 1.5; 
    margin: 0;
    font-weight: 500;
}

/* Answer Card */
.answer-card {
    background: rgba(0, 223, 216, 0.03);
    border: 1px solid rgba(0, 223, 216, 0.2);
    border-radius: 20px;
    padding: 25px;
    margin-top: 20px;
    animation: fadeIn 0.4s ease;
}

.answer-card h4 { 
    color: #00dfd8; 
    margin-bottom: 10px; 
    font-size: 0.9rem; 
    text-transform: uppercase;
    font-weight: 700; 
}

/* Hint Card */
.hint-card {
    background: rgba(245, 166, 35, 0.03);
    border: 1px solid rgba(245, 166, 35, 0.2);
    border-radius: 20px;
    padding: 20px;
    margin-top: 15px;
}

.hint-card h4 { 
    color: #f5a623; 
    margin-bottom: 8px; 
    font-size: 0.85rem; 
    text-transform: uppercase;
    font-weight: 700; 
}

/* List Items */
.q-list-item {
    background: var(--glass-bg);
    border: 1px solid var(--glass-border);
    border-radius: 16px;
    padding: 20px;
    margin-bottom: 15px;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.q-list-item:hover { 
    transform: translateX(5px);
    border-color: rgba(0, 112, 243, 0.5);
    background: rgba(255, 255, 255, 0.05);
}

.q-list-item .badge {
    display: inline-block;
    background: rgba(0, 112, 243, 0.1);
    color: #0070f3;
    border-radius: 8px;
    padding: 4px 12px;
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
}

.badge-red { 
    background: rgba(255, 0, 128, 0.1) !important; 
    color: #ff0080 !important; 
}

/* Stats */
.stat-box {
    background: var(--glass-bg);
    border: 1px solid var(--glass-border);
    border-radius: 16px;
    padding: 20px;
    text-align: center;
}

.stat-box .num { 
    font-size: 2.2rem; 
    font-weight: 800; 
    font-family: 'Outfit', sans-serif;
    background: var(--blue-gradient);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.stat-box .label { 
    font-size: 0.75rem; 
    color: #888; 
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-top: 5px; 
}

/* Buttons Styling */
div.stButton > button {
    border-radius: 12px !important;
    padding: 12px 24px !important;
    font-weight: 600 !important;
    font-family: 'Inter', sans-serif !important;
    text-transform: none !important;
    letter-spacing: 0.2px !important;
    transition: all 0.2s ease !important;
    border: 1px solid var(--glass-border) !important;
    background: var(--glass-bg) !important;
    color: #fff !important;
}

div.stButton > button:hover {
    border-color: #0070f3 !important;
    box-shadow: 0 0 20px rgba(0, 112, 243, 0.2) !important;
    background: rgba(0, 112, 243, 0.1) !important;
}

div.stButton > button[kind="primary"] {
    background: var(--primary-gradient) !important;
    border: none !important;
    box-shadow: 0 4px 15px rgba(121, 40, 202, 0.3) !important;
}

div.stButton > button[kind="primary"]:hover {
    box-shadow: 0 6px 20px rgba(121, 40, 202, 0.5) !important;
    transform: scale(1.02) !important;
}

/* Tabs Styling */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background: transparent;
}

.stTabs [data-baseweb="tab"] {
    background: var(--glass-bg);
    border-radius: 12px 12px 0 0;
    padding: 10px 20px;
    color: #888;
}

.stTabs [aria-selected="true"] {
    background: rgba(255, 255, 255, 0.05) !important;
    color: #fff !important;
}

/* Animations */
@keyframes slideUp { 
    from { opacity: 0; transform: translateY(30px); } 
    to { opacity: 1; transform: translateY(0); } 
}

@keyframes fadeIn { 
    from { opacity: 0; } 
    to { opacity: 1; } 
}

</style>
""", unsafe_allow_html=True)

# ─── CONSTANTS & CONFIG ────────────────────────────────────────
DATA_FILE = Path(__file__).parent / "lernzettel_data.json"
DEFAULT_LERNZETTEL_DIR = str(Path(__file__).parent / "Lernzettel")

MODELS = {
    "gpt-4o-mini (schnell & günstig)": ("openai", "gpt-4o-mini"),
    "gpt-4.1-nano (sehr schnell)": ("openai", "gpt-4.1-nano"),
    "deepseek-chat (alternativ)": ("deepseek", "deepseek-chat"),
}

# ─── PERSISTENCE & HELPERS ────────────────────────────────────
def load_data() -> dict:
    if DATA_FILE.exists():
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_data(data: dict):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_bereiche(path_str: str) -> list[str]:
    path = Path(path_str)
    if not path.exists() or not path.is_dir():
        return []
    return sorted([d.name for d in path.iterdir() if d.is_dir() and not d.name.startswith(".")])

def read_bereich_content(path_str: str, bereich: str) -> dict[str, str]:
    path = Path(path_str) / bereich
    if not path.exists():
        return {}
    texts = Docs.read_folder(path)
    return texts

# ─── AI QUESTION GENERATOR ────────────────────────────────────
def generate_questions(path_str: str, bereich: str, n: int, provider: str, model: str) -> list[dict]:
    texts = read_bereich_content(path_str, bereich)
    if not texts:
        return []

    combined = ""
    source_files = []
    for path, content in texts.items():
        fname = Path(path).name
        source_files.append(fname)
        combined += f"\n\n--- {fname} ---\n{content[:3000]}"

    combined = combined[:8000]

    prompt = f"""Du bist ein Lernassistent. Basierend auf folgendem Lernmaterial generierst du {n} Lernfragen auf Deutsch.

LERNMATERIAL (Bereich: {bereich}):
{combined}

Gib genau {n} Fragen zurück. Jede Frage soll:
- Eine klare, präzise Frage aus dem Lernmaterial sein
- Eine detaillierte Modellantwort haben
- Einen hilfreichen Hinweis haben (nicht die Antwort verraten, aber helfen)

Antworte NUR mit validem JSON in diesem Format:
{{
  "questions": [
    {{
      "question": "...",
      "answer": "...",
      "hint": "..."
    }}
  ]
}}"""

    try:
        resp = AI.chat(
            prompt,
            system="Du bist ein hilfreicher Lernassistent. Antworte immer auf Deutsch mit validem JSON.",
            model=model,
            provider=provider,
            json_mode=True,
            max_tokens=3000,
        )
        import re
        raw = resp.text.strip()
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        parsed = json.loads(raw)
        questions_raw = parsed.get("questions", [])

        results = []
        for q in questions_raw:
            results.append({
                "id": str(uuid.uuid4()),
                "bereich": bereich,
                "question": q.get("question", ""),
                "answer": q.get("answer", ""),
                "hint": q.get("hint", ""),
                "source_files": source_files,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "times_wrong": 0,
                "last_result": None,
            })
        return results
    except Exception as e:
        st.error(f"Fehler beim Generieren: {e}")
        return []

# ─── SESSION STATE INIT ───────────────────────────────────────
if "data" not in st.session_state:
    st.session_state.data = load_data()
if "lernzettel_path" not in st.session_state:
    st.session_state.lernzettel_path = DEFAULT_LERNZETTEL_DIR
if "current_q_index" not in st.session_state:
    st.session_state.current_q_index = 0
if "show_answer" not in st.session_state:
    st.session_state.show_answer = False
if "show_hint" not in st.session_state:
    st.session_state.show_hint = False
if "practice_bereich" not in st.session_state:
    st.session_state.practice_bereich = None
if "practice_queue" not in st.session_state:
    st.session_state.practice_queue = []
if "repeat_mode" not in st.session_state:
    st.session_state.repeat_mode = False

# ─── SIDEBAR ──────────────────────────────────────────────────
with st.sidebar:
    st.markdown("<h2 class='outfit-text'>🧠 Lernzettel Quiz</h2>", unsafe_allow_html=True)
    st.markdown("---")

    # Path Input
    st.markdown("### 📁 Verzeichnis")
    new_path = st.text_input(
        "Lernzettel Pfad",
        value=st.session_state.lernzettel_path,
        placeholder="z.B. /Benutzer/Name/Dokumente/Lernzettel",
        help="Absoluter Pfad zum Ordner, der deine Lernbereiche enthält."
    )
    if new_path != st.session_state.lernzettel_path:
        st.session_state.lernzettel_path = new_path
        st.rerun()

    current_path = st.session_state.lernzettel_path
    bereiche = get_bereiche(current_path)

    if not bereiche:
        if not Path(current_path).exists():
            st.error("Pfad existiert nicht!")
        else:
            st.warning("Keine Bereiche (Unterordner) gefunden.")
    else:
        selected_bereich = st.selectbox(
            "📂 Bereich auswählen",
            bereiche,
            key="selected_bereich",
        )

        st.markdown("---")
        st.markdown("### ⚙️ KI-Einstellungen")

        selected_model_name = st.selectbox(
            "🤖 Modell",
            list(MODELS.keys()),
            key="model_selection",
        )
        provider, model_id = MODELS[selected_model_name]
        Config.default_provider = provider

        n_questions = st.slider("Anzahl Fragen", min_value=3, max_value=15, value=5, key="n_questions")

        st.markdown("---")

        bereich_data = st.session_state.data.get(selected_bereich, [])
        total_q = len(bereich_data)
        wrong_q = len([q for q in bereich_data if q.get("times_wrong", 0) > 0])

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f'<div class="stat-box"><div class="num">{total_q}</div><div class="label">Fragen gesamt</div></div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="stat-box"><div class="num">{wrong_q}</div><div class="label">Zum Wiederholen</div></div>', unsafe_allow_html=True)

        st.markdown("---")

        if st.button("🔄 Neue Fragen generieren", use_container_width=True, type="primary"):
            with st.spinner(f"Generiere {n_questions} Fragen für '{selected_bereich}'..."):
                new_qs = generate_questions(current_path, selected_bereich, n_questions, provider, model_id)
                if new_qs:
                    if selected_bereich not in st.session_state.data:
                        st.session_state.data[selected_bereich] = []
                    st.session_state.data[selected_bereich].extend(new_qs)
                    save_data(st.session_state.data)
                    st.success(f"✅ {len(new_qs)} Fragen hinzugefügt!")
                    st.rerun()
                else:
                    st.error("Keine Fragen generiert. Stelle sicher, dass Dateien im Bereich vorhanden sind.")

        if st.button("🗑️ Alle Fragen löschen", use_container_width=True):
            if selected_bereich in st.session_state.data:
                del st.session_state.data[selected_bereich]
                save_data(st.session_state.data)
                st.session_state.current_q_index = 0
                st.session_state.practice_queue = []
                st.rerun()

        st.markdown("---")
        st.caption("Fragen werden in `lernzettel_data.json` gespeichert.")

# ─── MAIN CONTENT ─────────────────────────────────────────────
if not bereiche:
    st.title("🧠 Lernzettel Quiz")
    st.info("Erstelle zuerst Unterordner im `Lernzettel/`-Ordner und füge Lernmaterial hinzu.")
    st.stop()

selected_bereich = st.session_state.get("selected_bereich", bereiche[0] if bereiche else None)
bereich_questions = st.session_state.data.get(selected_bereich, [])

st.markdown(f"<h1 class='outfit-text'>🧠 Lernzettel Quiz — {selected_bereich}</h1>", unsafe_allow_html=True)
st.markdown("<div style='height: 2px; background: var(--glass-border); margin: 20px 0;'></div>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📚 Fragen üben", "🔁 Wiederholungsliste", "📋 Alle Fragen"])

# ══════════════════════════════════════════════
# TAB 1: ÜBEN
# ══════════════════════════════════════════════
with tab1:
    if not bereich_questions:
        st.markdown("""
        <div style="text-align:center; padding: 80px 20px; color: #888;">
            <div style="font-size:4rem; margin-bottom: 20px;">📭</div>
            <h2 class="outfit-text" style="color:#fff; margin-bottom: 10px;">Noch keine Fragen</h2>
            <p style="font-size: 1.1rem; max-width: 400px; margin: 0 auto;">Klicke in der Seitenleiste auf <strong style="color: #00dfd8;">„Neue Fragen generieren"</strong>, um deine Lernsession zu starten.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Build practice queue
        if (st.session_state.practice_bereich != selected_bereich or
                not st.session_state.practice_queue):
            st.session_state.practice_bereich = selected_bereich
            st.session_state.practice_queue = list(range(len(bereich_questions)))
            st.session_state.current_q_index = 0
            st.session_state.show_answer = False
            st.session_state.show_hint = False

        queue = st.session_state.practice_queue
        idx = st.session_state.current_q_index

        if idx >= len(queue):
            st.markdown("""
            <div style="text-align:center; padding: 60px; background: rgba(0, 223, 216, 0.05); border-radius: 24px; border: 1px solid rgba(0, 223, 216, 0.1);">
                <div style="font-size:4rem; margin-bottom: 20px;">🎉</div>
                <h2 class="outfit-text" style="color:#00dfd8;">Hervorragend!</h2>
                <p style="color: #888; font-size: 1.1rem;">Du hast alle Fragen in diesem Bereich durchgearbeitet.</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("🔄 Neu starten"):
                st.session_state.current_q_index = 0
                st.session_state.show_answer = False
                st.session_state.show_hint = False
                st.rerun()
        else:
            q = bereich_questions[queue[idx]]
            progress = idx / len(queue)

            st.progress(progress, text=f"Frage {idx + 1} von {len(queue)}")
            st.markdown("")

            # Question card
            st.markdown(f"""
            <div class="question-card">
                <h3>❓ Frage {idx + 1}</h3>
                <p>{q['question']}</p>
            </div>
            """, unsafe_allow_html=True)

            col_hint, col_show = st.columns([1, 1])
            with col_hint:
                if st.button("💡 Hinweis anzeigen", key="hint_btn"):
                    st.session_state.show_hint = not st.session_state.show_hint
            with col_show:
                if st.button("👁️ Antwort anzeigen", key="show_btn"):
                    st.session_state.show_answer = not st.session_state.show_answer

            if st.session_state.show_hint:
                st.markdown(f"""
                <div class="hint-card">
                    <h4>💡 Hinweis</h4>
                    <p>{q['hint']}</p>
                </div>
                """, unsafe_allow_html=True)

            if st.session_state.show_answer:
                st.markdown(f"""
                <div class="answer-card">
                    <h4>✅ Modellantwort</h4>
                    <p>{q['answer']}</p>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("---")
            c1, c2, c3 = st.columns([1, 1, 1])
            with c1:
                if st.button("✅ Richtig beantwortet", use_container_width=True, type="primary"):
                    q["last_result"] = "correct"
                    save_data(st.session_state.data)
                    st.session_state.current_q_index += 1
                    st.session_state.show_answer = False
                    st.session_state.show_hint = False
                    st.rerun()
            with c2:
                if st.button("❌ Falsch beantwortet", use_container_width=True):
                    q["last_result"] = "wrong"
                    q["times_wrong"] = q.get("times_wrong", 0) + 1
                    save_data(st.session_state.data)
                    st.session_state.current_q_index += 1
                    st.session_state.show_answer = False
                    st.session_state.show_hint = False
                    st.rerun()
            with c3:
                if st.button("⏭️ Überspringen", use_container_width=True):
                    st.session_state.current_q_index += 1
                    st.session_state.show_answer = False
                    st.session_state.show_hint = False
                    st.rerun()

# ══════════════════════════════════════════════
# TAB 2: WIEDERHOLUNG
# ══════════════════════════════════════════════
with tab2:
    wrong_questions = [q for q in bereich_questions if q.get("times_wrong", 0) > 0]

    if not wrong_questions:
        st.markdown("""
        <div style="text-align:center; padding: 80px 20px; color: #888;">
            <div style="font-size:4rem; margin-bottom: 20px;">🏆</div>
            <h2 class="outfit-text" style="color:#00dfd8; margin-bottom: 10px;">Alles im Griff!</h2>
            <p style="font-size: 1.1rem; max-width: 400px; margin: 0 auto;">Du hast momentan keine falsch beantworteten Fragen. Zeit für neuen Stoff?</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"<h3 class='outfit-text'>🔁 {len(wrong_questions)} Frage(n) zum Wiederholen</h3>", unsafe_allow_html=True)
        st.markdown("")

        for i, q in enumerate(wrong_questions):
            with st.expander(f"❌ {q['question'][:80]}... ({q.get('times_wrong',0)}× falsch)"):
                st.markdown(f"""
                <div class="answer-card">
                    <h4>✅ Korrekte Antwort</h4>
                    <p>{q['answer']}</p>
                </div>
                <div class="hint-card" style="margin-top:10px;">
                    <h4>💡 Hinweis</h4>
                    <p>{q['hint']}</p>
                </div>
                """, unsafe_allow_html=True)

                col_a, col_b = st.columns([1, 1])
                with col_a:
                    if st.button("✅ Als gelernt markieren", key=f"mark_learned_{q['id']}"):
                        q["last_result"] = "correct"
                        q["times_wrong"] = 0
                        save_data(st.session_state.data)
                        st.rerun()
                with col_b:
                    if st.button("🗑️ Frage löschen", key=f"del_wrong_{q['id']}"):
                        st.session_state.data[selected_bereich] = [
                            x for x in bereich_questions if x["id"] != q["id"]
                        ]
                        save_data(st.session_state.data)
                        st.rerun()

# ══════════════════════════════════════════════
# TAB 3: ALLE FRAGEN
# ══════════════════════════════════════════════
with tab3:
    if not bereich_questions:
        st.info("Noch keine Fragen in diesem Bereich.")
    else:
        st.markdown(f"<h3 class='outfit-text'>📋 Alle Fragen — {selected_bereich} <span style='color: #888; font-weight: 400;'>({len(bereich_questions)})</span></h3>", unsafe_allow_html=True)
        st.markdown("")

        # Filter options
        filter_col, _ = st.columns([2, 3])
        with filter_col:
            filter_status = st.selectbox(
                "Filter",
                ["Alle", "Nur falsche", "Nur richtige", "Noch nicht geübt"],
                key="filter_status",
            )

        def filter_q(q):
            s = filter_status
            if s == "Alle":
                return True
            if s == "Nur falsche":
                return q.get("times_wrong", 0) > 0
            if s == "Nur richtige":
                return q.get("last_result") == "correct" and q.get("times_wrong", 0) == 0
            if s == "Noch nicht geübt":
                return q.get("last_result") is None
            return True

        filtered = [q for q in bereich_questions if filter_q(q)]
        st.caption(f"{len(filtered)} Frage(n) angezeigt")
        st.markdown("")

        for q in filtered:
            wrong_count = q.get("times_wrong", 0)
            result = q.get("last_result")
            if result == "correct":
                status_badge = '<span class="badge">✅ Richtig</span>'
            elif wrong_count > 0:
                status_badge = f'<span class="badge badge-red">❌ {wrong_count}× falsch</span>'
            else:
                status_badge = '<span class="badge" style="background:rgba(139,148,158,0.15);color:#8b949e;">⬜ Unbeantwortet</span>'

            src = ", ".join(q.get("source_files", []))
            st.markdown(f"""
            <div class="q-list-item">
                <div>{status_badge}<strong>{q['question']}</strong></div>
                <div class="meta">📁 {src} &nbsp;|&nbsp; 🕐 {q.get('created_at','')}</div>
            </div>
            """, unsafe_allow_html=True)

            with st.expander("Antwort & Hinweis anzeigen"):
                st.markdown(f"**✅ Antwort:** {q['answer']}")
                st.markdown(f"**💡 Hinweis:** {q['hint']}")
                col_a, col_b = st.columns([1, 4])
                with col_a:
                    if st.button("🗑️ Löschen", key=f"del_{q['id']}"):
                        st.session_state.data[selected_bereich] = [
                            x for x in bereich_questions if x["id"] != q["id"]
                        ]
                        save_data(st.session_state.data)
                        st.rerun()
