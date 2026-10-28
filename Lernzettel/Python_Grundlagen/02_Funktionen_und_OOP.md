# Python Grundlagen: Funktionen und Objektorientierung (OOP)

## 1. Funktionen
Funktionen werden mit dem Schlüsselwort `def` definiert:
```python
def begruessung(name: str, formal: bool = False) -> str:
    """Gibt eine Begrüßung zurück."""
    if formal:
        return f"Sehr geehrte(r) Frau/Herr {name}."
    return f"Hallo {name}!"
```

### Variable Argumente (`*args` und `**kwargs`)
- `*args`: Nimmt beliebig viele positionelle Argumente als Tupel entgegen.
- `**kwargs`: Nimmt beliebig viele benannte Argumente (*keyword arguments*) als Dictionary entgegen.

```python
def beispiel(*args, **kwargs):
    print("Positionelle Argumente:", args)
    print("Keyword Argumente:", kwargs)
```

## 2. Objektorientierte Programmierung (OOP)

### Klassen und Instanzen
```python
class Student:
    universitaet = "Hochschule"  # Klassenattribut

    def __init__(self, name: str, matrikelnummer: int):
        self.name = name                      # Instanzattribut
        self.matrikelnummer = matrikelnummer  # Instanzattribut

    def vorstellen(self) -> str:
        return f"Ich bin {self.name} (Nr: {self.matrikelnummer}) an der {self.universitaet}."

    def __repr__(self) -> str:
        return f"Student(name='{self.name}', matrikelnummer={self.matrikelnummer})"
```

### Vererbung
Eine Subklasse erbt Attribute und Methoden von der Superklasse. Mit `super()` wird die Elternklasse aufgerufen:
```python
class MasterStudent(Student):
    def __init__(self, name: str, matrikelnummer: int, thesis_titel: str):
        super().__init__(name, matrikelnummer)
        self.thesis_titel = thesis_titel
```

