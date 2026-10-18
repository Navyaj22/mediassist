# MediAssist - Healthcare Document Q&A Assistant

A full-stack Retrieval-Augmented Generation (RAG) app. Ask questions in plain English about
health-plan documents and get an answer with the exact source passages cited.

> Uses **synthetic sample data only**. No real patient or personal information. Not medical or insurance advice.

## How it works

```
React + Tailwind UI  --/api-->  FastAPI backend
                                  |-- chunk documents (txt / md / pdf)
                                  |-- TF-IDF retrieval (scikit-learn) -> top 3 passages
                                  |-- LLM (Anthropic API) answers from those passages only, cites [1], [2]
                                  `-- SQLite stores chat history
```

1. Documents are split into ~70-word chunks and indexed with TF-IDF (unigrams + bigrams).
2. A question is matched to the most similar chunks by cosine similarity.
3. If no chunk is relevant enough, the app says the answer is not in the documents instead of guessing.
4. Otherwise the passages go to an LLM with instructions to answer only from them and cite sources.
   Without an API key the app still works and shows the best matching passage.

## Responsible AI
- Answers are grounded in the provided documents only, with the source passage shown for verification.
- Out-of-scope questions are declined rather than answered from the model's general knowledge.
- Synthetic data only; the UI warns users not to upload personal information.
- Uploads are limited to .txt, .md and .pdf files up to 2 MB.

## Run locally

**Backend** (Python 3.10+)
```bash
cd backend
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your_key_here                # optional, enables generated answers
uvicorn main:app --reload
```

**Frontend** (Node 18+), in a second terminal
```bash
cd frontend
npm install
npm run dev        # open http://localhost:5173
```

**Tests**
```bash
cd backend && pytest -q
```

## API
| Method | Path | Purpose |
|---|---|---|
| GET | /api/health | Health check |
| GET | /api/documents | List indexed documents |
| POST | /api/documents | Upload a document and re-index |
| POST | /api/chat | Ask a question, returns answer + sources |
| GET / DELETE | /api/history | Read / clear chat history |

## Tech stack
Python, FastAPI, scikit-learn, SQLite, Anthropic API, React, Vite, TailwindCSS, pytest, GitHub Actions.

## Possible next steps
Swap TF-IDF for embeddings + a vector store (FAISS/Chroma), add streaming responses, and add user authentication.
