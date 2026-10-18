async function request(path, options) {
  const res = await fetch(`/api${path}`, options);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed (${res.status})`);
  }
  return res.json();
}

export const getDocuments = () => request("/documents");
export const getHistory = () => request("/history");
export const clearHistory = () => request("/history", { method: "DELETE" });
export const askQuestion = (question) =>
  request("/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
export const uploadDocument = (file) => {
  const form = new FormData();
  form.append("file", file);
  return request("/documents", { method: "POST", body: form });
};
