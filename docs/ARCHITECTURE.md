# P_200 Architecture

```text
Student
  ↓
React/Vite Web App
  ↓ HTTP/JSON
Node/Express Backend
  ├── Authentication / Sessions / Feedback
  ├── Admin document upload
  ↓
Python/FastAPI AI Service
  ├── Intent classifier: TF-IDF + Logistic Regression
  ├── Query retrieval: TF-IDF cosine similarity (baseline)
  ├── Knowledge base ingestion/chunking
  └── Optional local LLM via Ollama
  ↓
Research dataset + institution documents
```

## Production evolution
The baseline retrieval layer can be replaced by Sentence Transformers + FAISS/Chroma without changing the frontend API. The current implementation deliberately keeps a lightweight fallback so the prototype can run on a normal student laptop.
