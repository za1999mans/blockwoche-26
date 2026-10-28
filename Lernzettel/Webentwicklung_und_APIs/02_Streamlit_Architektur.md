# Webentwicklung & APIs: Streamlit-Architektur

## 1. Was ist Streamlit?
Streamlit ist ein Open-Source-Framework für Python, mit dem Entwickler in kürzester Zeit interaktive Webanwendungen für Data Science, KI und Prototyping bauen können – ganz ohne HTML, CSS oder JavaScript schreiben zu müssen.

## 2. Das Ausführungsmodell von Streamlit
- **Top-to-Bottom Execution**: Sobald der Benutzer mit einem Widget interagiert (Klick auf einen Button, Ändern eines Sliders oder Textfelds), führt Streamlit das **gesamte Python-Skript von oben nach unten neu aus** (*Rerun*).
- **Vorteil**: Extrem einfaches, deklaratives Programmiermodell.
- **Herausforderung**: Lokale Variablen gehen bei jedem Rerun verloren.

## 3. Session State (`st.session_state`)
Um Daten über Reruns hinweg im Speicher zu behalten (z.B. den Punktestand, die aktuelle Fragen-Nummer oder Benutzerdaten), verwendet man `st.session_state`:
```python
if "counter" not in st.session_state:
    st.session_state.counter = 0

if st.button("Hochzählen"):
    st.session_state.counter += 1

st.write(f"Zählerstand: {st.session_state.counter}")
```

## 4. Wichtige Layout- und UI-Elemente
- **`st.sidebar`**: Platzieren von Widgets in der linken Seitenleiste.
- **`st.columns([1, 2, 1])`**: Mehrspaltiges Layout nebeneinander.
- **`st.tabs(["Tab 1", "Tab 2"])`**: Strukturierung in Reiter.
- **`st.rerun()`**: Erzwingt sofortigen Neustart des Skripts (z.B. nach Datenänderungen).

