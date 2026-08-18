const API = import.meta.env.VITE_API_URL || "";

async function request(path, options = {}) {
  const headers = { Accept: "application/json" };
  if (options.body && !(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }
  const res = await fetch(`${API}${path}`, { ...options, headers: { ...headers, ...options.headers } });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || `Request failed (${res.status})`);
  }
  if (res.status === 204) return null;
  return res.json();
}

export const adtApi = {
  health: () => request("/health"),
  constitution: () => request("/v1/constitution"),
  experts: () => request("/v1/experts"),
  routeExperts: (query, highRisk = false) =>
    request("/v1/experts/route", {
      method: "POST",
      body: JSON.stringify({ query, high_risk: highRisk }),
    }),
  inbox: () => request("/v1/inbox"),
  addKnowledge: (payload) =>
    request("/v1/inbox", { method: "POST", body: JSON.stringify(payload) }),
  reviewKnowledge: (id, action) =>
    request(`/v1/inbox/${id}/review?action=${action}`, { method: "POST" }),
  searchKnowledge: (q, includeProposed = false) =>
    request(`/v1/knowledge/search?q=${encodeURIComponent(q)}&include_proposed=${includeProposed}`),
  analyzeDecision: (question, context = {}) =>
    request("/v1/decisions/analyze", {
      method: "POST",
      body: JSON.stringify({ question, context }),
    }),
  listDecisions: () => request("/v1/decisions"),
  finalizeDecision: (id, final_decision) =>
    request(`/v1/decisions/${id}/finalize`, {
      method: "POST",
      body: JSON.stringify({ final_decision }),
    }),
  reasoningRecord: (id) => request(`/v1/decisions/${id}/reasoning-record`),
  recall: (q = "") => request(`/v1/memories/recall?q=${encodeURIComponent(q)}`),
  researchPrograms: () => request("/v1/research/programs"),
  driftCheck: () => request("/v1/governance/drift-check"),
  proposeAmendment: (payload) =>
    request("/v1/constitution/amendments", { method: "POST", body: JSON.stringify(payload) }),
};
