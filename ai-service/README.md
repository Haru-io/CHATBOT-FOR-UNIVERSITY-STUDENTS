# P_200 AI Service

FastAPI service for intent classification and retrieval-augmented university support.

## Baseline
- Intent classifier: TF-IDF + Logistic Regression.
- Retrieval: TF-IDF cosine similarity.
- Optional generation: local Ollama (`ENABLE_OLLAMA=true`).
- Knowledge sources: processed research dataset plus files placed in `knowledge-base/documents`.

## Run
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

The baseline works without an LLM API. If Ollama is installed locally, set `ENABLE_OLLAMA=true` and configure `OLLAMA_MODEL`.
