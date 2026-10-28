# Deploy the Hochschul chatbot on Streamlit Community Cloud

The Streamlit entrypoint is `hochschul_chatbot.py` in the repository root.

## Dependencies and Python

Use Python **3.12** in Streamlit's **Advanced settings**. The project supports
Python 3.12 through 3.15. Previously, `pyproject.toml` and `poetry.lock` required
Python 3.15 or newer, preventing installation on an older cloud interpreter.

Keep `pyproject.toml` and `poetry.lock` together in Git. Streamlit uses Poetry for
this project; no additional `requirements.txt` is needed. Poetry's
`package-mode = false` installs the dependencies without trying to install this
collection of app scripts as a Python package.

To validate dependency changes locally:

```bash
poetry check --lock
poetry install --only main --dry-run
poetry run python -m unittest discover -s tests -v
```

## Supply the existing search index

The app now ships with an offline deployment bundle:

- `HS_DATA/_rag/vector_index.sqlite3.gz` — the actual precomputed embeddings,
  texts, and metadata, compressed to about 9 MB.
- `HS_DATA/_rag/vector_index.sqlite3.gz.json` — checksums, corpus fingerprint,
  model, dimensions, and chunk count.
- `HS_DATA/_rag/chunks.jsonl` — the matching source chunks.

Keep all three files and `hs_index_bundle.py` in Git. On a fresh cloud startup,
the app checks and restores the bundle to `data/hs_vector_index.sqlite3` before
loading the chat. It does not call the embedding API during this startup.
The existing 1,687 document embeddings are reused, including after a cloud
restart. The uncompressed runtime database remains ignored by Git.

To update the package after changing and reindexing the corpus:

```bash
poetry run python index_hs_data.py index
poetry run python index_hs_data.py package
```

Commit the updated compressed package, its JSON manifest and `chunks.jsonl`
together. The restore checks reject a bundle that does not match the chunks.
Only active document embeddings and selected index metadata are exported;
local absolute paths and unused embedding-cache entries are not included.

An existing runtime database is preserved. Alternatively, provide a database
through your hosting setup and set `HS_RAG_DB` to its path. Relative configured
paths are resolved from the project root, independently of the working directory.

## Configure secrets and deploy

1. Commit and push the dependency fixes, the app modules (including
   `hs_dialogue.py`, `hs_voice.py`, and `hs_index_bundle.py`), the corpus, and
   both index-bundle files to the branch
   used by Streamlit.
2. Select `hochschul_chatbot.py` as the main file.
3. Choose Python **3.12** in **Advanced settings** when creating the deployment.
4. Add the following under **Secrets**, using your actual API key:

   ```toml
   OPENAI_API_KEY = "your-api-key"
   ```

   Add any optional `HS_CHAT_PROVIDER`, `HS_CHAT_MODEL`, or voice configuration
   here too, using top-level TOML keys. Top-level secrets become environment
   variables, which the app already reads. The local `.env` stays local.
5. Deploy, or let Streamlit rebuild after the push. If it still fails, open
   **Manage app** and read the first installation error in the logs. The generic
   “Error installing requirements” page does not identify the failing package.

If an existing deployment uses a Python version outside the project's supported
range, Streamlit requires recreating the deployment to change Python. Preserve
the app settings and secrets before doing that.

References: [dependency selection](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies),
[deployment settings](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy),
[secrets](https://docs.streamlit.io/develop/concepts/connections/secrets-management),
and [changing Python](https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app/upgrade-python).
