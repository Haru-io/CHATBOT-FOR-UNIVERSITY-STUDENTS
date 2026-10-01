# P_200 — AI-Powered Chatbot for University Student Support

A prototype/MVP implementing the planned P_200 architecture: React frontend, Node/Express backend, Python/FastAPI AI service, NLP intent classification, retrieval-augmented answering, authentication, chat history, feedback and admin document upload.

## Important data note
The supplied Zenodo e-learning dataset is used as a **research/NLP baseline**. It is not your university's official policy data. Before a real university deployment, replace/add approved university documents in `knowledge-base/documents/` and verify all institutional answers.

## Architecture
```text
React/Vite → Node/Express → FastAPI AI service
                         ↘ intent classifier
                          ↘ RAG retrieval → optional Ollama LLM
MongoDB is the planned production database; this prototype uses JSON persistence so it can run without MongoDB.
```

## Prerequisites
- Node.js 20+
- Python 3.11+ (3.13 should work with the pinned packages)
- Optional: MongoDB for a production persistence implementation
- Optional: Ollama for local generative answers

## 1) Start AI service
```powershell
cd ai-service
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## 2) Start backend
Open a second terminal:
```powershell
cd backend
npm install
copy .env.example .env
npm run seed:admin
npm run dev
```

Default admin created by the seed command:
- Email: `admin@p200.local`
- Password: `Admin@12345`

Change these before any real deployment.

## 3) Start frontend
Open a third terminal:
```powershell
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173`.

## Optional local LLM
If Ollama is installed and a model is available, set in the AI-service environment:
```text
ENABLE_OLLAMA=true
OLLAMA_MODEL=llama3.2:3b
```
The baseline still works without Ollama: it returns the best retrieved evidence and exposes sources.

## Project phases represented in this codebase
1. Dataset cleaning and category/intent preparation
2. NLP intent classifier
3. Retrieval/RAG knowledge base
4. AI service API
5. Node/Express authentication and chat API
6. React student interface
7. Admin document upload/re-indexing
8. Feedback and chat history

## Production improvements
- Replace JSON store with MongoDB/Mongoose repositories.
- Use a stronger embedding model/vector database for larger institutional corpora.
- Add proper document versioning and access controls.
- Add automated evaluation and monitoring.
- Use official university documents and approval workflows.
