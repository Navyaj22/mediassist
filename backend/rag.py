"""Retrieval-Augmented Generation: chunk documents, retrieve with TF-IDF, answer with citations."""
import os
import re
from dataclasses import dataclass
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

DOCS_DIR = Path(os.getenv("MEDIASSIST_DOCS", Path(__file__).parent / "documents"))
ALLOWED = {".txt", ".md", ".pdf"}
MIN_SCORE = 0.05  # below this, we say the answer is not in the documents

SYSTEM_PROMPT = (
    "You are MediAssist, an assistant that answers questions about health-insurance "
    "documents. Answer ONLY using the numbered context passages. Cite the passages you "
    "use like [1] or [2]. If the answer is not in the passages, say you could not find "
    "it in the provided documents. Do not give medical or legal advice. Be concise."
)


@dataclass
class Chunk:
    doc: str
    text: str


def read_file(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        from pypdf import PdfReader

        return "\n\n".join((p.extract_text() or "") for p in PdfReader(str(path)).pages)
    return path.read_text(encoding="utf-8", errors="ignore")


def chunk_text(text: str, max_words: int = 70) -> list[str]:
    """Group paragraphs into chunks of about max_words; split very long paragraphs."""
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks, cur, count = [], [], 0
    for p in paras:
        words = p.split()
        if len(words) > max_words:
            if cur:
                chunks.append("\n".join(cur))
                cur, count = [], 0
            for i in range(0, len(words), max_words):
                chunks.append(" ".join(words[i : i + max_words]))
            continue
        if count + len(words) > max_words and cur:
            chunks.append("\n".join(cur))
            cur, count = [], 0
        cur.append(p)
        count += len(words)
    if cur:
        chunks.append("\n".join(cur))
    return chunks


class Index:
    def __init__(self):
        self.chunks: list[Chunk] = []
        self.vectorizer = None
        self.matrix = None

    def build(self):
        DOCS_DIR.mkdir(parents=True, exist_ok=True)
        self.chunks = []
        for path in sorted(DOCS_DIR.iterdir()):
            if path.suffix.lower() in ALLOWED:
                for piece in chunk_text(read_file(path)):
                    self.chunks.append(Chunk(path.name, piece))
        if self.chunks:
            self.vectorizer = TfidfVectorizer(
                stop_words="english", ngram_range=(1, 2), sublinear_tf=True
            )
            self.matrix = self.vectorizer.fit_transform([c.text for c in self.chunks])
        else:
            self.vectorizer = self.matrix = None

    def documents(self) -> list[dict]:
        names = sorted({c.doc for c in self.chunks})
        return [
            {"name": n, "chunks": sum(1 for c in self.chunks if c.doc == n)} for n in names
        ]

    def search(self, question: str, k: int = 3) -> list[dict]:
        if self.vectorizer is None:
            return []
        scores = cosine_similarity(self.vectorizer.transform([question]), self.matrix)[0]
        order = scores.argsort()[::-1][:k]
        return [
            {"doc": self.chunks[i].doc, "text": self.chunks[i].text, "score": round(float(scores[i]), 3)}
            for i in order
            if scores[i] >= MIN_SCORE
        ]


def generate_answer(question: str, hits: list[dict]) -> tuple[str, str]:
    """Return (answer, mode). Uses the Anthropic API if a key is set, else shows the best passage."""
    if not hits:
        return (
            "I could not find that in the provided documents. Try rephrasing, or upload a document that covers it.",
            "none",
        )
    if os.getenv("ANTHROPIC_API_KEY"):
        try:
            from anthropic import Anthropic

            context = "\n\n".join(f"[{i + 1}] ({h['doc']}) {h['text']}" for i, h in enumerate(hits))
            msg = Anthropic().messages.create(
                model=os.getenv("MEDIASSIST_MODEL", "claude-sonnet-5-5"),
                max_tokens=500,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}],
            )
            return msg.content[0].text, "llm"
        except Exception as exc:  # fall back so the app still works
            print("LLM call failed, using extractive answer:", exc)
    top = hits[0]
    return (
        f"Most relevant passage from {top['doc']}:\n\n{top['text']}\n\n"
        "(Set ANTHROPIC_API_KEY to get a written answer generated from the passages.)",
        "extractive",
    )


index = Index()
