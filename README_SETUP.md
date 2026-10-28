## Projekt-Setup unter Windows

### 1. Python installieren

1. Lade Python hier herunter:
   [https://www.python.org/downloads/](https://www.python.org/downloads/)

2. Achte bei der Installation darauf, dass folgende Optionen aktiviert sind:

   * **Add Python to PATH**
   * **pip mitinstallieren**

3. Überprüfe anschließend, ob Python und pip korrekt installiert wurden. Öffne dafür die **Eingabeaufforderung** / **CMD** und führe aus:

```bash
python --version
pip --version
```

4. Falls die Befehle nicht funktionieren, schließe das Terminal und öffne es erneut. Falls es danach immer noch nicht funktioniert, starte den Computer neu.

---

### 2. Poetry installieren

1. Öffne die **Eingabeaufforderung** / **CMD**.

2. Installiere Poetry mit:

```bash
pip install poetry
```

3. Überprüfe, ob Poetry installiert wurde:

```bash
poetry --version
```

---

## Projekt-Setup unter macOS

### 1. Homebrew installieren

1. Öffne das **Terminal**.

2. Installiere Homebrew über die offizielle Website:
   [https://brew.sh](https://brew.sh)

   Oder führe direkt diesen Befehl im Terminal aus:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

3. Überprüfe, ob Homebrew korrekt installiert wurde:

```bash
brew --version
```

---

### 2. Poetry installieren

1. Öffne das **Terminal**.

2. Installiere Poetry mit:

```bash
brew install poetry
```

3. Überprüfe, ob Poetry korrekt installiert wurde:

```bash
poetry --version
```

---

## Projekt in Antigravity oder VS Code einrichten

### 3. Editor installieren

Installiere entweder:

* **Antigravity**:
  [https://antigravity.google](https://antigravity.google)

oder

* **Visual Studio Code**:
  [https://code.visualstudio.com/download](https://code.visualstudio.com/download)

Öffne anschließend Antigravity und melde dich mit deinem Google-Konto an.

---

### 4. Projektordner öffnen

1. Öffne in Antigravity einen Ordner, in dem die Projektdateien gespeichert werden sollen.

2. Öffne das integrierte Terminal in Antigravity:

```text
Oben links in der Menüleiste → Terminal → New Terminal
```

3. Führe folgenden Befehl aus:

```bash
poetry init
```

Dieser Befehl erstellt ein neues Poetry-Projekt im aktuellen Ordner.

4. Beantworte die Fragen im Terminal. Du kannst meistens einfach **Enter** drücken, um die Standardwerte zu übernehmen. Beim Feld **Author** solltest du deinen Namen oder einen beliebigen Namen eintragen.

---

### 5. README-Datei erstellen

Erstelle im aktuellen Ordner eine neue Datei mit dem Namen:

```text
readme.md
```

Das kannst du entweder über das Datei-Symbol oben links machen oder über das Terminal mit:

```bash
touch readme.md
```

---

### 6. Benötigte Pakete installieren

Führe folgenden Befehl aus, um die benötigten Pakete zu installieren:

```bash
poetry add openai python-dotenv pypdf numpy streamlit
```

Dadurch werden die benötigten Libraries für das Projekt heruntergeladen.

---

### 7. Poetry-Umgebung verwenden

Nach der Installation erstellt Poetry automatisch eine eigene virtuelle Umgebung. Diese Umgebung muss verwendet werden, damit dein Projekt Zugriff auf die installierten Pakete hat.

Führe folgenden Befehl aus, um den Speicherort der Umgebung anzuzeigen:

```bash
poetry env info
```

Du siehst dann zum Beispiel so etwas:

```text
Virtualenv
Python:         3.13.5
Implementation: CPython
Path:           /Users/zmansour/Library/Caches/pypoetry/virtualenvs/blockwoche-TSVD7g-R-py3.13
Executable:     /Users/zmansour/Library/Caches/pypoetry/virtualenvs/blockwoche-TSVD7g-R-py3.13/bin/python
Valid:          True
```

Wichtig ist hier der Wert bei **Path**. Diesen Pfad brauchst du im nächsten Schritt.

---

### 8. Python-Interpreter in Antigravity auswählen

1. Kopiere den Pfad aus der Zeile **Path**.

   Beispiel:

```text
/Users/zmansour/Library/Caches/pypoetry/virtualenvs/blockwoche-TSVD7g-R-py3.13
```

2. Erstelle eine neue Python-Datei, zum Beispiel:

```text
main.py
```

3. Antigravity erkennt nun, dass es sich um eine Python-Datei handelt. Unten links solltest du eine Python-Version sehen, zum Beispiel:

```text
3.14.**
```

4. Klicke auf diese Python-Version.

5. Wähle im Menü die Option:

```text
Enter interpreter path
```

6. Füge den zuvor kopierten Pfad ein und bestätige mit **Enter**.

7. Danach sollte unten links nicht mehr die allgemeine Python-Version angezeigt werden, sondern die Poetry-Umgebung, zum Beispiel:

```text
blockwoche-TSVD7g-R-py3.13
```
