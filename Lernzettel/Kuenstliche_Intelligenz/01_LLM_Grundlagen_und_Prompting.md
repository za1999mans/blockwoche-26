# Künstliche Intelligenz: LLM-Grundlagen und Prompting

## 1. Was sind Large Language Models (LLMs)?
LLMs basieren meist auf der Transformer-Architektur (Decoder-Only, z.B. GPT-4, DeepSeek). Sie sagen autoregressiv das nächste Token (Wortbaustein) basierend auf dem bisherigen Kontext voraus.

- **Tokens**: Wörter oder Wortteile. Ein Token entspricht ca. 4 Zeichen oder 0.75 Wörtern im Englischen/Deutschen.
- **Kontextfenster (*Context Window*)**: Die maximale Anzahl an Tokens (Eingabe + Ausgabe), die das Modell gleichzeitig im Speicher halten kann.

## 2. Rollen in Chat-Modellen
- **System**: Definiert das Grundverhalten, Regeln, Persona und Einschränkungen des Assistenten.
- **User**: Die Eingabe oder Anfrage des Benutzers.
- **Assistant**: Die Antwort des Modells.

## 3. Wichtige Hyperparameter
- **Temperature (0.0 bis 2.0)**:
  - Niedrig (z.B. 0.0 - 0.2): Deterministisch, präzise, ideal für Fakten und Code.
  - Hoch (z.B. 0.7 - 1.2): Kreativ, abwechslungsreich, höherer Zufallsfaktor.
- **Top-P (Nucleus Sampling)**:
  - Begrenzt die Auswahl auf die wahrscheinlichsten Tokens, deren kumulierte Wahrscheinlichkeit `p` erreicht.
- **Max Tokens**:
  - Maximale Tokenanzahl der generierten Antwort.

## 4. Prompt Engineering Techniken
- **Zero-Shot**: Aufgabe ohne Beispiele direkt beschreiben.
- **Few-Shot**: Dem Modell 2-3 konkrete Frage-Antwort-Beispiele im Prompt mitgeben, um das Ausgabeformat zu kalibrieren.
- **Chain-of-Thought (CoT)**: Das Modell anweisen, Schritt für Schritt laut nachzudenken ("Denke Schritt für Schritt"), bevor die finale Antwort gegeben wird.

