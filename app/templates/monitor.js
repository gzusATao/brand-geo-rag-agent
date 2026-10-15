"use strict";
const monitorState = {libraryPage:1, analysisPage:1, settingsProject:null, revision:{library:0, single:0}};
const mainPanel = document.querySelector("main");
const navPanel = document.querySelector("nav");
const menuGroup = document.createElement("div");
menuGroup.className = "monitor-group";
menuGroup.textContent = "◈ 数据监控";
navPanel.prepend(menuGroup);
for (const [key, title] of [["single","单次问句分析"],["setup","创建新数据监控项目"],["library","数据监控项目库"]].reverse()) {
  const button = document.createElement("button");
  button.dataset.view = key;
  button.className = "monitor-child";
  button.textContent = title;
  button.addEventListener("click", () => perform(async () => {view(key); if(key !== "setup") await loadMonitorPage(key);}));
  menuGroup.after(button);
}
navPanel.querySelector('[data-view="setup"]:not(.monitor-child)').remove();
navPanel.querySelector('[data-view="monitor"]').innerHTML = '<span class="nav-icon">▥</span>监测数据详情';

function statusOptions(includeDraft=false) {
  return `<option value="">全部</option>${includeDraft ? '<option value="draft">草稿</option>' : ''}<option value="pending">等待执行</option><option value="running">执行中</option><option value="completed">已完成</option><option value="failed">失败</option>`;
}
for (const [key,title,action] of [["library","项目列表","＋ 新建数据监控"],["single","分析记录","＋ 新增问句分析"]]) {
  const section = document.createElement("section");
  section.dataset.panel = key;
  section.hidden = true;
  section.innerHTML = `<div class="monitor-toolbar"><h2>${title}</h2><button id="${key}-new">${action}</button></div><form id="${key}-filters" class="card monitor-filters">${key === "library" ? '<label>项目名称<input name="name" placeholder="请输入项目名称" maxlength="100"></label>' : ''}<label>品牌名称<input name="brand" placeholder="请输入品牌名称" maxlength="100"></label>${key === "single" ? '<label>问句内容<input name="question" placeholder="请输入已保存问句" maxlength="500"></label><label>数据来源<select name="source"><option value="">全部来源</option><option value="historical">历史回答</option><option value="real">真实回答</option><option value="mock">模拟回答</option><option value="mixed">混合导入</option></select></label>' : '<label>创建日期起<input type="date" name="start_date"></label><label>创建日期止<input type="date" name="end_date"></label>'}<label>项目状态<select name="status">${statusOptions(key === "library")}</select></label><button>搜索</button><button type="button" class="secondary" id="${key}-reset">重置</button></form><article class="card monitor-table"><div id="${key}-rows"></div><div class="monitor-pagination"><span id="${key}-total"></span><select id="${key}-size" aria-label="${title}每页条数"><option value="20">20条/页</option><option value="50">50条/页</option><option value="100">100条/页</option></select><button class="secondary" id="${key}-prev" aria-label="${title}上一页">‹</button><span id="${key}-page"></span><button class="secondary" id="${key}-next" aria-label="${title}下一页">›</button></div></article><p class="monitor-note">${key === "library" ? '项目状态取自最新批次；本版手动运行，不代表持续自动采集。品牌词典创建后固定，确保历史证据可复现。' : '单问句模拟与CSV导入批次统一展示，导入可包含多条问句。真实、历史来源由导入者声明，尚未直连公共AI平台。'}</p>`;
  mainPanel.querySelector("footer").before(section);
  form(`${key}-filters`, async () => {monitorState[key === "library" ? "libraryPage" : "analysisPage"] = 1; await loadMonitorPage(key);});
  $(`${key}-reset`).addEventListener("click", () => { $(`${key}-filters`).reset(); monitorState[key === "library" ? "libraryPage" : "analysisPage"] = 1; perform(() => loadMonitorPage(key)); });
  $(`${key}-size`).addEventListener("change", () => {monitorState[key === "library" ? "libraryPage" : "analysisPage"] = 1; perform(() => loadMonitorPage(key));});
  for(const [direction,increment] of [["prev",-1],["next",1]]) $(`${key}-${direction}`).addEventListener("click", (event) => perform(async () => {monitorState[key === "library" ? "libraryPage" : "analysisPage"] += increment; await loadMonitorPage(key);}, event.currentTarget));
}
const historyPanel = document.createElement("section");
historyPanel.dataset.panel = "history";
historyPanel.hidden = true;
historyPanel.innerHTML = '<article class="card monitor-table"><h2>运行与导入历史</h2><div id="history-rows"></div></article>';
mainPanel.querySelector("footer").before(historyPanel);
const context = document.createElement("div");
context.className = "monitor-context";
context.innerHTML = '<label for="detail-batch">统计批次</label><select id="detail-batch"><option value="">全部批次</option></select><button class="secondary" id="detail-history">批次历史</button><button class="secondary" id="detail-library">返回项目库</button>';
document.querySelector('[data-panel="monitor"]').prepend(context);
const intro = document.createElement("article");
intro.className = "card monitor-intro";
intro.innerHTML = '<span class="monitor-step">01 品牌配置 → 02 监测问句 → 03 采集与分析</span><h2>建立一份可追溯的品牌监测项目</h2><p>填写目标品牌、别名和竞品后，在项目详情添加监测问句。可运行模拟批次验证流程，或导入已核验的真实、历史回答。</p><p>品牌资料在知识库中独立管理，不注入监测回答，以避免干扰自然回答的可见性评估。</p>';
document.querySelector('[data-panel="setup"]').prepend(intro);
document.querySelector('[data-panel="setup"] .narrow p').textContent = "项目名称可以修改；品牌、别名与竞品词典创建后固定。无需媒体投放或发布文章。";

const dialog = document.createElement("dialog");
dialog.id = "monitor-dialog";
dialog.className = "monitor-dialog";
dialog.innerHTML = '<h2 id="monitor-dialog-title"></h2><p id="monitor-dialog-description"></p><form id="monitor-dialog-form"><label id="rename-label">项目名称<input id="rename-project" required maxlength="100"></label><label id="single-label">选择当前项目的启用问句<select id="single-question" required></select></label><div class="dialog-actions"><button type="button" class="secondary" id="monitor-dialog-close">取消</button><button>确认</button></div></form>';
document.body.append(dialog);
$("monitor-dialog-close").addEventListener("click", () => dialog.close());

async function loadMonitorPage(key) {
  const revision = ++monitorState.revision[key];
  const page = monitorState[key === "library" ? "libraryPage" : "analysisPage"];
  const params = new URLSearchParams();
  for(const [name,value] of new FormData($(`${key}-filters`))) if(value) params.set(name,value);
  if(params.get("start_date") && params.get("end_date") && params.get("start_date") > params.get("end_date")) throw new Error("开始日期不能晚于结束日期");
  params.set("page",page); params.set("page_size",$(`${key}-size`).value);
  const result = await api(`/${key === "library" ? "monitor-projects" : "monitor-analyses"}?${params}`);
  if(revision !== monitorState.revision[key]) return;
  if(!result.items.length && page > 1) {monitorState[key === "library" ? "libraryPage" : "analysisPage"] = 1; return loadMonitorPage(key);}
  const headers = key === "library" ? ["序号","创建日期","项目名称","品牌名称","品牌别名","启用问句","项目类型","项目状态","操作"] : ["序号","创建日期","品牌名称","问句摘要","分析规模","数据来源","项目状态","操作"];
  const rows = result.items.map((item,index) => {
    // 失败批次可能保留部分证据，不能仅凭失败状态禁止查看原文。
    const waiting = ["pending","running"].includes(item.status) && !item.completed;
    const viewLabel = item.status === "failed" ? item.completed ? "查看已保存回答" : "失败原因" : "查看";
    const actions = key === "library"
      ? `<button data-monitor-action="data" data-project-id="${item.id}">数据</button><button data-monitor-action="settings" data-project-id="${item.id}">设置</button><button data-monitor-action="history" data-project-id="${item.id}">历史</button>`
      : `<button data-monitor-action="data" data-project-id="${item.project_id}" data-batch-id="${item.id}" data-source="${item.source}" ${waiting ? 'disabled title="尚无已保存回答，请稍后刷新列表"' : ''}>${viewLabel}</button>`;
    return `<tr><td>${(page-1)*Number(params.get("page_size"))+index+1}</td><td>${esc(item.created_at.slice(0,10))}</td>${key === "library" ? `<td>${esc(item.name)}</td><td>${badge(item.brand)}</td><td>${item.aliases.map(a=>badge(a)).join(" ") || "—"}</td><td>${item.question_count}</td><td>${badge("数据监控")}</td>` : `<td>${badge(item.brand)}</td><td class="question-cell">${esc(item.question)}</td><td>${item.total === 1 ? "单问句分析" : `${item.total}条回答批次`}</td><td>${badge(sources[item.source],item.source === "mock" ? "amber" : "blue")}</td>`}<td>${badge(item.status === "draft" ? "草稿" : statuses[item.status], item.status === "completed" ? "green" : item.status === "failed" ? "red" : "blue")}</td><td>${actions}</td></tr>`;
  }).join("");
  $(`${key}-rows`).innerHTML = rows ? `<div class="table-wrap"><table><thead><tr>${headers.map(h=>`<th>${h}</th>`).join("")}</tr></thead><tbody>${rows}</tbody></table></div>` : `<div class="monitor-empty"><strong>${key === "library" ? "暂无监测项目" : "暂无分析记录"}</strong>${key === "library" ? "创建品牌项目，开始第一轮研究。" : "运行单问句模拟分析，或在项目详情导入回答CSV。"}</div>`;
  $(`${key}-total`).textContent = `共 ${result.total} 条`;
  $(`${key}-page`).textContent = `${page} / ${Math.max(1,Math.ceil(result.total/Number(params.get("page_size"))))}`;
  $(`${key}-prev`).disabled = page === 1;
  $(`${key}-next`).disabled = page*Number(params.get("page_size")) >= result.total;
  $(`${key}-rows`).querySelectorAll('[data-monitor-action]').forEach(button=>button.classList.add("secondary"));
  if(key === "single") $(`${key}-rows`).querySelectorAll('[data-monitor-action="data"]').forEach(button=>button.dataset.monitorAction="analysis");
  document.dispatchEvent(new CustomEvent("monitor-page-loaded",{detail:{key,result,page}}));
}

async function openMonitor(projectId,batchId=null,source=null) {
  state.batchId = batchId;
  await loadProjects(projectId);
  if(source !== null) $("source").value = source === "mixed" ? "" : source;
  const batches = await api(path("/monitor-batches"));
  $("detail-batch").innerHTML = '<option value="">全部批次</option>' + batches.map(b=>`<option value="${b.id}">#${b.id} · ${sources[b.source]} · ${statuses[b.status]}</option>`).join("");
  $("detail-batch").value = batchId ? String(batchId) : "";
  await refresh();
  view("monitor");
}
async function showHistory(projectId) {
  await openMonitor(projectId);
  const batches = await api(path("/monitor-batches"));
  $("history-rows").innerHTML = batches.length ? `<div class="table-wrap"><table><thead><tr><th>批次</th><th>创建时间</th><th>来源</th><th>状态</th><th>进度</th><th>异常说明</th><th>操作</th></tr></thead><tbody>${batches.map(b=>`<tr><td>#${b.id}</td><td>${esc(b.created_at)}</td><td>${badge(sources[b.source])}</td><td>${badge(statuses[b.status])}</td><td>${b.completed}/${b.total}</td><td class="question-cell">${esc(b.error || "—")}</td><td><button data-monitor-action="data" data-project-id="${projectId}" data-batch-id="${b.id}" data-source="${b.source}">批次数据</button></td></tr>`).join("")}</tbody></table></div>` : '<div class="monitor-empty">暂无运行或导入批次</div>';
  view("history");
}
document.addEventListener("click", (event) => {
  const button = event.target.closest("[data-monitor-action]");
  if(!button) return;
  if(!["data","history","settings"].includes(button.dataset.monitorAction)) return;
  perform(async () => {
    const id = Number(button.dataset.projectId);
    if(button.dataset.monitorAction === "history") return showHistory(id);
    if(button.dataset.monitorAction === "data") return openMonitor(id,Number(button.dataset.batchId)||null,button.dataset.source ?? null);
    if(button.dataset.monitorAction === "settings") return openMaintenance(id);
    const project = await api(`/projects/${id}`);
    monitorState.settingsProject = id;
    $("monitor-dialog-title").textContent = "监测项目设置";
    $("monitor-dialog-description").textContent = "可修改项目名称。监测问句的启停在项目数据详情中管理；品牌词典保持不变。";
    $("rename-label").hidden = false; $("single-label").hidden = true;
    $("rename-project").disabled = false; $("single-question").disabled = true;
    $("rename-project").value = project.name;
    dialog.showModal();
  },button);
});
$("library-new").addEventListener("click", () => view("setup"));
$("single-new").addEventListener("click", (event) => perform(async () => {
  if(!state.projectId) {goCollect(); return;}
  const questions = await api(path("/questions"));
  const enabled = questions.filter(q=>q.enabled);
  if(!enabled.length) {goCollect(); message("在下方补充一条监测问句，保存后就可以分析。"); return;}
  monitorState.settingsProject = null;
  $("monitor-dialog-title").textContent = "单次问句分析";
  $("monitor-dialog-description").textContent = "当前仅支持模拟适配器，结果用于验证流程，不代表公共AI平台的实际推荐效果。";
  $("rename-label").hidden = true; $("single-label").hidden = false;
  $("rename-project").disabled = true; $("single-question").disabled = false;
  $("single-question").innerHTML = enabled.map(q=>`<option value="${q.id}">${esc(q.text)}</option>`).join("");
  dialog.showModal();
},event.currentTarget));
form("monitor-dialog-form", async () => {
  if(monitorState.settingsProject) {
    await api(`/projects/${monitorState.settingsProject}`,"PATCH",{name:$("rename-project").value});
    dialog.close(); await loadProjects(state.projectId); await loadMonitorPage("library"); message("项目名称已更新"); return;
  }
  const projectId = state.projectId;
  const batch = await api(path("/monitor-batches/mock"),"POST",{question_ids:[Number($("single-question").value)]});
  dialog.close();
  // 新批次保留独立记录，不覆盖历史证据；后台执行完成后再展示状态。
  for(let i=0;i<30;i++) {
    const current = await api(`/monitor-batches/${batch.id}`);
    if(["completed","failed"].includes(current.status)) {await openMonitor(projectId,batch.id,"mock"); message(current.error || "单问句模拟分析完成，仅用于流程验证",current.status === "failed"); return;}
    await new Promise(resolve=>setTimeout(resolve,500));
  }
  view("single"); await loadMonitorPage("single"); message("批次仍在执行，请稍后刷新");
});
$("detail-batch").addEventListener("change", () => perform(async () => {state.batchId = Number($("detail-batch").value)||null; if(state.batchId) {const batch=await api(`/monitor-batches/${state.batchId}`); $("source").value=batch.source === "mixed" ? "" : batch.source;} await refresh();}));
$("detail-history").addEventListener("click", () => perform(() => showHistory(state.projectId)));
$("detail-library").addEventListener("click", () => perform(async () => {view("library"); await loadMonitorPage("library");}));
document.addEventListener("monitor-data-loaded", (event) => {
  $("detail-batch").innerHTML = '<option value="">全部批次</option>' + event.detail.batches.map(b=>`<option value="${b.id}">#${b.id} · ${sources[b.source]} · ${statuses[b.status]}</option>`).join("");
  $("detail-batch").value = state.batchId ? String(state.batchId) : "";
});
// 创建、导入和整组模拟后回到全部批次，避免旧批次过滤隐藏新记录。
for(const id of ["mock","import"]) $(id).addEventListener("click", () => {state.batchId=null;}, {capture:true});
view("library");
perform(() => loadMonitorPage("library"));
