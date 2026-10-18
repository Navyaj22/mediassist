import os
import sys
import tempfile

os.environ["MEDIASSIST_DB"] = os.path.join(tempfile.mkdtemp(), "test.db")
os.environ.pop("ANTHROPIC_API_KEY", None)
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi.testclient import TestClient  # noqa: E402

from main import app  # noqa: E402


def test_health_and_documents():
    with TestClient(app) as client:
        assert client.get("/api/health").json()["status"] == "ok"
        assert len(client.get("/api/documents").json()) >= 3


def test_answer_has_cited_source():
    with TestClient(app) as client:
        r = client.post("/api/chat", json={"question": "What is the annual deductible?"}).json()
        assert r["sources"], "expected at least one source"
        assert r["sources"][0]["doc"] == "plan_summary.md"
        assert "500" in r["sources"][0]["text"] or "deductible" in r["sources"][0]["text"].lower()


def test_unrelated_question_is_not_answered():
    with TestClient(app) as client:
        r = client.post("/api/chat", json={"question": "best pizza recipe with mushrooms"}).json()
        assert r["sources"] == []
        assert r["mode"] == "none"


def test_history_saved_and_cleared():
    with TestClient(app) as client:
        client.post("/api/chat", json={"question": "How do I appeal a denied claim?"})
        assert len(client.get("/api/history").json()) >= 1
        client.delete("/api/history")
        assert client.get("/api/history").json() == []


def test_rejects_bad_upload():
    with TestClient(app) as client:
        r = client.post("/api/documents", files={"file": ("x.exe", b"hi")})
        assert r.status_code == 400
