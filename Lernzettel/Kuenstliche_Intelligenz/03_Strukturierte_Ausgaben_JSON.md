# Künstliche Intelligenz: Strukturierte Ausgaben und JSON-Modus

## 1. Warum strukturierte Ausgaben?
Standard-LLM-Antworten sind reiner Fließtext in natürlicher Sprache. Wenn eine Anwendung (wie z.B. unsere Quiz-App) die Antwort programmatisch weiterverarbeiten will (z.B. Fragen, Antworten, Punkte als Python-Objekt parsen), muss die Ausgabe in einem strikten Format wie JSON vorliegen.

## 2. JSON Mode vs. Freitext
- **Problem bei Freitext**: Das Modell schreibt Einleitungssätze wie "Hier sind die Fragen:" oder formatiert in Markdown-Codeblöcken (` ```json ... ``` `).
- **JSON Mode (`response_format={"type": "json_object"}`)**:
  - Zwingt das Modell, syntaktisch valides JSON zu erzeugen.
  - Wichtig: Der Prompt muss das Wort "JSON" explizit erwähnen, sonst wirft die API einen Fehler.

## 3. Structured Outputs mit Schemadefinition
Moderne APIs (OpenAI Structured Outputs) erlauben die Übergabe eines JSON-Schemas (oder Pydantic-Modells). Das Modell garantiert zu 100% die Einhaltung der vorgegebenen Keys, Datentypen und Enums.

```json
{
  "name": "QuizItem",
  "strict": true,
  "schema": {
    "type": "object",
    "properties": {
      "question": { "type": "string" },
      "answer": { "type": "string" },
      "hint": { "type": "string" }
    },
    "required": ["question", "answer", "hint"],
    "additionalProperties": false
  }
}
```

