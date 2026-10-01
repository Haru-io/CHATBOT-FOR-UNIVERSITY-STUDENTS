from __future__ import annotations

import csv
import os
import re
from pathlib import Path
from typing import Any

import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics.pairwise import cosine_similarity


# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).resolve().parents[2]

# ML dataset — used ONLY for intent classification
PROC = ROOT / "dataset" / "processed"

# ABES Knowledge Base — used ONLY for RAG retrieval
KB = ROOT / "knowledge-base" / "abes"

MODEL_DIR = Path(__file__).resolve().parent / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

KB.mkdir(parents=True, exist_ok=True)


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="P_200 AI Service",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# GLOBAL MODELS
# ============================================================

classifier = None
classifier_vectorizer = None

retriever_vectorizer = None
retriever_matrix = None
retriever_docs: list[dict[str, Any]] = []


# ============================================================
# REQUEST / RESPONSE MODELS
# ============================================================

class ChatRequest(BaseModel):
    message: str = Field(
        min_length=2,
        max_length=2000
    )

    top_k: int = Field(
        default=3,
        ge=1,
        le=8
    )


class ChatResponse(BaseModel):
    answer: str
    intent: str
    confidence: float
    sources: list[dict[str, Any]]
    provider: str


# ============================================================
# TEXT CLEANING
# ============================================================

def clean_text(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# ============================================================
# ML DATASET
# ============================================================

def load_train_data():
    """
    Loads the research/ML dataset.

    This dataset is ONLY used for intent classification.
    It is NOT used as the ABES knowledge base.
    """

    path = PROC / "train.csv"

    texts = []
    labels = []

    with path.open(
        encoding="utf-8-sig",
        newline=""
    ) as f:

        for row in csv.DictReader(f):

            texts.append(
                clean_text(row["text"])
            )

            labels.append(
                row["intent"]
            )

    return texts, labels


# ============================================================
# TRAIN INTENT CLASSIFIER
# ============================================================

def train_classifier():

    global classifier
    global classifier_vectorizer

    texts, labels = load_train_data()

    classifier_vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),
        min_df=1,
        sublinear_tf=True
    )

    X = classifier_vectorizer.fit_transform(texts)

    classifier = LogisticRegression(
        max_iter=2500,
        class_weight="balanced"
    )

    classifier.fit(X, labels)


# ============================================================
# CHUNK TEXT
# ============================================================

def chunk_text(
    text: str,
    size: int,
    overlap: int
) -> list[str]:

    words = text.split()

    chunks = []

    start = 0

    while start < len(words):

        end = min(
            len(words),
            start + size
        )

        chunks.append(
            " ".join(words[start:end])
        )

        if end == len(words):
            break

        start = max(
            0,
            end - overlap
        )

    return chunks


# ============================================================
# LOAD ABES KNOWLEDGE BASE
# ============================================================

def load_rag_documents() -> list[dict[str, Any]]:

    docs: list[dict[str, Any]] = []

    # --------------------------------------------------------
    # Read ONLY from:
    #
    # knowledge-base/abes/
    #
    # Research dataset is intentionally NOT loaded here.
    # --------------------------------------------------------

    for path in sorted(KB.rglob("*")):

        if not path.is_file():
            continue

        if path.name.startswith("."):
            continue

        suffix = path.suffix.lower()

        try:

            # ------------------------------------------------
            # TXT / MARKDOWN
            # ------------------------------------------------

            if suffix in {".txt", ".md"}:

                text = path.read_text(
                    encoding="utf-8",
                    errors="ignore"
                )

            # ------------------------------------------------
            # JSON
            # ------------------------------------------------

            elif suffix == ".json":

                import json

                data = json.loads(
                    path.read_text(
                        encoding="utf-8"
                    )
                )

                if isinstance(data, list):

                    for idx, item in enumerate(data):

                        if not isinstance(item, dict):
                            continue

                        answer = clean_text(
                            str(
                                item.get(
                                    "answer",
                                    item.get(
                                        "text",
                                        ""
                                    )
                                )
                            )
                        )

                        if not answer:
                            continue

                        docs.append(
                            {
                                "id": f"{path.stem}-{idx}",

                                "text": answer,

                                "source": str(
                                    path.relative_to(KB)
                                ),

                                "category": item.get(
                                    "category",
                                    "ABES Knowledge Base"
                                )
                            }
                        )

                    continue

                text = json.dumps(
                    data,
                    ensure_ascii=False
                )

            # ------------------------------------------------
            # PDF
            # ------------------------------------------------

            elif suffix == ".pdf":

                try:

                    from pypdf import PdfReader

                    reader = PdfReader(
                        str(path)
                    )

                    text = "\n".join(
                        (
                            page.extract_text()
                            or ""
                        )
                        for page in reader.pages
                    )

                except Exception:

                    continue

            else:

                continue

            # ------------------------------------------------
            # CLEAN TEXT
            # ------------------------------------------------

            text = clean_text(text)

            if not text:
                continue

            # ------------------------------------------------
            # CREATE CHUNKS
            # ------------------------------------------------

            chunks = chunk_text(
                text,
                900,
                120
            )

            for i, chunk in enumerate(chunks):

                docs.append(
                    {
                        "id": f"{path.stem}-{i}",

                        "text": chunk,

                        "source": str(
                            path.relative_to(KB)
                        ),

                        "category": "ABES Knowledge Base"
                    }
                )

        except Exception as error:

            print(
                f"Could not load {path}: {error}"
            )

            continue

    return docs


# ============================================================
# BUILD RETRIEVER
# ============================================================

def build_retriever():

    global retriever_vectorizer
    global retriever_matrix
    global retriever_docs

    print(
        "\nLoading ABES Knowledge Base..."
    )

    retriever_docs = load_rag_documents()

    if not retriever_docs:

        retriever_docs = [
            {
                "id": "fallback",

                "text": (
                    "No ABES knowledge-base content "
                    "is currently indexed."
                ),

                "source": "system",

                "category": "System"
            }
        ]

    retriever_vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),
        sublinear_tf=True,
        min_df=1
    )

    retriever_matrix = (
        retriever_vectorizer.fit_transform(
            [
                d["text"]
                for d in retriever_docs
            ]
        )
    )

    print(
        f"ABES Knowledge Base loaded: "
        f"{len(retriever_docs)} documents/chunks"
    )


# ============================================================
# RETRIEVE RELEVANT DOCUMENTS
# ============================================================

def retrieve(
    query: str,
    top_k: int
):

    q = retriever_vectorizer.transform(
        [
            clean_text(query)
        ]
    )

    scores = cosine_similarity(
        q,
        retriever_matrix
    )[0]

    indices = scores.argsort()[::-1][:top_k]

    return [
        (
            retriever_docs[i],
            float(scores[i])
        )
        for i in indices
    ]


# ============================================================
# CLASSIFY USER QUERY
# ============================================================

def classify(query: str):

    X = classifier_vectorizer.transform(
        [
            clean_text(query)
        ]
    )

    probs = classifier.predict_proba(X)[0]

    idx = probs.argmax()

    return (
        classifier.classes_[idx],
        float(probs[idx])
    )


# ============================================================
# OPTIONAL OLLAMA
# ============================================================

def generate_with_ollama(
    query: str,
    context: list[
        tuple[
            dict[str, Any],
            float
        ]
    ]
) -> str | None:

    base = os.getenv(
        "OLLAMA_BASE_URL",
        "http://localhost:11434"
    ).rstrip("/")

    model = os.getenv(
        "OLLAMA_MODEL",
        "llama3.2:3b"
    )

    if (
        os.getenv(
            "ENABLE_OLLAMA",
            "false"
        ).lower()
        != "true"
    ):
        return None

    context_text = "\n\n".join(
        f"SOURCE: {d['source']}\n{d['text']}"
        for d, _ in context
    )

    prompt = (
        "You are P_200, a university "
        "student-support assistant for ABES "
        "Engineering College.\n\n"

        "Answer ONLY using the supplied "
        "ABES knowledge-base context.\n\n"

        "If the context does not contain enough "
        "evidence, clearly say that the information "
        "is not available and advise the student "
        "to check the official ABES source.\n\n"

        "Do not invent fees, deadlines, rules, "
        "eligibility requirements or statistics.\n\n"

        f"QUESTION:\n{query}\n\n"

        f"CONTEXT:\n{context_text}"
    )

    try:

        response = requests.post(
            f"{base}/api/generate",

            json={
                "model": model,
                "prompt": prompt,
                "stream": False
            },

            timeout=45
        )

        response.raise_for_status()

        return (
            response
            .json()
            .get("response", "")
            .strip()
            or None
        )

    except Exception:

        return None


# ============================================================
# FALLBACK ANSWER
# ============================================================

def fallback_answer(context):

    if (
        not context
        or context[0][1] < 0.08
    ):

        return (
            "I could not find enough evidence "
            "in the ABES knowledge base to answer "
            "this confidently. Please check the "
            "official ABES source or add the "
            "relevant document to the knowledge base."
        )

    return context[0][0]["text"]


# ============================================================
# STARTUP
# ============================================================

@app.on_event("startup")
def startup():

    print(
        "\n========================================"
    )

    print(
        "Starting P_200 AI Service"
    )

    print(
        "========================================"
    )

    # Train ML intent classifier
    train_classifier()

    # Build ABES RAG retriever
    build_retriever()

    print(
        "P_200 AI Service ready."
    )


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():

    return {
        "status": "ok",

        "service": "ai-service",

        "documents": len(
            retriever_docs
        ),

        "knowledge_base": "ABES",

        "model": (
            "TF-IDF + "
            "LogisticRegression + "
            "ABES RAG retrieval"
        )
    }


# ============================================================
# CHAT
# ============================================================

@app.post(
    "/chat",
    response_model=ChatResponse
)
def chat(
    payload: ChatRequest
):

    # --------------------------------------------
    # 1. Intent classification
    # --------------------------------------------

    intent, confidence = classify(
        payload.message
    )

    # --------------------------------------------
    # 2. Retrieve ABES information
    # --------------------------------------------

    results = retrieve(
        payload.message,
        payload.top_k
    )

    # --------------------------------------------
    # 3. Optional Ollama generation
    # --------------------------------------------

    answer = generate_with_ollama(
        payload.message,
        results
    )

    # --------------------------------------------
    # 4. Fallback to retrieved ABES content
    # --------------------------------------------

    provider = (
        "ollama"
        if answer
        else "abes-retrieval"
    )

    if not answer:

        answer = fallback_answer(
            results
        )

    # --------------------------------------------
    # 5. Sources
    # --------------------------------------------

    sources = [

        {
            "id": d["id"],

            "source": d["source"],

            "category": d.get(
                "category",
                ""
            ),

            "score": round(
                score,
                4
            )
        }

        for d, score in results

        if score > 0
    ]

    # --------------------------------------------
    # 6. Response
    # --------------------------------------------

    return ChatResponse(

        answer=answer,

        intent=intent,

        confidence=round(
            confidence,
            4
        ),

        sources=sources,

        provider=provider
    )


# ============================================================
# REINDEX
# ============================================================

@app.post("/reindex")
def reindex():

    build_retriever()

    return {

        "status": "ok",

        "knowledge_base": "ABES",

        "documents": len(
            retriever_docs
        )
    }