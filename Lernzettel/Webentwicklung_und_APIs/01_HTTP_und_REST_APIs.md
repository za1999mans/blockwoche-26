# Webentwicklung & APIs: HTTP-Grundlagen und REST

## 1. Das Client-Server-Modell
Webanwendungen kommunizieren nach dem Client-Server-Prinzip über HTTP/HTTPS:
- **Client (Frontend)**: Sendet einen HTTP-Request an den Server.
- **Server (Backend)**: Verarbeitet den Request und sendet eine HTTP-Response mit Daten zurück.

## 2. HTTP-Methoden (Verben)
- **GET**: Daten vom Server abrufen (idempotent, keine Seiteneffekte auf dem Server).
- **POST**: Neue Ressource erstellen (sendet Payload im Request-Body).
- **PUT**: Existierende Ressource vollständig ersetzen/aktualisieren.
- **PATCH**: Teile einer existierenden Ressource aktualisieren.
- **DELETE**: Ressource löschen.

## 3. HTTP-Statuscodes
- **2xx (Erfolg)**:
  - `200 OK`: Erfolgreiche Anfrage.
  - `201 Created`: Ressource erfolgreich erstellt.
- **4xx (Client-Fehler)**:
  - `400 Bad Request`: Fehlerhafte Syntax oder ungültige Parameter.
  - `401 Unauthorized`: Fehlende oder fehlerhafte Authentifizierung (z.B. API-Key fehlt).
  - `403 Forbidden`: Authentifiziert, aber keine Berechtigung für die Ressource.
  - `404 Not Found`: Ressource existiert nicht.
  - `429 Too Many Requests`: Rate-Limit überschritten.
- **5xx (Server-Fehler)**:
  - `500 Internal Server Error`: Unerwarteter Absturz auf dem Server.
  - `503 Service Unavailable`: Server überlastet oder in Wartung.

## 4. REST (Representational State Transfer) Prinzipien
1. **Zustandslosigkeit (*Stateless*)**: Jeder Request muss alle nötigen Informationen zur Bearbeitung enthalten.
2. **Einheitliche Schnittstelle (*Uniform Interface*)**: Ressourcen werden über URLs identifiziert (z.B. `GET /api/v1/users/42`).
3. **JSON als Standard**: Datenübertragung erfolgt heutzutage nahezu ausnahmslos als JSON.

