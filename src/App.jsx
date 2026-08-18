import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { adtApi } from "./api";

const CATEGORY_LABEL = {
  value: "Dharma",
  goal: "Goal",
  preference: "True North",
  blind_spot: "Watch-out",
  persona: "Persona",
  role: "Role",
  guardrail: "Guardrail",
  leadership: "Leadership",
  wealth: "Wealth",
  parenting: "Parenting",
};

function Score({ label, value, tone = "gold" }) {
  const v = Math.round(value ?? 0);
  return (
    <div className="score">
      <span>{label}</span>
      <div className="bar"><i className={tone} style={{ width: `${v}%` }} /></div>
      <b>{v}</b>
    </div>
  );
}

function Expert({ name, domain, finding, signal = "neutral" }) {
  return (
    <article className="expert-card">
      <div className="expert-head">
        <div className="avatar">{name.split(" ").map((x) => x[0]).join("").slice(0, 2)}</div>
        <div><b>{name}</b><small>{domain} · independent routing</small></div>
        <span className={`signal ${signal}`}>
          {signal === "support" ? "Supports" : signal === "challenge" ? "Challenges" : "Routed"}
        </span>
      </div>
      <p>{finding}</p>
    </article>
  );
}

export default function App() {
  const [tab, setTab] = useState("brief");
  const [backendOk, setBackendOk] = useState(null);
  const [constitution, setConstitution] = useState([]);
  const [inbox, setInbox] = useState([]);
  const [researchPrograms, setResearchPrograms] = useState([]);
  const [decision, setDecision] = useState(
    "Should I commit the next 12 weeks to the ACA research program while launching the Vaidya Mitra clinical validation cohort?"
  );
  const [analysis, setAnalysis] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [memory, setMemory] = useState([]);
  const [recallQuery, setRecallQuery] = useState("");
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const fileRef = useRef(null);

  const loadAll = useCallback(async () => {
    try {
      await adtApi.health();
      setBackendOk(true);
      const [c, inboxItems, programs, decisions] = await Promise.all([
        adtApi.constitution(),
        adtApi.inbox(),
        adtApi.researchPrograms(),
        adtApi.listDecisions(),
      ]);
      setConstitution(c);
      setInbox(inboxItems);
      setResearchPrograms(programs);
      setMemory(
        decisions.map((d) => ({
          id: d.id,
          type: "Decision",
          title: d.question.slice(0, 76) + (d.question.length > 76 ? "…" : ""),
          detail: d.final_decision || d.recommendation,
          tag: "decision",
          created_at: d.created_at,
        }))
      );
      setError("");
    } catch (e) {
      setBackendOk(false);
      setError("Backend offline — run: cd backend && uvicorn app.main:app --reload --port 8000");
    }
  }, []);

  useEffect(() => {
    loadAll();
  }, [loadAll]);

  const trueNorth = useMemo(() => {
    const item = constitution.find((c) => c.category === "preference");
    return item?.statement || "Diagnose deeply, act sparingly, align with vision, preserve resilience.";
  }, [constitution]);

  const pendingInbox = inbox.filter((i) => i.status === "received" || i.status === "proposed");

  async function runAnalysis() {
    setAnalyzing(true);
    setError("");
    try {
      const result = await adtApi.analyzeDecision(decision);
      setAnalysis(result);
      setNotice("Analysis saved to persistent backend — Constitution, evidence and experts kept separate.");
    } catch (e) {
      setError(e.message);
    } finally {
      setAnalyzing(false);
    }
  }

  async function recordDecision() {
    if (!analysis?.id) return;
    try {
      await adtApi.finalizeDecision(analysis.id, analysis.recommendation);
      await loadAll();
      setNotice("Decision finalized in SQLite vault. ADT will recall it in future sessions.");
    } catch (e) {
      setError(e.message);
    }
  }

  async function handleFileUpload(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      const text = await file.text();
      const ext = file.name.split(".").pop()?.toLowerCase() || "text";
      const contentType = ext === "md" ? "markdown" : ext === "pdf" ? "pdf" : "text";
      await adtApi.addKnowledge({
        title: file.name,
        content_type: contentType,
        summary: text.slice(0, 4000) || `Uploaded file: ${file.name}`,
        source_class: "ajay",
      });
      await loadAll();
      setNotice(`"${file.name}" received — proposed knowledge only. Constitution unchanged.`);
      setTab("inbox");
    } catch (err) {
      setError(err.message);
    } finally {
      e.target.value = "";
    }
  }

  async function acceptItem(id) {
    try {
      await adtApi.reviewKnowledge(id, "accepted");
      await loadAll();
      setNotice("Knowledge accepted — now available for decision retrieval.");
    } catch (e) {
      setError(e.message);
    }
  }

  async function rejectItem(id) {
    try {
      await adtApi.reviewKnowledge(id, "rejected");
      await loadAll();
      setNotice("Knowledge rejected.");
    } catch (e) {
      setError(e.message);
    }
  }

  async function doRecall() {
    try {
      const results = await adtApi.recall(recallQuery);
      setMemory(
        results.map((r) => ({
          id: r.id,
          type: r.memory_type === "decision" ? "Decision" : "Knowledge",
          title: r.title,
          detail: r.created_at ? new Date(r.created_at).toLocaleDateString() : "",
          tag: r.memory_type,
        }))
      );
    } catch (e) {
      setError(e.message);
    }
  }

  const expertCards = (analysis?.experts || []).map((ex) => ({
    name: ex.name,
    domain: ex.protocol || (ex.domains || []).join(", "),
    finding: ex.protocol
      ? `${ex.name} routed independently via ${ex.protocol}. Synthesis occurs only after expert views are recorded.`
      : "Independent expert routed for this decision.",
    signal: ex.id === "dharma_governor" ? "support" : "neutral",
  }));

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand"><span className="brand-mark">A</span><div><b>ADT</b><small>Ajay Digital Twin</small></div></div>
        <nav>
          {[["brief", "⌂", "Today"], ["inbox", "↓", "Knowledge inbox"], ["memory", "◌", "Memory"], ["constitution", "◇", "Constitution"], ["research", "⌁", "Research"]].map(([id, icon, label]) => (
            <button key={id} onClick={() => setTab(id)} className={tab === id ? "active" : ""}>
              <i>{icon}</i>{label}{id === "inbox" && pendingInbox.length ? <em>{pendingInbox.length}</em> : null}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="privacy"><span className={backendOk ? "" : "offline"}>●</span> {backendOk ? "Backend connected" : backendOk === false ? "Backend offline" : "Connecting…"}</div>
          <button className="profile">A <span>Ajay</span><b>⌄</b></button>
        </div>
      </aside>
      <main>
        <header className="top">
          <div>
            <p className="kicker">{new Date().toLocaleDateString("en-IN", { weekday: "long", day: "numeric", month: "long" }).toUpperCase()}</p>
            <h1>{tab === "brief" ? "Good morning, Ajay." : tab === "constitution" ? "Constitution of ADT" : tab === "inbox" ? "Knowledge inbox" : tab === "memory" ? "Memory & recall" : "Research program"}</h1>
          </div>
          <div className="top-actions">
            <button className="quiet" onClick={() => fileRef.current?.click()}>↓ Add knowledge</button>
            <input ref={fileRef} type="file" accept=".md,.txt,.json" hidden onChange={handleFileUpload} />
          </div>
        </header>
        {notice && <div className="notice"><span>✓</span>{notice}<button onClick={() => setNotice("")}>×</button></div>}
        {error && <div className="notice error"><span>!</span>{error}<button onClick={() => setError("")}>×</button></div>}

        {tab === "brief" && (
          <>
            <section className="north-star">
              <div><p className="kicker">TRUE NORTH</p><h2>“{trueNorth.slice(0, 100)}{trueNorth.length > 100 ? "…" : ""}”</h2></div>
              <button onClick={() => setTab("constitution")}>Open Constitution <span>→</span></button>
            </section>
            <section className="signal-row">
              <article><span className="signal-icon gold-dot">✦</span><div><small>CONSTITUTION</small><b>{constitution.length} approved items loaded</b></div><button onClick={() => setTab("constitution")}>Review →</button></article>
              <article><span className="signal-icon blue-dot">⌁</span><div><small>INBOX</small><b>{pendingInbox.length} item(s) awaiting review</b></div><button onClick={() => setTab("inbox")}>Review →</button></article>
            </section>
            <section className="section-title"><div><p className="kicker">DECISION WORKBENCH</p><h2>Think with ADT</h2></div><span>Persistent backend · SQLite vault</span></section>
            <section id="decision" className="workbench">
              <div className="question-box">
                <label>What are you deciding?</label>
                <textarea value={decision} onChange={(e) => { setDecision(e.target.value); setAnalysis(null); }} />
                <div>
                  <span>ADT separates facts, assumptions, values, expert routing and uncertainty.</span>
                  <button className="primary" onClick={runAnalysis} disabled={analyzing || !backendOk}>
                    {analyzing ? "Analyzing…" : "Run decision engine"} <b>→</b>
                  </button>
                </div>
              </div>
              {analysis && (
                <div className="analysis">
                  <div className="analysis-head">
                    <div><small>ANALYSIS COMPLETE · ID {analysis.id?.slice(0, 8)}</small><h3>{analysis.recommendation?.slice(0, 72)}…</h3></div>
                    <span className="confidence">{Math.round((analysis.confidence ?? 0) * 100)}% confidence</span>
                  </div>
                  <p className="recommendation">{analysis.recommendation}</p>
                  <div className="pills">
                    <span>Experts routed: {analysis.experts?.length || 0}</span>
                    {(analysis.aca_risks || []).map((r) => <span key={r}>ACA: {r}</span>)}
                    <span>Uncertainty preserved</span>
                  </div>
                  <div className="decision-grid">
                    <div>
                      <h4>Values applied</h4>
                      {(analysis.values_applied || []).map((v) => <Score key={v} label={v} value={85} />)}
                      {analysis.uncertainty && <p className="uncertainty"><b>Uncertainty:</b> {analysis.uncertainty}</p>}
                    </div>
                    <div className="next">
                      <h4>Next steps</h4>
                      <ol>
                        {(analysis.next_steps || []).map((s, i) => (
                          <li key={i}><b>{s}</b></li>
                        ))}
                      </ol>
                    </div>
                  </div>
                  <div className="analysis-footer">
                    <button className="quiet" onClick={() => setTab("memory")}>View in memory</button>
                    <button className="primary" onClick={recordDecision}>Record my decision →</button>
                  </div>
                </div>
              )}
            </section>
            {expertCards.length > 0 && (
              <>
                <section className="section-title compact"><div><p className="kicker">INDEPENDENT EXPERT ROUTING</p><h2>Useful disagreement is preserved.</h2></div></section>
                <section className="experts">
                  {expertCards.map((e) => <Expert key={e.name} {...e} />)}
                </section>
              </>
            )}
          </>
        )}

        {tab === "inbox" && (
          <section className="inbox-page">
            <div className="upload-zone">
              <span>↓</span>
              <h2>Bring knowledge into the vault</h2>
              <p>Uploads enter as reviewable proposals — never as a silent update to Ajay's constitutional identity.</p>
              <button className="primary" onClick={() => fileRef.current?.click()}>Upload MD / TXT / JSON</button>
            </div>
            {inbox.map((item) => (
              <article key={item.id} className="inbox-item">
                <div className="file-icon">{(item.content_type || "txt").slice(0, 3).toUpperCase()}</div>
                <div>
                  <b>{item.title}</b>
                  <p>{item.source_class} · {item.status} · {item.summary?.slice(0, 100)}…</p>
                </div>
                <span className={item.status === "accepted" ? "accepted" : "proposed"}>{item.status}</span>
                {(item.status === "received" || item.status === "proposed") && (
                  <>
                    <button className="primary" onClick={() => acceptItem(item.id)}>Accept</button>
                    <button className="quiet" onClick={() => rejectItem(item.id)}>Reject</button>
                  </>
                )}
              </article>
            ))}
            <div className="guardrail"><b>Constitutional guardrail</b><span>Web references (NIST AI RMF, HL7 FHIR, clinical AI reviews) are seeded as proposed — accept only after review.</span></div>
          </section>
        )}

        {tab === "constitution" && (
          <section className="constitution-page">
            <div className="version">
              <div><p className="kicker">APPROVED · VERSION 1.0</p><h2>Constitutional memory</h2><p>{constitution.length} items in SQLite. Uploads and web findings cannot change these without explicit amendment approval.</p></div>
            </div>
            <div className="constitution-grid">
              {constitution.map((item) => (
                <article key={item.id}>
                  <span>{CATEGORY_LABEL[item.category] || item.category}</span>
                  <h3>{item.statement.slice(0, 60)}{item.statement.length > 60 ? "…" : ""}</h3>
                  <p>{item.statement}</p>
                  <small>Confirmed by Ajay · v{item.version} · priority {item.priority}</small>
                </article>
              ))}
            </div>
            <div className="amendment">
              <div><b>Need to evolve a constitutional item?</b><p>Propose → rationale → Ajay review → approval → version + changelog.</p></div>
              <button className="primary" onClick={async () => { try { await adtApi.proposeAmendment({ title: "Constitutional amendment", summary: "Proposed via UI — awaiting Ajay review.", source_class: "ajay" }); setNotice("Amendment proposed. Constitution unchanged until approved."); } catch (e) { setError(e.message); } }}>Propose amendment</button>
            </div>
          </section>
        )}

        {tab === "memory" && (
          <section className="memory-page">
            <div className="recall">
              <p className="kicker">FUTURE RECALL</p>
              <h2>What should ADT remember?</h2>
              <div>
                <span>⌕</span>
                <input value={recallQuery} onChange={(e) => setRecallQuery(e.target.value)} placeholder="Search decisions, accepted knowledge…" onKeyDown={(e) => e.key === "Enter" && doRecall()} />
                <button className="primary" onClick={doRecall}>Recall</button>
              </div>
            </div>
            <div className="memory-list">
              {memory.map((item) => (
                <article key={item.id}>
                  <span className={`memory-type ${item.tag}`}>{item.type}</span>
                  <div><b>{item.title}</b><p>{item.detail}</p></div>
                </article>
              ))}
            </div>
            <div className="guardrail"><b>Memory protocol</b><span>Decisions retain reasoning records with evidence, assumptions, experts, disagreements, ACA risks, values and uncertainty.</span></div>
          </section>
        )}

        {tab === "research" && (
          <section className="research-page">
            <p className="kicker">RESEARCH PROGRAMS</p>
            <h2>ACA / AI Faculty Dissociation</h2>
            {researchPrograms.map((p) => (
              <div key={p.id}>
                <p className="research-intro">{p.hypothesis}</p>
                <div className="research-grid">
                  <article><span>01</span><h3>{p.title}</h3><p>{p.next_experiment}</p><b>{p.evidence_status}</b></article>
                  <article><span>02</span><h3>Status</h3><p>{p.status}</p><b>{p.status}</b></article>
                  <article><span>03</span><h3>Next experiment</h3><p>{p.next_experiment}</p><b>Active</b></article>
                </div>
              </div>
            ))}
          </section>
        )}
      </main>
    </div>
  );
}
