import React, { useMemo, useState } from "react";

const constitution = [
  ["Dharma", "Primary compass", "Act with courage, clarity and responsibility; do not attach to untested conclusions."],
  ["Leadership", "Build capability in others", "Remove fear, anger, grief and guilt from the environment of one’s people."],
  ["Decision", "Diagnose deeply; act sparingly", "Protect optionality, resilience, people and the long horizon."],
  ["Known watch-out", "Overextension", "Check delegation, energy load and family-role impact before committing."],
];

const seedMemory = [
  { type: "Decision", title: "Research platform direction", detail: "Dated 12 Aug · Review due in 30 days", tag: "decision" },
  { type: "Knowledge", title: "ACA / AI faculty-dissociation findings", detail: "Research · supported / replication pending", tag: "research" },
  { type: "Experience", title: "Vaidya Mitra: validation before scale", detail: "Ajay knowledge · accepted", tag: "experience" },
];

function Score({ label, value, tone = "gold" }) {
  return <div className="score"><span>{label}</span><div className="bar"><i className={tone} style={{ width: `${value}%` }} /></div><b>{value}</b></div>;
}

function Expert({ name, domain, finding, signal }) {
  return <article className="expert-card"><div className="expert-head"><div className="avatar">{name.split(" ").map(x => x[0]).join("")}</div><div><b>{name}</b><small>{domain} · independent view</small></div><span className={`signal ${signal}`}>{signal === "support" ? "Supports" : "Challenges"}</span></div><p>{finding}</p><button className="text-button">View evidence trail →</button></article>;
}

export default function App() {
  const [tab, setTab] = useState("brief");
  const [decision, setDecision] = useState("Should I commit the next 12 weeks to the ACA research program while launching the Vaidya Mitra clinical validation cohort?");
  const [analyzed, setAnalyzed] = useState(true);
  const [uploaded, setUploaded] = useState(false);
  const [accepted, setAccepted] = useState(false);
  const [memory, setMemory] = useState(seedMemory);
  const [notice, setNotice] = useState("");

  const decisionTitle = useMemo(() => decision.length > 76 ? `${decision.slice(0, 76)}…` : decision, [decision]);
  function runAnalysis() { setAnalyzed(true); setNotice("Analysis refreshed: Constitution and evidence remain separately visible."); }
  function addUpload() { setUploaded(true); setAccepted(false); setNotice("Source received in Inbox. It is proposed knowledge only — no constitutional change has been made."); }
  function acceptKnowledge() { setAccepted(true); setNotice("Knowledge accepted with provenance; it is now available for retrieval."); }
  function recordDecision() { setMemory([{ type: "Decision", title: decisionTitle, detail: "Just now · outcome review scheduled in 30 days", tag: "decision" }, ...memory]); setNotice("Decision record saved. ADT will surface it on future related questions."); }

  return <div className="shell">
    <aside className="sidebar">
      <div className="brand"><span className="brand-mark">A</span><div><b>ADT</b><small>Ajay Digital Twin</small></div></div>
      <nav>
        {[['brief','⌂','Today'],['inbox','↓','Knowledge inbox'],['memory','◌','Memory'],['constitution','◇','Constitution'],['research','⌁','Research']].map(([id, icon, label]) =>
          <button key={id} onClick={() => setTab(id)} className={tab === id ? 'active' : ''}><i>{icon}</i>{label}{id === 'inbox' && uploaded && !accepted ? <em>1</em> : null}</button>)}
      </nav>
      <div className="sidebar-bottom"><div className="privacy"><span>●</span> Private workspace</div><button className="profile">A <span>Ajay</span><b>⌄</b></button></div>
    </aside>
    <main>
      <header className="top"><div><p className="kicker">MONDAY, 17 AUGUST</p><h1>{tab === 'brief' ? 'Good morning, Ajay.' : tab === 'constitution' ? 'Constitution of ADT' : tab === 'inbox' ? 'Knowledge inbox' : tab === 'memory' ? 'Memory & recall' : 'Research program'}</h1></div><div className="top-actions"><button className="quiet" onClick={() => setTab('inbox')}>↓ Add knowledge</button><button className="command">⌘ K</button></div></header>
      {notice && <div className="notice"><span>✓</span>{notice}<button onClick={() => setNotice('')}>×</button></div>}

      {tab === 'brief' && <>
        <section className="north-star"><div><p className="kicker">TRUE NORTH</p><h2>“Diagnose deeply, act sparingly,<br/>align with vision, preserve resilience.”</h2></div><button onClick={() => setTab('constitution')}>Open Constitution <span>→</span></button></section>
        <section className="signal-row"><article><span className="signal-icon gold-dot">✦</span><div><small>DECISION READINESS</small><b>One decision needs your attention</b></div><button onClick={() => document.getElementById('decision')?.scrollIntoView({ behavior: 'smooth' })}>Review →</button></article><article><span className="signal-icon blue-dot">⌁</span><div><small>RESEARCH</small><b>ACA replication: next experiment ready</b></div><button onClick={() => setTab('research')}>Explore →</button></article></section>
        <section className="section-title"><div><p className="kicker">DECISION WORKBENCH</p><h2>Think with ADT</h2></div><span>Constitutional synthesis · v0.1</span></section>
        <section id="decision" className="workbench"><div className="question-box"><label>What are you deciding?</label><textarea value={decision} onChange={e => {setDecision(e.target.value); setAnalyzed(false);}} /><div><span>ADT will separate facts, assumptions, values and uncertainty.</span><button className="primary" onClick={runAnalysis}>Run decision engine <b>→</b></button></div></div>
          {analyzed && <div className="analysis">
            <div className="analysis-head"><div><small>ANALYSIS COMPLETE</small><h3>Commit in a bounded, staged way.</h3></div><span className="confidence">78% confidence</span></div>
            <p className="recommendation">Run a <b>6-week clinical-validation + research-design sprint</b> with named owners and a stop/go gate. This preserves the research trajectory without asking Ajay to carry two full launches personally.</p>
            <div className="pills"><span>Evidence: mixed / sufficient to stage</span><span>Risk: manageable</span><span>ACA: overextension watch</span></div>
            <div className="decision-grid"><div><h4>Constitutional fit</h4><Score label="Dharma & duty" value={91}/><Score label="Long-term compounding" value={86}/><Score label="People impact" value={79}/><Score label="Energy / resilience" value={58} tone="red"/></div><div className="next"><h4>Next 3 steps</h4><ol><li><b>Define the cohort’s clinical-validation protocol</b><span>Owner: clinical lead · this week</span></li><li><b>Ring-fence two deep-work blocks for ACA design</b><span>Owner: Ajay · 6 weeks</span></li><li><b>Set an explicit stop/go review</b><span>Evidence, bandwidth, delegation · week 6</span></li></ol></div></div>
            <div className="analysis-footer"><button className="quiet" onClick={() => setTab('memory')}>View reasoning record</button><button className="primary" onClick={recordDecision}>Record my decision →</button></div>
          </div>}
        </section>
        <section className="section-title compact"><div><p className="kicker">INDEPENDENT EXPERT VIEWS</p><h2>Useful disagreement is preserved.</h2></div><button className="text-button">Open expert panel →</button></section>
        <section className="experts"><Expert name="Dr. Meera Shah" domain="Clinical validation" signal="support" finding="A narrowly scoped cohort is the highest-leverage evidence generator. Do not expand feature scope until validation criteria are set."/><Expert name="Arjun Rao" domain="Research strategy" signal="challenge" finding="Parallel work is viable only if the experiment is preregistered and leadership ownership is explicitly delegated; otherwise both programs diffuse."/><Expert name="ADT Dharma Governor" domain="Constitutional synthesis" signal="support" finding="The staged approach honours the builder’s responsibility while avoiding the known pattern of overextension."/></section>
      </>}

      {tab === 'inbox' && <section className="inbox-page"><div className="upload-zone"><span>↓</span><h2>Bring knowledge into the vault</h2><p>Text, PDF, slides, data, images and notes enter as reviewable proposals — never as a silent update to Ajay’s identity.</p><button className="primary" onClick={addUpload}>Simulate an upload</button></div>{uploaded && <article className="inbox-item"><div className="file-icon">PDF</div><div><b>ACA persistent-state benchmark notes.pdf</b><p>12 claims extracted · 3 require evidence review · source class: Ajay research</p></div><span className={accepted ? 'accepted' : 'proposed'}>{accepted ? 'Accepted' : 'Proposed'}</span>{!accepted && <button className="primary" onClick={acceptKnowledge}>Review & accept</button>}</article>}<div className="guardrail"><b>Constitutional guardrail</b><span>Uploads can extend knowledge and memory. Any proposed value, goal, role or belief change requires Ajay’s explicit approval and a new version.</span></div></section>}

      {tab === 'constitution' && <section className="constitution-page"><div className="version"><div><p className="kicker">APPROVED · VERSION 1.0</p><h2>Constitutional memory</h2><p>This is ADT’s protected reference for identity and values. It is not a prompt that uploads can rewrite.</p></div><button className="quiet">View changelog</button></div><div className="constitution-grid">{constitution.map(([type,title,body]) => <article key={title}><span>{type}</span><h3>{title}</h3><p>{body}</p><small>Confirmed by Ajay · v1.0</small></article>)}</div><div className="amendment"><div><b>Need to evolve a constitutional item?</b><p>Propose → rationale/evidence → Ajay review → approval → version + changelog.</p></div><button className="primary" onClick={() => setNotice('Amendment workflow intentionally awaits explicit Ajay approval.')}>Propose amendment</button></div></section>}

      {tab === 'memory' && <section className="memory-page"><div className="recall"><p className="kicker">FUTURE RECALL</p><h2>What should ADT remember?</h2><div><span>⌕</span><input placeholder="Search decisions, research, experiences…" /><button className="primary">Recall</button></div></div><div className="memory-list">{memory.map((item,i) => <article key={i}><span className={`memory-type ${item.tag}`}>{item.type}</span><div><b>{item.title}</b><p>{item.detail}</p></div><button className="text-button">Open →</button></article>)}</div><div className="guardrail"><b>Memory protocol</b><span>Decisions retain assumptions, evidence, disagreement, uncertainty and eventual outcomes—so learning does not become retrospective fiction.</span></div></section>}

      {tab === 'research' && <section className="research-page"><p className="kicker">ACA / AI FACULTY DISSOCIATION</p><h2>Research program</h2><p className="research-intro">Are AI failures functionally decomposable into distinguishable stages, and can diagnosis improve intervention selection?</p><div className="research-grid"><article><span>01</span><h3>Frontier faculty benchmark</h3><p>Compare frontier reasoning, frontier general, small open and agentic systems across defined faculty slices.</p><b>Ready to design</b></article><article><span>02</span><h3>Persistent state benchmark</h3><p>Condition behavior, reverse environment and measure recurrence across 50–100 episode trajectories.</p><b>Protocol draft</b></article><article><span>03</span><h3>Stage-aware intervention</h3><p>Compare generic correction, diagnosis + targeted prompt, routing, process supervision and external memory.</p><b>Next experiment</b></article></div></section>}
    </main>
  </div>;
}
