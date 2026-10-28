# Python Grundlagen: Fehlerbehandlung und Dateioperationen

## 1. Exception Handling (`try / except / finally`)
Laufzeitfehler werden in Python als Exceptions abgefangen:
```python
try:
    wert = int(benutzer_eingabe)
    ergebnis = 100 / wert
except ValueError:
    print("Ungültige Zahl eingegeben.")
except ZeroDivisionError:
    print("Teilen durch 0 ist nicht erlaubt.")
except Exception as e:
    print(f"Unerwarteter Fehler: {e}")
else:
    print("Wird nur ausgeführt, wenn keine Ausnahme aufgetreten ist.")
finally:
    print("Wird IMMER ausgeführt (z.B. Aufräumarbeiten).")
```

## 2. Eigene Exceptions
Exceptions leiten von `Exception` ab:
```python
class UngueltigesAlterError(Exception):
    pass

def set_alter(alter: int):
    if alter < 0:
        raise UngueltigesAlterError("Alter darf nicht negativ sein!")
```

## 3. Dateioperationen mit `with`
Der Kontextmanager (`with`) stellt sicher, dass Dateien auch bei Fehlern korrekt geschlossen werden:
```python
# Datei lesen
with open("notizen.txt", "r", encoding="utf-8") as f:
    inhalt = f.read()

# Datei schreiben
with open("ausgabe.txt", "w", encoding="utf-8") as f:
    f.write("Erste Zeile\n")
```

## 4. Modernes Dateisystem mit `pathlib`
`pathlib.Path` ist dem älteren `os.path` vorzuziehen:
```python
from pathlib import Path

ordner = Path("./meine_daten")
ordner.mkdir(exist_ok=True)
datei = ordner / "info.json"
if datei.exists():
    text = datei.read_text(encoding="utf-8")
```

