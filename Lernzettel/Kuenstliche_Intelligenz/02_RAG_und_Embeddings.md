# Künstliche Intelligenz: RAG und Vektoreinbettungen (Embeddings)

## 1. Was ist RAG (Retrieval-Augmented Generation)?
RAG löst zwei zentrale Probleme von LLMs:
1. Veraltetes Wissen (Knowledge Cutoff).
2. Halluzinationen bei firmeninternen oder privaten Dokumenten.

### Die RAG-Pipeline:
1. **Indexierung**: Dokumente einlesen, in handliche Chunks (Abschnitte) zerteilen und via Embedding-Modell in Vektoren umwandeln.
2. **Retrieval**: Bei einer Nutzeranfrage wird diese ebenfalls vektorisiert. Die ähnlichsten Chunks werden mittels Ähnlichkeitsmaß (z.B. Cosine Similarity) gesucht.
3. **Generation**: Die gefundenen Chunks werden zusammen mit der Nutzerfrage in den Prompt gepackt ("Beantworte die Frage nur anhand des folgenden Kontextes...").

## 2. Text Embeddings
Ein Text Embedding ist ein numerischer Vektor (z.B. 1536 Fließkommazahlen bei `text-embedding-3-small`), der die semantische Bedeutung eines Textes kodiert.
- Texte mit ähnlicher Bedeutung liegen im Vektorraum nah beieinander.
- **Cosine Similarity**: Misst den Winkel zwischen zwei Vektoren:
  $$\text{sim}(u, v) = \frac{u \cdot v}{\|u\| \|v\|}$$
  Ein Wert von 1.0 bedeutet identische Ausrichtung, 0 bedeutet orthogonal (keine thematische Ähnlichkeit).

## 3. Chunking-Strategien
- Zu große Chunks verwässern den semantischen Fokus.
- Zu kleine Chunks verlieren den Kontext des Satzes.
- Typische Praxis: Chunk-Größe von ca. 300–800 Zeichen mit einem Überlappungsbereich (Overlap) von 50–100 Zeichen.

