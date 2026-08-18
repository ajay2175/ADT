const API = import.meta.env.VITE_API_URL || "";

async function request(path, options = {}) {
  const headers = { Accept: "application/json" };
  if (options.body && !(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }
  const res = await fetch(`${API}${path}`, { ...options, headers: { ...headers, ...options.headers } });
  if (!res.ok) throw new Error(await res.text() || `HTTP ${res.status}`);
  return res.json();
}

export const adtApi = {
  health: () => request("/health"),
  constitution: () => request("/v1/constitution"),
  experts: () => request("/v1/experts"),
  inbox: () => request("/v1/inbox"),
  uploadFile: (file, sourceClass = "ajay") => {
    const form = new FormData();
    form.append("file", file);
    return request(`/v1/inbox/upload?source_class=${sourceClass}`, { method: "POST", body: form });
  },
  addKnowledge: (payload) => request("/v1/inbox", { method: "POST", body: JSON.stringify(payload) }),
  reviewKnowledge: (id, action) => request(`/v1/inbox/${id}/review?action=${action}`, { method: "POST" }),
  searchKnowledge: (q) => request(`/v1/knowledge/search?q=${encodeURIComponent(q)}`),
  analyzeDecision: (question, context = {}) =>
    request("/v1/decisions/analyze", { method: "POST", body: JSON.stringify({ question, context }) }),
  listDecisions: () => request("/v1/decisions"),
  finalizeDecision: (id, final_decision) =>
    request(`/v1/decisions/${id}/finalize`, { method: "POST", body: JSON.stringify({ final_decision }) }),
  reasoningRecord: (id) => request(`/v1/decisions/${id}/reasoning-record`),
  recall: (q = "") => request(`/v1/memories/recall?q=${encodeURIComponent(q)}`),
  researchPrograms: () => request("/v1/research/programs"),
  driftCheck: (question = "", context = {}) =>
    request("/v1/governance/drift-check", { method: "POST", body: JSON.stringify({ question, context }) }),
  proposeAmendment: (payload) =>
    request("/v1/constitution/amendments", { method: "POST", body: JSON.stringify(payload) }),
  chat: (message) => request("/v1/chat", { method: "POST", body: JSON.stringify({ message }) }),
};
