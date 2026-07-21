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
    if (b.dataset.tab === "viewer" && !VW) loadDomain();
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
    c.append(el("div", { class: "ok-badge" }, "✓ 정본 서명과 일치 (트리플 49,210 · 커버 20/49)"));
  }
  return c;
}
function fmt(n) { return (typeof n === "number" ? n : 0).toLocaleString(); }

/* ---------- 그래프 선택 드롭다운 ---------- */
function populateGraphSelects() {
  const opts = GRAPHS_AVAILABLE.map((k) => `<option value="${k}">${G_LABEL[k]} · ${k}</option>`).join("");
  ["graph-select", "expert-graph", "pa-graph", "fto-graph", "nl-graph", "vw-graph"].forEach((id) => {
    const s = document.getElementById(id);
    if (s) s.innerHTML = opts;
  });
  // 기본은 G₁ — 신기술 별칭(HBM·GAA·식각)이 병합 때 실체화되므로 G₀ 에서는 문장 질의가
  // 약해 보인다. 데모의 기본값이 도구를 실제보다 못하게 보이게 해서는 안 된다.
  if (GRAPHS_AVAILABLE.includes("v1"))
    for (const id of ["graph-select", "nl-graph", "vw-graph"]) {
      const s = document.getElementById(id);
      if (s) s.value = "v1";
    }
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

/* ---------- 문장으로 질의 (앵커링) ---------- */
const NL_TITLE = {
  expert: "① 전문가 후보",
  priorart: "② 선행기술 후보",
  fto: "③ FTO 청구항 준비 현황",
};

async function runNL() {
  const box = document.getElementById("nl-result");
  const text = document.getElementById("nl-text").value.trim();
  if (!text) { box.innerHTML = '<span class="err">문장을 입력하세요</span>'; return; }
  const graph = document.getElementById("nl-graph").value;
  const before = document.getElementById("nl-date").value || "2015-01-01";
  box.innerHTML = '<span class="spin">문장 해석 · 질의 중…</span>';
  try {
    const r = await api("/api/interpret", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, graph, before }),
    });
    box.innerHTML = "";

    // (1) 인식된 앵커 — 무엇을 근거로 읽었는지 그대로 보인다.
    box.append(el("h4", {}, `인식된 개념 ${r.anchors.length}개`));
    if (r.anchors.length === 0)
      box.append(el("div", { class: "empty" }, "그래프 어휘와 겹치는 개념이 없습니다 — 공정·소자·스킬 용어를 포함해 보세요"));
    const chips = el("div", { class: "chips" });
    for (const a of r.anchors) {
      chips.append(
        el("span", { class: "chip" + (a.queryable ? "" : " muted"), title: a.iri },
          el("b", {}, a.cls), ` ${a.label}`,
          el("i", {}, ` ← ${a.matched.join(", ")}${a.via_alt ? " (별칭)" : ""} · ${a.score}`))
      );
    }
    box.append(chips);

    // (2) 질의에 쓰이지 않은 구절 — 대응 술어가 없는 것을 있는 척하지 않는다.
    if (r.unused.length)
      box.append(el("div", { class: "meta" },
        `질의에 쓰이지 않음 (대응 술어 없음): ${r.unused.join(" · ")}`));

    // (3) 시나리오별 결과 + 생성된 SPARQL(펼쳐보기 · SPARQL 탭으로 복사 가능)
    for (const kind of ["expert", "priorart", "fto"]) {
      const q = r.queries[kind];
      if (!q) continue;
      const res = r.results[kind];
      box.append(el("h4", {}, `${NL_TITLE[kind]} — ${res.rows.length} 건`));
      if (res.rows.length === 0)
        box.append(el("div", { class: "empty" }, "결과 없음 — 그래프를 바꾸거나 기준일을 조정하세요"));
      else box.append(selectTable(res.columns, res.rows.slice(0, 50)));
      const det = el("details", {}, el("summary", {}, "생성된 SPARQL 보기"));
      det.append(el("pre", { class: "gen-sparql" }, q));
      det.append(el("button", {
        class: "btn", onclick: () => {
          document.getElementById("query").value = q;
          document.getElementById("graph-select").value = graph;
          document.querySelector('nav button[data-tab="sparql"]').click();
        },
      }, "SPARQL 탭에서 편집"));
      box.append(det);
    }
  } catch (e) {
    box.innerHTML = `<span class="err">${e.message}</span>`;
  }
}

/* ---------- 부트 ---------- */
document.getElementById("run-btn").addEventListener("click", runQuery);
document.getElementById("csv-btn").addEventListener("click", exportCSV);
document.getElementById("query").addEventListener("keydown", (e) => { if ((e.ctrlKey || e.metaKey) && e.key === "Enter") runQuery(); });
for (const id of ["vw-graph", "vw-mode"])
  document.getElementById(id).addEventListener("change", () => { if (VW) loadDomain(); });
loadStatus();
loadCQs();

/* ---------- 온톨로지 뷰어 ---------- */
// 축 색은 서버(viewer.AXES)와 한 벌이어야 한다 — 한쪽만 바뀌면 범례가 거짓말을 한다.
const VW_AXIS = {
  Process: ["공정 그룹", "#4493f8"], SubProcess: ["하위 공정", "#3fb950"],
  Device: ["소자·제품", "#e5487f"], Material: ["재료", "#d29922"],
  Equipment: ["장비", "#a371f7"], EquipmentClass: ["장비 클래스", "#8957e5"],
  Skill: ["역량", "#39c5cf"], FailureMode: ["불량 모드", "#f85149"],
  Problem: ["실무 문제", "#db6d28"], Expert: ["전문가", "#2ea043"],
  Patent: ["특허", "#7d8590"], RejectedPatent: ["거절 특허", "#6e7681"],
  Organization: ["조직", "#bf8700"], Vendor: ["공급사", "#9e6a03"],
  ProblemCategory: ["문제 범주(집계)", "#8250df"],
};
let VW = null;              // cytoscape 인스턴스
let VW_LOADED = new Set();  // 이미 펼친 노드 — 같은 노드를 두 번 질의하지 않는다

function vwColor(cls) { return (VW_AXIS[cls] || ["기타", "#8b98a5"])[1]; }
function vwKo(cls) { return (VW_AXIS[cls] || ["기타", "#8b98a5"])[0]; }

function vwApi(body) {
  return api("/api/viewer", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ graph: document.getElementById("vw-graph").value, ...body }),
  });
}

function vwEls(d) {
  const els = [];
  for (const n of d.nodes) {
    els.push({ data: {
      id: n.id, label: n.label, cls: n.cls, axis: n.axis_ko || vwKo(n.cls),
      def: n.definition || "", patents: n.patents || 0,
      experts: n.experts, problems: n.problems, derived: !!n.derived,
      // 특허 수로 크기를 준다 — 로그 스케일이 아니면 EPROM(5,139)이 화면을 다 먹는다.
      size: 16 + Math.min(26, Math.log2(1 + (n.patents || 0)) * 3),
    } });
  }
  for (const e of d.edges) els.push({ data: { id: `${e.src}|${e.pred}|${e.dst}`, source: e.src, target: e.dst, pred: e.pred } });
  return els;
}

function vwInit() {
  if (VW) return VW;
  VW = cytoscape({
    container: document.getElementById("vw-canvas"),
    style: [
      { selector: "node", style: {
          "background-color": (n) => vwColor(n.data("cls")),
          width: "data(size)", height: "data(size)",
          label: "data(label)", color: "#c9d1d9", "font-size": 10,
          "text-valign": "bottom", "text-margin-y": 4, "text-outline-width": 2,
          "text-outline-color": "#0d1117", "min-zoomed-font-size": 7 } },
      { selector: "node:selected", style: { "border-width": 3, "border-color": "#e6edf3" } },
      { selector: "edge", style: {
          width: 1, "line-color": "#30363d", "target-arrow-color": "#30363d",
          "target-arrow-shape": "triangle", "curve-style": "bezier", "arrow-scale": 0.7 } },
      { selector: "edge[pred = 'hasSubprocess']", style: { "line-color": "#3fb950", "target-arrow-color": "#3fb950", width: 1.6 } },
    ],
    wheelSensitivity: 0.2,
  });
  VW.on("mouseover", "node", (e) => vwTip(e.target, e.renderedPosition || e.target.renderedPosition()));
  VW.on("mouseout", "node", () => { document.getElementById("vw-tip").style.display = "none"; });
  VW.on("tap", "node", (e) => vwDetail(e.target.id(), e.target.data()));
  VW.on("dbltap", "node", (e) => vwExpand(e.target.id(), e.target.data("derived")));
  return VW;
}

// 마우스오버 툴팁 — 이름 · 축 배지 · 정의 · 특허 수 · IRI
function vwTip(node, pos) {
  const tip = document.getElementById("vw-tip");
  const d = node.data();
  const def = d.def || "<i>정의 없음 — 그래프에 skos:definition 이 없습니다</i>";
  // 축마다 세는 것이 다르다 — 특허 수를 인력 축에 붙이면 거짓이 된다.
  let use;
  if (d.derived) use = `<span>집계</span> 이 범주의 실무문제 ${fmt(d.problems)}건 — 그래프의 개체가 아닙니다`;
  else if (d.experts !== undefined) use = `<span>인력</span> 보유 전문가 ${fmt(d.experts)}명 · 요구 실무문제 ${fmt(d.problems)}건`;
  else if (d.problems !== undefined) use = `<span>연결</span> 이 불량모드를 보이는 실무문제 ${fmt(d.problems)}건`;
  else use = `<span>연결</span> 이 개념을 실현·언급하는 특허 ${fmt(d.patents)}건`;
  tip.innerHTML = `<div class="t-name">${d.label}</div>`
    + `<div class="t-cat">${d.axis}</div>`
    + `<div class="t-desc">${def}</div>`
    + `<div class="t-use">${use}</div>`
    + `<div class="t-id">${shorten(d.id)}</div>`;
  const box = document.getElementById("vw-canvas").getBoundingClientRect();
  tip.style.display = "block";
  tip.style.left = Math.min(box.left + pos.x + 14, window.innerWidth - 340) + "px";
  tip.style.top = (box.top + pos.y + 12) + "px";
}

async function loadDomain() {
  const meta = document.getElementById("vw-meta");
  const mode = document.getElementById("vw-mode").value;
  meta.innerHTML = '<span class="spin">지도 계산 중…</span>';
  vwInit();
  VW_LOADED = new Set();
  try {
    const d = await vwApi({ mode });
    VW.elements().remove();
    VW.add(vwEls(d));
    VW.layout({ name: "cose", animate: false, nodeRepulsion: 9000, idealEdgeLength: 70, padding: 30 }).run();
    meta.innerHTML = `노드 ${d.nodes.length} · 엣지 ${d.edges.length} — 클릭: 속성 · 더블클릭: 이웃 펼치기`;
    if (d.note) meta.innerHTML += `<br /><span class="warn-note">${d.note}</span>`;
    vwLegend();
  } catch (e) { meta.innerHTML = `<span class="err">${e.message}</span>`; }
}

async function vwExpand(iri, derived) {
  const meta = document.getElementById("vw-meta");
  if (VW_LOADED.has(iri)) { meta.innerHTML = "이미 펼친 노드입니다."; return; }
  meta.innerHTML = '<span class="spin">이웃 조회 중…</span>';
  try {
    const d = await vwApi({ mode: derived ? "category" : "expand", iri });
    VW_LOADED.add(iri);
    const els = vwEls(d).filter((el) => !VW.getElementById(el.data.id).length);
    VW.add(els);
    VW.layout({ name: "cose", animate: false, nodeRepulsion: 9000, idealEdgeLength: 70, padding: 30 }).run();
    meta.innerHTML = `+${d.nodes.length} 이웃 · 총 ${VW.nodes().length} 노드`;
    // 상한에 걸렸으면 말한다 — 조용히 자르면 "이게 전부"로 읽힌다.
    if (d.truncated) meta.innerHTML += ` <span class="warn-note">⚠ 상한 절단 — 이웃이 더 있습니다</span>`;
  } catch (e) { meta.innerHTML = `<span class="err">${e.message}</span>`; }
}

async function vwDetail(iri, data) {
  const panel = document.getElementById("vw-panel");
  // 집계 노드는 그래프에 없다 — detail 을 물으면 빈 응답이 온다. 그 사실을 그대로 말한다.
  if (data && data.derived) {
    panel.innerHTML = "";
    panel.append(el("h4", {}, data.label));
    panel.append(el("div", { class: "t-cat" }, data.axis));
    panel.append(el("p", { class: "vw-def muted" },
      `ont:problemCategory 집계 노드입니다 — 그래프의 개체가 아니라 실무문제 ${fmt(data.problems)}건을 묶은 것입니다.`));
    panel.append(el("button", { class: "btn", onclick: () => vwExpand(iri, true) }, "이 범주의 문제 펼치기"));
    return;
  }
  panel.innerHTML = '<div class="empty spin">속성 조회 중…</div>';
  try {
    const d = await vwApi({ mode: "detail", iri });
    panel.innerHTML = "";
    panel.append(el("h4", {}, d.label));
    panel.append(el("div", { class: "t-cat" }, d.axis_ko));
    if (d.definition) panel.append(el("p", { class: "vw-def" }, d.definition));
    else panel.append(el("p", { class: "vw-def muted" }, "정의 없음 — 그래프에 skos:definition 이 없습니다"));
    if (d.alt_labels.length) panel.append(el("div", { class: "meta" }, "별칭: " + d.alt_labels.join(" · ")));
    panel.append(el("div", { class: "t-id" }, shorten(d.iri)));
    // 같은 술어가 여러 값을 갖는 일이 흔하다(confidence 4개·isDueTo 3개) — 술어당 한 줄로 묶는다.
    // 자르지 않는다: 잘린 값은 읽을 수 없고, 읽을 수 없으면 속성창이 아니다.
    const byPred = new Map();
    for (const p of d.props) {
      if (!byPred.has(p.pred)) byPred.set(p.pred, []);
      byPred.get(p.pred).push(p);
    }
    const tbl = el("table", { class: "vw-props" });
    for (const [pred, items] of byPred) {
      const cell = el("td", { class: "vw-vals" });
      for (const p of items) {
        if (p.is_iri) {
          // IRI 는 라벨이 있으면 라벨로 — 없으면 접두사로 줄인다. 링크는 새 창.
          const text = p.label || shorten(p.value);
          cell.append(p.value.startsWith("http") && !p.value.startsWith("https://w3id.org/sdkb")
            ? el("a", { href: p.value, target: "_blank", rel: "noreferrer", class: "vw-link" }, text)
            : el("span", { class: "vw-iri", title: p.value }, text));
        } else {
          cell.append(el("span", {}, p.value));
        }
      }
      tbl.append(el("tr", {}, el("td", {}, pred), cell));
    }
    if (d.props.length) panel.append(tbl);
    panel.append(el("button", { class: "btn", onclick: () => vwExpand(iri) }, "이웃 펼치기"));
  } catch (e) { panel.innerHTML = `<span class="err">${e.message}</span>`; }
}

function vwLegend() {
  const box = document.getElementById("vw-legend");
  box.innerHTML = "";
  const present = new Set(VW.nodes().map((n) => n.data("cls")));
  for (const cls of present) {
    box.append(el("span", { class: "lg" }, el("i", { style: `background:${vwColor(cls)}` }), vwKo(cls)));
  }
}
