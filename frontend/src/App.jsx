import { useEffect, useRef, useState } from "react";
import { askQuestion, clearHistory, getDocuments, getHistory, uploadDocument } from "./api.js";

const EXAMPLES = [
  "What is the annual deductible?",
  "How do I appeal a denied claim?",
  "How much is a tier 2 drug?",
];

function Sources({ sources }) {
  if (!sources?.length) return null;
  return (
    <div className="mt-3 space-y-2">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Sources</p>
      {sources.map((s, i) => (
        <details key={i} className="rounded-lg border border-slate-200 bg-slate-50 p-2 text-sm">
          <summary className="cursor-pointer text-slate-700">
            [{i + 1}] {s.doc} <span className="text-slate-400">(match {Math.round(s.score * 100)}%)</span>
          </summary>
          <p className="mt-2 whitespace-pre-wrap text-slate-600">{s.text}</p>
        </details>
      ))}
    </div>
  );
}

export default function App() {
  const [docs, setDocs] = useState([]);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const bottomRef = useRef(null);

  useEffect(() => {
    getDocuments().then(setDocs).catch((e) => setError(e.message));
    getHistory()
      .then((rows) =>
        setMessages(
          rows.flatMap((r) => [
            { role: "user", text: r.question },
            { role: "assistant", text: r.answer, sources: r.sources },
          ])
        )
      )
      .catch(() => {});
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function send(question) {
    const q = question.trim();
    if (q.length < 3 || loading) return;
    setError("");
    setInput("");
    setMessages((m) => [...m, { role: "user", text: q }]);
    setLoading(true);
    try {
      const res = await askQuestion(q);
      setMessages((m) => [...m, { role: "assistant", text: res.answer, sources: res.sources }]);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function onUpload(e) {
    const file = e.target.files[0];
    if (!file) return;
    setError("");
    try {
      setDocs(await uploadDocument(file));
    } catch (err) {
      setError(err.message);
    }
    e.target.value = "";
  }

  async function onClear() {
    await clearHistory();
    setMessages([]);
  }

  return (
    <div className="mx-auto flex h-screen max-w-6xl flex-col gap-4 p-4 md:flex-row">
      <aside className="w-full shrink-0 rounded-2xl bg-white p-4 shadow md:w-72">
        <h1 className="text-xl font-bold text-orange-600">MediAssist</h1>
        <p className="mt-1 text-sm text-slate-500">Ask questions about health-plan documents and get cited answers.</p>

        <h2 className="mt-5 text-sm font-semibold text-slate-700">Documents ({docs.length})</h2>
        <ul className="mt-2 max-h-40 space-y-1 overflow-y-auto text-sm text-slate-600">
          {docs.map((d) => (
            <li key={d.name} className="truncate">• {d.name}</li>
          ))}
        </ul>

        <label className="mt-3 block cursor-pointer rounded-lg border border-dashed border-slate-300 p-3 text-center text-sm text-slate-600 hover:bg-slate-50">
          + Upload .txt / .md / .pdf
          <input type="file" accept=".txt,.md,.pdf" className="hidden" onChange={onUpload} />
        </label>

        <button onClick={onClear} className="mt-3 text-sm text-slate-500 underline hover:text-slate-700">
          Clear chat history
        </button>

        <p className="mt-5 rounded-lg bg-amber-50 p-2 text-xs text-amber-800">
          Demo with synthetic data only. Do not upload real personal or patient information. Not medical or insurance advice.
        </p>
      </aside>

      <main className="flex min-h-0 flex-1 flex-col rounded-2xl bg-white shadow">
        <div className="flex-1 space-y-4 overflow-y-auto p-4">
          {messages.length === 0 && (
            <div className="mt-10 text-center text-slate-500">
              <p className="mb-3">Try a question:</p>
              <div className="flex flex-wrap justify-center gap-2">
                {EXAMPLES.map((q) => (
                  <button key={q} onClick={() => send(q)} className="rounded-full border border-slate-300 px-3 py-1 text-sm hover:bg-slate-50">
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}
          {messages.map((m, i) => (
            <div key={i} className={m.role === "user" ? "flex justify-end" : "flex justify-start"}>
              <div className={`max-w-[85%] rounded-2xl px-4 py-3 ${m.role === "user" ? "bg-orange-600 text-white" : "bg-slate-100 text-slate-800"}`}>
                <p className="whitespace-pre-wrap">{m.text}</p>
                {m.role === "assistant" && <Sources sources={m.sources} />}
              </div>
            </div>
          ))}
          {loading && <p className="text-sm text-slate-400">Searching documents…</p>}
          <div ref={bottomRef} />
        </div>

        {error && <p className="px-4 pb-1 text-sm text-red-600">{error}</p>}
        <form
          className="flex gap-2 border-t border-slate-200 p-3"
          onSubmit={(e) => {
            e.preventDefault();
            send(input);
          }}
        >
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about deductibles, copays, claims, prescriptions…"
            className="flex-1 rounded-xl border border-slate-300 px-4 py-2 outline-none focus:border-orange-500"
          />
          <button disabled={loading} className="rounded-xl bg-orange-600 px-5 py-2 font-medium text-white hover:bg-orange-700 disabled:opacity-50">
            Ask
          </button>
        </form>
      </main>
    </div>
  );
}
