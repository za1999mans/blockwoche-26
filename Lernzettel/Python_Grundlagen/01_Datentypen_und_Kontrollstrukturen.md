# Python Grundlagen: Datentypen und Kontrollstrukturen

## 1. Grundlegende Datentypen
Python ist dynamisch, aber stark typisiert. Die wichtigsten Basisdatentypen sind:
- **`int`**: Ganze Zahlen (z.B. `x = 42`, beliebig groß in Python 3).
- **`float`**: Fließkommazahlen (z.B. `pi = 3.14159`).
- **`str`**: Zeichenketten (z.B. `s = "Hallo Welt"`). Strings sind unveränderlich (*immutable*).
- **`bool`**: Wahrheitswerte (`True` oder `False`).

## 2. Komplexe Datenstrukturen
- **Listen (`list`)**:
  - Geordnet, veränderlich (*mutable*), erlaubt Duplikate.
  - Erstellung: `fruits = ["Apfel", "Banane", "Kirsche"]`
  - Zugriff: `fruits[0]` (erstes Element), `fruits[-1]` (letztes Element).
  - Methoden: `.append()`, `.extend()`, `.pop()`, `.remove()`.
- **Tupel (`tuple`)**:
  - Geordnet, unveränderlich (*immutable*).
  - Erstellung: `point = (10, 20)`
- **Sets (`set`)**:
  - Ungeordnet, keine Duplikate, optimiert für Mitgliedschaftstests (`in`).
  - Erstellung: `unique_ids = {1, 2, 3}`
- **Dictionaries (`dict`)**:
  - Key-Value-Paare, Schlüssel müssen hashbar sein (z.B. Strings, Zahlen, Tupel).
  - Erstellung: `user = {"name": "Alex", "age": 25}`
  - Zugriff mit Fallback: `user.get("role", "Gast")`

## 3. Kontrollstrukturen
- **Verzweigungen (`if-elif-else`)**:
  ```python
  if score >= 90:
      grade = "A"
  elif score >= 80:
      grade = "B"
  else:
      grade = "C"
  ```
- **Schleifen (`for` und `while`)**:
  ```python
  for item in items:
      print(item)

  for i, item in enumerate(items):
      print(f"{i}: {item}")
  ```

## 4. List Comprehensions
Kompakte Syntax zum Transformieren und Filtern von Listen:
```python
quadrate = [x**2 for x in range(10) if x % 2 == 0]
```

