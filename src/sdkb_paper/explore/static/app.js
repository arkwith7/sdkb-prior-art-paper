"use strict";

const PREFIXES = [
  ["https://w3id.org/sdkb/ont/", "ont:"],
  ["https://w3id.org/sdkb/data/patent/", "pat:"],
  ["https://w3id.org/sdkb/data/subprocess/", "subproc:"],
  ["https://w3id.org/sdkb/data/process/", "proc:"],
  ["https://w3id.org/sdkb/data/device/", "dev:"],
  ["https://w3id.org/sdkb/data/organization/", "org:"],
  ["https://w3id.org/sdkb/data/", "data:"],
  ["https://w3id.org/sdkb/gov/", "gov:"],
  ["http://www.w3.org/2004/02/skos/core#", "skos:"],
  ["http://www.w3.org/2000/01/rdf-schema#", "rdfs:"],
  ["http://www.w3.org/1999/02/22-rdf-syntax-ns#", "rdf:"],
  ["http://www.w3.org/2001/XMLSchema#", "xsd:"],
];
const G_LABEL = { v0: "G₀", v1: "G₁", v2: "G₂" };

function shorten(iri) {
  for (const [full, pfx] of PREFIXES) if (iri.startsWith(full)) return pfx + iri.slice(full.length);
  return iri;
}
function el(tag, attrs = {}, ...kids) {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") e.className = v;
    else if (k === "html") e.innerHTML = v;
    else if (k.startsWith("on")) e.addEventListener(k.slice(2), v);
    else e.setAttribute(k, v);
  }
  for (const kid of kids) e.append(kid?.nodeType ? kid : document.createTextNode(kid ?? ""));
  return e;
}
async function api(path, opts) {
  const r = await fetch(path, opts);
  const j = await r.json();
  if (j.error) throw new Error(j.error);
  return j;
}

/* ---------- 탭 ---------- */
document.querySelectorAll("nav button").forEach((b) =>
  b.addEventListener("click", () => {
    document.querySelectorAll("nav button").forEach((x) => x.classList.remove("active"));
    document.querySelectorAll(".tab").forEach((x) => x.classList.remove("active"));
    b.classList.add("active");
    document.getElementById(b.dataset.tab).classList.add("active");
    if (b.dataset.tab === "findings") loadFindings();
  })
);

/* ---------- 대시보드 ---------- */
let GRAPHS_AVAILABLE = [];
async function loadStatus() {
  const box = document.getElementById("status-cards");
  try {
    const s = await api("/api/status");
    box.innerHTML = "";
    GRAPHS_AVAILABLE = [];
    for (const key of ["v0", "v1", "v2"]) {
      const info = s.graphs[key];
      if (!info) continue;
      if (info.exists) GRAPHS_AVAILABLE.push(key);
      box.append(statusCard(key, info, s.signatures[key]));
    }
    populateGraphSelects();
  } catch (e) {
    box.innerHTML = `<div class="empty" style="color:var(--danger)">상태 로드 실패: ${e.message}</div>`;
  }
}
function statusCard(key, info, sig) {
  const c = el("div", { class: "card" });
  c.append(el("h3", {}, el("span", { class: "dot " + key }), info.label));
  c.append(el("div", { class: "path" }, info.path.split("/").slice(-2).join("/")));
  if (!info.exists) {
    c.append(el("div", { class: "empty" }, "파일 없음 — make baseline / make merge 필요"));
    return c;
  }
  if (!sig) {
    c.append(el("div", { class: "empty spin" }, "질의 중…"));
    return c;
  }
  const stat = (n, l) => el("div", { class: "stat" }, el("div", { class: "n" }, fmt(n)), el("div", { class: "l" }, l));
  const row1 = el("div", { class: "stat-row" }, stat(sig.triples, "트리플"), stat(sig.patent, "특허"), stat(sig.steps, "공정 단계"));
  const row2 = el("div", { class: "stat-row" }, stat(sig.device, "디바이스"), stat(sig.organization, "조직"), stat(sig.expert, "전문가"));
  c.append(row1, row2);
  // coverage bar
  const covPct = sig.steps ? (sig.covered / sig.steps) * 100 : 0;
  const bar = el("div", { class: "bar" });
  bar.append(el("div", { class: "fill", style: `width:${covPct}%` }), el("div", { class: "gap", style: `width:${100 - covPct}%` }));
  c.append(bar);
  c.append(el("div", { class: "cov-legend" },
    el("span", {}, `커버 ${sig.covered}`), el("span", {}, `공백 ${sig.gap}`), el("span", {}, `${covPct.toFixed(0)}%`)));
  // drift (G0)
  if (sig.drift && Object.keys(sig.drift).length) {
    const items = Object.entries(sig.drift).map(([k, v]) => `${k}: ${v.got}≠정본${v.expected}`).join(" · ");
    c.append(el("div", { class: "drift" }, "⚠ 정본 서명과 불일치 — " + items));
  } else if (sig.drift) {
    c.append(el("div", { class: "ok-badge" }, "✓ 정본 서명과 일치 (트리플 44,202 · 커버 20/49)"));
  }
  return c;
}
function fmt(n) { return (typeof n === "number" ? n : 0).toLocaleString(); }

/* ---------- 그래프 선택 드롭다운 ---------- */
function populateGraphSelects() {
  const opts = GRAPHS_AVAILABLE.map((k) => `<option value="${k}">${G_LABEL[k]} · ${k}</option>`).join("");
  ["graph-select", "expert-graph", "pa-graph", "fto-graph"].forEach((id) => {
    const s = document.getElementById(id);
    if (s) s.innerHTML = opts;
  });
  const gs = document.getElementById("graph-select");
  if (gs && GRAPHS_AVAILABLE.includes("v1")) gs.value = "v1";
}

/* ---------- CQ 프리셋 ---------- */
async function loadCQs() {
  const box = document.getElementById("cq-list");
  try {
    const { cqs } = await api("/api/cq");
    box.innerHTML = "";
    for (const cq of cqs) {
      const item = el("div", { class: "cq-item", onclick: () => { document.getElementById("query").value = cq.sparql; document.getElementById("active-cq").textContent = cq.name + " (expect ≥ " + cq.expect_min + ")"; runQuery(); } });
      item.append(el("div", { class: "cq-name" }, cq.name.replace(/_/g, " ")));
      item.append(el("div", { class: "cq-desc" }, cq.desc));
      box.append(item);
    }
  } catch (e) {
    box.innerHTML = `<div class="empty" style="color:var(--danger)">${e.message}</div>`;
  }
}

/* ---------- SPARQL 실행 ---------- */
let LAST_RESULT = null;
async function runQuery() {
  const graph = document.getElementById("graph-select").value;
  const query = document.getElementById("query").value.trim();
  const meta = document.getElementById("query-meta");
  const tblBox = document.getElementById("result-table");
  const tabs = document.getElementById("result-tabs");
  if (!query) return;
  meta.innerHTML = '<span class="spin">실행 중…</span>';
  tblBox.innerHTML = ""; tabs.style.display = "none";
  try {
    const res = await api("/api/sparql", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ graph, query }) });
    LAST_RESULT = res;
    renderResult(res, graph);
  } catch (e) {
    meta.innerHTML = `<span class="err">${e.message}</span>`;
  }
}
function renderResult(res, graph) {
  const meta = document.getElementById("query-meta");
  const tblBox = document.getElementById("result-table");
  const tabs = document.getElementById("result-tabs");
  const graphBox = document.getElementById("result-graph");
  graphBox.style.display = "none";
  if (res.kind === "ask") {
    meta.innerHTML = `<b>${G_LABEL[graph]}</b> · ASK → <b style="color:${res.boolean ? "var(--accent2)" : "var(--danger)"}">${res.boolean}</b> · ${res.elapsed_ms.toFixed(1)} ms`;
    return;
  }
  const nrows = res.kind === "construct" ? res.triples.length : res.rows.length;
  meta.innerHTML = `<b>${G_LABEL[graph]}</b> · ${res.kind.toUpperCase()} · ${fmt(nrows)} 행${res.truncated ? " (상한 절단)" : ""} · ${res.elapsed_ms.toFixed(1)} ms`;
  tblBox.innerHTML = "";
  if (nrows === 0) { tblBox.append(el("div", { class: "empty" }, "결과 0행")); return; }

  if (res.kind === "construct") {
    tabs.style.display = "flex";
    tblBox.append(triplesTable(res.triples));
    setupGraphView(res.triples);
    document.querySelectorAll("#result-tabs button").forEach((b) => b.onclick = () => switchView(b.dataset.view));
    switchView("graph");
  } else {
    tabs.style.display = "none";
    tblBox.append(selectTable(res.columns, res.rows));
  }
}
function switchView(view) {
  document.getElementById("result-table").style.display = view === "table" ? "block" : "none";
  document.getElementById("result-graph").style.display = view === "graph" ? "block" : "none";
  document.querySelectorAll("#result-tabs button").forEach((b) => b.classList.toggle("primary", b.dataset.view === view));
  if (view === "graph" && window._cyResize) window._cyResize();
}
function cell(term) {
  if (!term) return el("td", { class: "muted" }, "—");
  if (term.type === "uri") {
    const short = shorten(term.value);
    return el("td", { class: "uri" }, el("a", { href: term.value, target: "_blank", title: term.value }, short));
  }
  const td = el("td", { class: "literal" + (isNum(term.value) ? " number" : "") }, term.value);
  if (term.datatype) td.append(el("span", { class: "tag" }, shorten(term.datatype)));
  if (term.lang) td.append(el("span", { class: "tag" }, "@" + term.lang));
  return td;
}
function isNum(v) { return v !== "" && !isNaN(v); }
function selectTable(cols, rows) {
  const wrap = el("div", { class: "tbl-wrap" });
  const t = el("table");
  const thead = el("tr");
  cols.forEach((c) => thead.append(el("th", {}, c)));
  t.append(el("thead", {}, thead));
  const tb = el("tbody");
  rows.forEach((r) => { const tr = el("tr"); r.forEach((c) => tr.append(cell(c))); tb.append(tr); });
  t.append(tb); wrap.append(t); return wrap;
}
function triplesTable(triples) {
  const wrap = el("div", { class: "tbl-wrap" });
  const t = el("table");
  t.append(el("thead", {}, el("tr", {}, el("th", {}, "subject"), el("th", {}, "predicate"), el("th", {}, "object"))));
  const tb = el("tbody");
  triples.forEach((tr) => tb.append(el("tr", {}, cell(tr.s), cell(tr.p), cell(tr.o))));
  t.append(tb); wrap.append(t); return wrap;
}

/* ---------- Cytoscape 그래프 뷰 ---------- */
let CY = null;
function setupGraphView(triples) {
  const nodes = new Map(), edges = [];
  const nid = (t) => t.type === "uri" ? t.value : t.type + ":" + t.value;
  for (const tr of triples) {
    const s = tr.s, o = tr.o;
    if (!nodes.has(nid(s))) nodes.set(nid(s), { data: { id: nid(s), label: shorten(s.value), kind: "node" } });
    if (o.type === "uri" || o.type === "bnode") {
      if (!nodes.has(nid(o))) nodes.set(nid(o), { data: { id: nid(o), label: shorten(o.value), kind: "node" } });
      edges.push({ data: { source: nid(s), target: nid(o), label: shorten(tr.p.value) } });
    } else {
      const litId = nid(s) + "|" + tr.p.value + "|" + o.value;
      nodes.set(litId, { data: { id: litId, label: o.value, kind: "lit" } });
      edges.push({ data: { source: nid(s), target: litId, label: shorten(tr.p.value) } });
    }
  }
  const container = document.getElementById("cy");
  if (CY) CY.destroy();
  CY = cytoscape({
    container,
    elements: [...nodes.values(), ...edges],
    style: [
      { selector: "node", style: { "background-color": "#4493f8", label: "data(label)", color: "#e6edf3", "font-size": "9px", "text-wrap": "wrap", "text-max-width": "90px", width: 16, height: 16, "text-valign": "center", "text-halign": "right", "text-margin-x": 3 } },
      { selector: 'node[kind="lit"]', style: { "background-color": "#3fb950", shape: "round-rectangle", width: 10, height: 10 } },
      { selector: "edge", style: { width: 1, "line-color": "#8b98a5", "target-arrow-color": "#8b98a5", "target-arrow-shape": "triangle", "curve-style": "bezier", label: "data(label)", "font-size": "7px", color: "#8b98a5", "text-rotation": "autorotate" } },
    ],
    layout: { name: "cose", animate: false, nodeRepulsion: 6000, idealEdgeLength: 70 },
  });
  window._cyResize = () => { CY.resize(); CY.fit(undefined, 30); };
}

/* ---------- CSV ---------- */
function exportCSV() {
  if (!LAST_RESULT) return;
  const r = LAST_RESULT;
  let cols, rows;
  if (r.kind === "construct") { cols = ["subject", "predicate", "object"]; rows = r.triples.map((t) => [t.s, t.p, t.o]); }
  else if (r.kind === "select") { cols = r.columns; rows = r.rows; }
  else return;
  const esc = (v) => { const s = v ? v.value : ""; return /[",\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s; };
  const csv = [cols.join(","), ...rows.map((row) => row.map(esc).join(","))].join("\n");
  const a = el("a", { href: URL.createObjectURL(new Blob([csv], { type: "text/csv" })), download: "sparql_result.csv" });
  a.click();
}

/* ---------- 핵심 발견 ---------- */
let FINDINGS_LOADED = false;
async function loadFindings() {
  if (FINDINGS_LOADED) return;
  const box = document.getElementById("findings-body");
  try {
    const f = await api("/api/findings");
    box.innerHTML = "";
    box.append(findingBlock("H1 · 공정 커버리지 확장", f.claims.h1, f.axes, "coverage_covered", "coverage_total"));
    box.append(findingBlock("RQ2 · 선행기술 후보 (CQ10)", f.claims.rq2, f.axes, "prior_art_cq10"));
    box.append(findingBlock("RQ3/FTO · 청구항 준비 (CQ27)", f.claims.fto, f.axes, "fto_cq27_rows"));
    FINDINGS_LOADED = true;
  } catch (e) {
    box.innerHTML = `<div class="empty" style="color:var(--danger)">${e.message}</div>`;
  }
}
function findingBlock(title, claim, axes, key, totalKey) {
  const b = el("div", { class: "finding" });
  b.append(el("h3", {}, title), el("div", { class: "claim" }, claim));
  const vals = Object.entries(axes).map(([g, a]) => ({ g, v: a[key], t: totalKey ? a[totalKey] : null }));
  const max = Math.max(1, ...vals.map((x) => x.v));
  const bars = el("div", { class: "axisbars" });
  for (const { g, v, t } of vals) {
    const h = (v / max) * 150 + 20;
    const colColor = g === "v0" ? "var(--g0)" : g === "v1" ? "var(--g1)" : "var(--g2)";
    const ab = el("div", { class: "axisbar" });
    ab.append(el("div", { class: "col", style: `height:${h}px;background:${colColor}` }, t ? `${v}/${t}` : String(v)));
    ab.append(el("div", { class: "lbl" }, G_LABEL[g]));
    bars.append(ab);
  }
  b.append(bars);
  return b;
}

/* ---------- 실무 질의 ---------- */
const P_LABEL = "PREFIX ont: <https://w3id.org/sdkb/ont/>\nPREFIX skos: <http://www.w3.org/2004/02/skos/core#>\nPREFIX xsd: <http://www.w3.org/2001/XMLSchema#>\n";
function ci(s) { return s.replace(/"/g, '\\"'); }
async function runPractical(kind) {
  let graph, query, target;
  if (kind === "expert") {
    graph = document.getElementById("expert-graph").value;
    const kw = ci(document.getElementById("expert-kw").value.trim());
    target = "expert-result";
    query = P_LABEL + `SELECT ?stepLabel ?skillLabel ?expertLabel WHERE {
  VALUES ?t { ont:Process ont:SubProcess }
  ?step a ?t ; ont:requiresSkill ?skill ; skos:prefLabel ?stepLabel .
  ?skill skos:prefLabel ?skillLabel .
  ?expert a ont:Expert ; ont:hasSkill ?skill ; skos:prefLabel ?expertLabel .
  ${kw ? `FILTER(CONTAINS(LCASE(?stepLabel), LCASE("${kw}")) || CONTAINS(LCASE(?skillLabel), LCASE("${kw}")))` : ""}
} ORDER BY ?stepLabel LIMIT 200`;
  } else if (kind === "priorart") {
    graph = document.getElementById("pa-graph").value;
    const kw = ci(document.getElementById("pa-kw").value.trim());
    const date = document.getElementById("pa-date").value || "2015-01-01";
    target = "priorart-result";
    query = P_LABEL + `SELECT ?conceptLabel ?prior ?filed WHERE {
  ?prior a ont:Patent ; ont:realizesProcess ?concept ; ont:filingDate ?filed .
  ?concept skos:prefLabel ?conceptLabel .
  FILTER(?filed < "${date}"^^xsd:date)
  ${kw ? `FILTER(CONTAINS(LCASE(?conceptLabel), LCASE("${kw}")))` : ""}
} ORDER BY ?filed LIMIT 200`;
  } else if (kind === "fto") {
    graph = document.getElementById("fto-graph").value;
    const kw = ci(document.getElementById("fto-kw").value.trim());
    target = "fto-result";
    query = P_LABEL + `SELECT ?orgLabel (COUNT(DISTINCT ?patent) AS ?ftoReady) WHERE {
  ?patent a ont:Patent ; ont:claimText ?claim ; ont:assignedTo ?org .
  ?org skos:prefLabel ?orgLabel .
  ${kw ? `FILTER(CONTAINS(?orgLabel, "${kw}"))` : ""}
} GROUP BY ?orgLabel ORDER BY DESC(?ftoReady) LIMIT 200`;
  }
  const box = document.getElementById(target);
  box.innerHTML = '<span class="spin">질의 중…</span>';
  try {
    const res = await api("/api/sparql", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ graph, query }) });
    box.innerHTML = "";
    box.append(el("div", { class: "meta" }, `${G_LABEL[graph]} · ${res.rows.length} 건 · ${res.elapsed_ms.toFixed(0)} ms`));
    if (res.rows.length === 0) box.append(el("div", { class: "empty" }, "결과 없음 — 그래프를 바꾸거나 키워드를 조정하세요"));
    else box.append(selectTable(res.columns, res.rows.slice(0, 50)));
  } catch (e) {
    box.innerHTML = `<span class="err">${e.message}</span>`;
  }
}

/* ---------- 부트 ---------- */
document.getElementById("run-btn").addEventListener("click", runQuery);
document.getElementById("csv-btn").addEventListener("click", exportCSV);
document.getElementById("query").addEventListener("keydown", (e) => { if ((e.ctrlKey || e.metaKey) && e.key === "Enter") runQuery(); });
loadStatus();
loadCQs();
