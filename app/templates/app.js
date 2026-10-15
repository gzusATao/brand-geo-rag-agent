"use strict";
const state = {projectId: null, runId: null, questions: [], revision: 0, batchId: null};
const $ = (id) => document.getElementById(id);
const esc = (value) => String(value ?? "").replace(/[&<>"']/g, (c) => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const sources = {mock:"模拟", historical:"历史", real:"真实", mixed:"混合"};
const statuses = {pending:"等待执行", running:"执行中", completed:"已完成", failed:"失败", approved:"已通过", rejected:"已驳回"};

async function api(path, method = "GET", payload) {
  const response = await fetch(`/api/v1${path}`, {method, headers: {"Content-Type":"application/json", "X-GEO-Request":"1"}, ...(payload === undefined ? {} : {body:JSON.stringify(payload)})});
  if (response.status === 401) {window.location.replace("/login"); throw new Error("登录已失效，请重新登录");}
  if (!response.ok) {const body = await response.json(); const error=new Error(typeof body.detail === "string" ? body.detail : "请求失败，请检查输入"); error.status=response.status; throw error;}
  return response.json();
}
function message(text, error = false) {const area=$("message"); area.textContent = text; area.className = error ? "error" : ""; area.setAttribute("role",error ? "alert" : "status"); if(text&&error)area.scrollIntoView({block:"nearest"});}
function path(suffix) {if (!state.projectId) throw new Error("请先创建或选择品牌项目"); return `/projects/${state.projectId}${suffix}`;}
function view(name) {
  const titles = {home:["开始使用","品牌监测，从这里开始"],collect:["运行监测","选择回答来源，开始一次监测"],library:["项目管理","数据监控项目库"],single:["分析记录","问句与批次分析记录"],history:["监测批次历史","监测批次历史"],monitor:["查看结果","本次品牌监测结果"],knowledge:["品牌知识库","品牌知识库"],content:["优化与审核","内容优化与审核"],setup:["创建监测项目","第一步：创建项目与监测问句"]};
  // 先确认页面注册，再切换面板，避免标题解析失败时留下半切换状态。
  titles.maintenance=["数据监控维护","数据监控维护"];
  if (!titles[name]) throw new Error("页面配置不存在，请刷新后重试");
  document.body.dataset.workspaceView=name;
  document.querySelectorAll("[data-panel]").forEach((panel) => panel.hidden = panel.dataset.panel !== name);
  document.querySelectorAll("[data-view]").forEach((button) => button.classList.toggle("active", button.dataset.view === name));
  $("tab-title").textContent = titles[name][0]; $("page-title").textContent = titles[name][1];
  message("");
  document.dispatchEvent(new CustomEvent("workspace-view-changed",{detail:{name}}));
}
function list(id, html, empty) {$(id).innerHTML = html || `<p>${esc(empty)}</p>`;}
function badge(text, tone = "blue") {return `<span class="badge ${tone}">${esc(text)}</span>`;}
function reset() {state.runId = null; $("review-card").hidden = true; ["hits","citations","trace"].forEach((id) => $(id).replaceChildren());}
async function perform(action, button) {if(button?.getAttribute("aria-busy")==="true")return; if (button) {button.disabled = true;button.setAttribute("aria-busy","true");} try {await action();} catch (error) {message(error.message, true);} finally {if (button) {button.disabled = false;button.removeAttribute("aria-busy");} document.dispatchEvent(new CustomEvent("workspace-action-finished"));}}
function form(id, action) {$(id).addEventListener("submit", (event) => {event.preventDefault(); perform(() => action(event), event.submitter);});}

async function loadProjects(selectedId) {
  const projects = await api("/projects");
  $("projects").innerHTML = projects.length ? projects.map((p) => `<option value="${p.id}">${esc(p.name)}</option>`).join("") : '<option value="">请先创建项目</option>';
  if (selectedId) $("projects").value = String(selectedId);
  state.projectId = Number($("projects").value) || null;
  reset();
  if (state.projectId) await refresh();
  document.dispatchEvent(new CustomEvent("workspace-ready",{detail:{projects}}));
}
async function refresh() {
  if (!state.projectId) return;
  const revision = ++state.revision;
  const projectId = state.projectId;
  const base = `/projects/${projectId}`;
  const filters = new URLSearchParams();
  if ($("source").value) filters.set("source", $("source").value);
  if (state.batchId) filters.set("batch_id", state.batchId);
  const filter = filters.size ? `?${filters}` : "";
  const [project, questions, metrics, answers, batches, documents, runs] = await Promise.all([
    api(base), api(base + "/questions"), api(base + "/metrics" + filter), api(base + "/answers" + filter),
    api(base + "/monitor-batches"), api(base + "/knowledge/documents"), api(base + "/optimization-runs")
  ]);
  if (revision !== state.revision || projectId !== state.projectId) return;
  state.questions = questions;
  $("subtitle").textContent = `${project.name} · 目标品牌 ${project.brand}`;
  $("count").textContent = metrics.sample_count;
  $("mention").textContent = metrics.sample_count ? `${(metrics.brands[0].mention_rate * 100).toFixed(1)}%` : "—";
  $("recommendation").textContent = metrics.sample_count ? `${(metrics.brands[0].recommendation_rate * 100).toFixed(1)}%` : "—";
  list("questions", questions.map((q) => `<div class="item">${esc(q.text)}<button data-question="${q.id}" data-enabled="${!q.enabled}" class="secondary">${q.enabled ? "停用" : "启用"}</button></div>`).join(""), "暂无问句");
  $("metrics").innerHTML = metrics.brands.map((m) => `<tr><td>${badge(m.brand)}</td><td>${m.mention_count}</td><td>${m.recommendation_count}</td><td>${metrics.sample_count ? (m.mention_rate * 100).toFixed(1) + "%" : "—"}</td><td>${esc(Object.entries(m.rank_distribution).map(([rank, count]) => `第${rank}位：${count}次`).join(" / ") || "无明确编号")}</td></tr>`).join("");
  list("batches", batches.length ? `<div class="table-wrap"><table><thead><tr><th>批次编号</th><th>数据来源</th><th>执行状态</th><th>完成 / 总数</th><th>创建时间</th><th>异常说明</th></tr></thead><tbody>${batches.map((b) => `<tr><td>#${b.id}</td><td>${badge(sources[b.source], b.source === "mock" ? "amber" : "blue")}</td><td>${badge(statuses[b.status], b.status === "completed" ? "green" : b.status === "failed" ? "red" : "blue")}</td><td>${b.completed} / ${b.total}</td><td>${esc(b.created_at)}</td><td class="error-cell">${esc(b.error || "—")}</td></tr>`).join("")}</tbody></table></div>` : "", "暂无监测批次，导入回答或运行模拟监测后将在这里展示");
  list("answers", answers.map((a) => `<details class="item"><summary>${esc(a.question)} · ${sources[a.source]} · ${esc(a.model)}</summary><pre>${esc(a.answer)}</pre>${a.extraction.map((e) => `<p>${esc(e.brand)}：提及 ${e.mentioned ? "是" : "否"} / 规则推荐 ${e.recommended ? "是" : "否"} / 排名 ${e.rank ?? "无明确顺序"}<br>${esc(e.evidence.join("；"))}</p>`).join("")}</details>`).join(""), "当前来源下暂无回答");
  list("documents", documents.map((d) => `<div class="item">${esc(d.title)} · ${d.chunk_count}个片段<p>${esc(d.source)}</p></div>`).join(""), "暂无品牌资料");
  list("runs", runs.map((r) => `<div class="item">${esc(r.query)} · ${r.review_status === "pending" ? "待审核" : statuses[r.review_status]}<button data-run="${r.id}" class="secondary">查看与审核</button></div>`).join(""), "暂无优化运行");
  document.dispatchEvent(new CustomEvent("monitor-data-loaded", {detail:{batches,projectId,project,questions,metrics,documents,runs}}));
}
function hits(id, items) {list(id, items.map((h) => `<div class="item">[${h.chunk_id}] ${esc(h.title)} · 词面分数 ${h.score}<p>${esc(h.text)}</p><small>来源：${esc(h.source)}</small></div>`).join(""), "未找到相关资料，请补充证据");}
function showRun(run) {state.runId = run.id; $("review-card").hidden = false; $("diagnosis").textContent = run.diagnosis; $("draft").value = run.draft; $("note").value = run.review_note || ""; $("trace").innerHTML = run.trace.map((s) => `<p>${esc(s.tool)} · ${esc(s.summary)}</p>`).join(""); hits("citations", run.citations); $("export").disabled = run.review_status !== "approved";}

document.querySelectorAll("[data-view]").forEach((button) => button.addEventListener("click", () => view(button.dataset.view)));
$("projects").addEventListener("change", () => {state.projectId = Number($("projects").value) || null; state.batchId = null; reset(); perform(refresh);});
$("source").addEventListener("change", () => perform(refresh));
$("reload").addEventListener("click", (event) => perform(() => loadProjects(state.projectId), event.currentTarget));
$("logout").addEventListener("click", (event) => perform(async () => {await api("/auth/logout", "POST"); window.location.replace("/login");}, event.currentTarget));
form("project-form", async () => {const lines = (id) => $(id).value.split(/\n/).map((s) => s.trim()).filter(Boolean); const p = await api("/monitor-projects", "POST", {name:$("name").value,brand:$("brand").value,aliases:lines("aliases"),competitors:lines("competitors"),initial_questions:lines("initial-questions")}); state.batchId=null; await loadProjects(p.id); view("collect"); message("项目与问句已保存。接下来选择模拟演示，或导入你收集的回答。");});
form("question-form", async () => {await api(path("/questions"), "POST", {text:$("question").value}); $("question").value = ""; await refresh(); message("问句已添加");});
$("questions").addEventListener("click", (event) => {const b = event.target.closest("[data-question]"); if (b) perform(async () => {await api(path(`/questions/${b.dataset.question}`), "PATCH", {enabled:b.dataset.enabled === "true"}); await refresh();}, b);});
$("mock").addEventListener("click", (event) => perform(async () => {const ids = state.questions.filter((q) => q.enabled).map((q) => q.id); if (!ids.length) throw new Error("请先添加启用问句"); const batch = await api(path("/monitor-batches/mock"), "POST", {question_ids:ids}); const projectId = state.projectId; state.batchId=batch.id; $("source").value = "mock"; message("正在生成模拟回答并提取品牌证据，请稍候……"); for (let i = 0; i < 30; i++) {const current = await api(`/monitor-batches/${batch.id}`); if (state.projectId !== projectId) return; if (["completed","failed"].includes(current.status)) {await refresh(); if(current.status === "completed") view("monitor"); message(current.error || "模拟演示已完成。下方指标只说明这批模拟样本，不代表品牌的真实效果。", current.status === "failed"); return;} await new Promise((resolve) => setTimeout(resolve, 500));} await refresh(); message("仍在执行，请稍后刷新进度");}, event.currentTarget));
$("import").addEventListener("click", (event) => perform(async () => {const file = $("csv").files[0]; if (!file) throw new Error("请选择CSV文件"); if (file.size > 500000) throw new Error("CSV文件不能超过500KB"); const content = await file.text(); if (content.includes("\ufffd")) throw new Error("请将CSV保存为UTF-8编码"); const batch = await api(path("/monitor-batches/import"), "POST", {content}); state.batchId=batch.id; $("source").value = batch.source === "mixed" ? "" : batch.source; await refresh(); view("monitor"); message(`已导入并分析${batch.completed}条回答。下方为本次导入结果，来源由你声明。`);}, event.currentTarget));
form("document-form", async () => {await api(path("/knowledge/documents"), "POST", {title:$("document-title").value,source:$("document-source").value,content:$("document-content").value}); await refresh(); message("资料已保存并分段");});
form("retrieval-form", async () => hits("hits", await api(path("/knowledge/retrieve"), "POST", {query:$("query").value,top_k:3})));
form("optimization-form", async () => {const run = await api(path("/optimization-runs"), "POST", {query:$("target-query").value,top_k:3}); await refresh(); showRun(run); message("固定工作流已完成，请人工核对");});
$("runs").addEventListener("click", (event) => {const b = event.target.closest("[data-run]"); if (b) perform(async () => showRun(await api(`/optimization-runs/${b.dataset.run}`)), b);});
form("review-form", async (event) => {if (!state.runId) throw new Error("请先选择运行"); const run = await api(`/optimization-runs/${state.runId}/review`, "POST", {status:event.submitter.value,note:$("note").value,draft:$("draft").value}); await refresh(); showRun(run); message("审核记录已保存");});
$("export").addEventListener("click", () => perform(async () => {const response = await fetch(`/api/v1/optimization-runs/${state.runId}/export`); if (response.status === 401) window.location.replace("/login"); if (!response.ok) throw new Error((await response.json()).detail); const url = URL.createObjectURL(await response.blob()); const link = document.createElement("a"); link.href = url; link.download = `草稿-${state.runId}.md`; link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000); message("已导出最新审核通过的保存版本，未保存编辑不包含在内");}));
view("monitor");
perform(async () => {const session = await api("/auth/session"); $("username").textContent = session.role === "superadmin" ? `${session.username} · 超级管理员` : session.username; await loadProjects();});
