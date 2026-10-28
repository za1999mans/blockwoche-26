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

The app requires `data/hs_vector_index.sqlite3` at startup. That file is currently
ignored by Git, so a normal push does not deploy it. Without it, the app stops
with “Die Hochschulinformationen werden noch vorbereitet.”

For a deployment with the existing index, check its status locally:

```bash
poetry run python index_hs_data.py status
```

If `ready` is true, explicitly include this existing database in the deployment
commit:

```bash
git add -f data/hs_vector_index.sqlite3
```

This reuses the existing document embeddings. Keep `HS_DATA/_rag/chunks.jsonl`
in the repository as well. Alternatively, supply the database through your
hosting setup and set `HS_RAG_DB` to its path. The app does not build a missing
index automatically.

## Configure secrets and deploy

1. Commit and push the dependency fixes, the app modules (including
   `hs_dialogue.py` and `hs_voice.py`), the corpus, and the index to the branch
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
