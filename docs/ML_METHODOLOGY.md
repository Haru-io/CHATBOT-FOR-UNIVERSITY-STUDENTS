# ML/NLP Methodology

## 1. Dataset
The supplied e-learning FAQ dataset contains 427 English questions, 79 answer records and 11 categories. The raw CSV contains some malformed quoting; the preprocessing script uses a robust line parser and normalizes the answer/category relationships.

## 2. Label
The primary supervised label is the category/intent (for example Documents, Assignments, Registration, Login). Answer IDs are retained as retrieval metadata rather than used as the main class label.

## 3. Preprocessing
- Normalize whitespace and HTML markup.
- Resolve Question → Answer → Category mappings.
- Remove malformed/unmapped rows only when the relationship cannot be recovered.
- Split by category with a fixed random seed.

## 4. Model
Baseline intent classifier: TF-IDF word n-grams (1–2) + Logistic Regression with class balancing.

## 5. Retrieval
The baseline RAG retriever indexes question + answer pairs and institution documents. Retrieval uses TF-IDF cosine similarity. This is intentionally lightweight; Sentence Transformers + FAISS/Chroma can be substituted for the final version.

## 6. Generation
If Ollama is enabled, retrieved context is passed to a local LLM with a grounding prompt. If no LLM is available, the system returns the best retrieved evidence instead of inventing an answer.

## 7. Evaluation
Evaluate intent accuracy/F1, retrieval Recall@k/Precision@k, answer correctness/groundedness, latency and user feedback.
