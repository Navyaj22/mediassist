"""MediAssist API: upload documents, ask questions, get cited answers."""
import re
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import db
import rag

MAX_UPLOAD = 2 * 1024 * 1024  # 2 MB


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    rag.index.build()
    yield


app = FastAPI(title="MediAssist", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)


@app.get("/api/health")
def health():
    return {"status": "ok", "documents": len(rag.index.documents())}


@app.get("/api/documents")
def list_documents():
    return rag.index.documents()


@app.post("/api/documents")
async def upload_document(file: UploadFile = File(...)):
    name = re.sub(r"[^A-Za-z0-9._-]", "_", file.filename or "upload")
    suffix = "." + name.rsplit(".", 1)[-1].lower() if "." in name else ""
    if suffix not in rag.ALLOWED:
        raise HTTPException(400, "Only .txt, .md and .pdf files are supported.")
    data = await file.read()
    if len(data) > MAX_UPLOAD:
        raise HTTPException(400, "File is too large (limit 2 MB).")
    rag.DOCS_DIR.mkdir(parents=True, exist_ok=True)
    (rag.DOCS_DIR / name).write_bytes(data)
    rag.index.build()
    return rag.index.documents()


@app.post("/api/chat")
def chat(req: ChatRequest):
    hits = rag.index.search(req.question)
    answer, mode = rag.generate_answer(req.question, hits)
    db.save_chat(req.question, answer, hits)
    return {"answer": answer, "sources": hits, "mode": mode}


@app.get("/api/history")
def history():
    return db.get_history()


@app.delete("/api/history")
def delete_history():
    db.clear_history()
    return {"cleared": True}
