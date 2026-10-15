"use strict";
document.body.classList.add("geo-console");
const consoleTabs = document.createElement("div");
consoleTabs.className="console-tabs";
consoleTabs.setAttribute("aria-label","已打开的工作页签");
document.querySelector(".tabbar").append(consoleTabs);
const openTabs=new Set(["home","single","setup","library"]);
const tabNames={home:"首页",single:"单次AI搜索数据",setup:"创建新数据监控项目",library:"数据监控项目库",collect:"数据采集与导入",monitor:"项目监控数据",maintenance:"数据监控维护",history:"监测历史",knowledge:"企业知识库",content:"文章草稿与审核"};
let activeConsoleView="home";
function renderConsoleTabs(){
  consoleTabs.innerHTML=Array.from(openTabs).map(key=>`<span class="console-tab ${key === activeConsoleView ? "selected" : ""}"><button data-console-tab="${key}">${esc(tabNames[key])}</button>${key !== "home" ? `<button data-close-tab="${key}" aria-label="关闭${esc(tabNames[key])}">×</button>` : ''}</span>`).join("");
}
document.addEventListener("workspace-view-changed",event=>{activeConsoleView=event.detail.name;openTabs.add(activeConsoleView);renderConsoleTabs();});
consoleTabs.addEventListener("click",event=>{
  const close=event.target.closest("[data-close-tab]");
  if(close){openTabs.delete(close.dataset.closeTab); if(activeConsoleView === close.dataset.closeTab)view("home");renderConsoleTabs();return;}
  const button=event.target.closest("[data-console-tab]");if(!button)return;
  const key=button.dataset.consoleTab;
  perform(async()=>{view(key);if(["single","library"].includes(key))await loadMonitorPage(key);});
});
renderConsoleTabs();
recordsNav.textContent="单次AI搜索数据"; setupNav.textContent="创建新数据监控项目"; libraryNav.textContent="数据监控项目库";
$("single-new").textContent="＋ 新增数据分析";
$("library-new").textContent="＋ 新建数据监控";
document.querySelector('[data-panel="single"] .monitor-toolbar h2').textContent="数据分析";
document.querySelector('[data-panel="library"] .monitor-toolbar h2').textContent="数据监控项目库";

// 复用已有导航节点及其事件，分组只改变组织方式，不创建无法执行的菜单入口。
function consoleIcon(name){
  const paths={
    home:'<path d="m3 10 9-7 9 7M5 9v12h14V9M9 21v-8h6v8"/>',
    monitor:'<rect x="3" y="4" width="18" height="13" rx="1"/><path d="M8 21h8M12 17v4M5 11h4l2-4 3 7 2-3h3"/>',
    article:'<path d="M5 3h10l4 4v14H5zM15 3v5h4M8 12h8M8 16h6"/>',
    knowledge:'<path d="m3 7 9-4 9 4-9 4zM3 12l9 4 9-4M3 17l9 4 9-4"/>',
    menu:'<path d="M4 5h16M4 12h16M4 19h16M8 3v18"/>'
  };
  return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths[name] || paths.monitor}</svg>`;
}
const consoleNav=document.querySelector("nav");
guideNav.innerHTML=`${consoleIcon("home")}<span>首页</span>`;
guideNav.classList.add("console-home");
const knowledgeNav=consoleNav.querySelector('[data-view="knowledge"]');
const articleNav=consoleNav.querySelector('[data-view="content"]');
collectNav.textContent="数据采集与导入";resultsNav.textContent="项目监控数据";
knowledgeNav.textContent="企业资料管理";articleNav.textContent="文章草稿与审核";
for(const [name,icon,buttons] of [
  ["GEO 数据监控","monitor",[recordsNav,setupNav,libraryNav,collectNav,resultsNav]],
  ["内容创作","article",[articleNav]],
  ["企业知识库","knowledge",[knowledgeNav]]
]){
  const group=document.createElement("details");
  group.className="console-nav-group";group.open=icon==="monitor";
  group.innerHTML=`<summary title="${name}">${consoleIcon(icon)}<span>${name}</span><i aria-hidden="true"></i></summary><div class="console-nav-children"></div>`;
  for(const button of buttons){button.classList.add("monitor-child");group.lastElementChild.append(button);}
  consoleNav.append(group);
}
menuGroup.remove();
const projectPicker=$("projects").closest("label");
projectPicker.className="console-project-picker";
document.querySelector(".topbar .account").before(projectPicker);
const sidebarControls=document.createElement("div");sidebarControls.className="console-sidebar-controls";
sidebarControls.innerHTML=`<button type="button" id="console-sidebar-toggle" aria-label="收起侧边菜单" aria-expanded="true">${consoleIcon("menu")}<span class="console-menu-label">菜单</span></button>`;
sidebarControls.append($("reload"));document.querySelector("aside").append(sidebarControls);
$("reload").textContent="刷新数据";
$("console-sidebar-toggle").addEventListener("click",()=>{
  if(window.matchMedia("(max-width:560px)").matches){
    const open=document.body.classList.toggle("mobile-menu-open");
    $("console-sidebar-toggle").setAttribute("aria-expanded",String(open));
    $("console-sidebar-toggle").setAttribute("aria-label",open ? "收起业务菜单" : "展开业务菜单");
    return;
  }
  const collapsed=document.body.classList.toggle("sidebar-collapsed");
  $("console-sidebar-toggle").setAttribute("aria-expanded",String(!collapsed));
  $("console-sidebar-toggle").setAttribute("aria-label",collapsed ? "展开侧边菜单" : "收起侧边菜单");
});
document.addEventListener("workspace-view-changed",event=>{
  const active=consoleNav.querySelector(`[data-view="${event.detail.name}"]`);
  if(active?.closest("details"))active.closest("details").open=true;
  consoleNav.querySelectorAll("[data-view]").forEach(button=>{
    if(button===active)button.setAttribute("aria-current","page");else button.removeAttribute("aria-current");
  });
  if(window.matchMedia("(max-width:560px)").matches){
    document.body.classList.remove("mobile-menu-open");
    $("console-sidebar-toggle").setAttribute("aria-expanded","false");
    $("console-sidebar-toggle").setAttribute("aria-label","展开业务菜单");
  }
});
if(window.matchMedia("(max-width:560px)").matches){
  $("console-sidebar-toggle").setAttribute("aria-expanded","false");
  $("console-sidebar-toggle").setAttribute("aria-label","展开业务菜单");
}
consoleNav.addEventListener("click",event=>{
  if(event.target.closest("summary")&&document.body.classList.contains("sidebar-collapsed"))$("console-sidebar-toggle").click();
});

// 两个月共用一个范围，表单始终提交真实日期而不是显示文本。
const rangePopup=document.createElement("div");rangePopup.className="date-range-popup";rangePopup.hidden=true;rangePopup.setAttribute("role","dialog");rangePopup.setAttribute("aria-label","选择创建日期范围");document.body.append(rangePopup);
let rangeState=null;
function dateText(date){return `${date.getFullYear()}-${String(date.getMonth()+1).padStart(2,"0")}-${String(date.getDate()).padStart(2,"0")}`;}
function drawRange(){
  const {month,start,end}=rangeState;
  const calendars=[0,1].map(offset=>{
    const current=new Date(month.getFullYear(),month.getMonth()+offset,1);
    const first=new Date(current.getFullYear(),current.getMonth(),1-current.getDay());
    const days=Array.from({length:42},(_,index)=>{const date=new Date(first.getFullYear(),first.getMonth(),first.getDate()+index);const value=dateText(date);return `<button type="button" data-range-day="${value}" class="${date.getMonth() !== current.getMonth() ? "outside-month" : ""} ${value === start || value === end ? "endpoint" : ""} ${start && end && value > start && value < end ? "in-range" : ""}" aria-label="${value}">${date.getDate()}</button>`;}).join("");
    return `<div class="date-month"><h3>${current.getFullYear()} 年 ${current.getMonth()+1} 月</h3><div class="date-week">${["日","一","二","三","四","五","六"].map(day=>`<span>${day}</span>`).join("")}</div><div class="date-days">${days}</div></div>`;
  }).join("");
  rangePopup.innerHTML=`<div class="date-nav"><button type="button" data-range-shift="-12" aria-label="上一年">«</button><button type="button" data-range-shift="-1" aria-label="上个月">‹</button><span>${start && !end ? "请选择结束日期" : "选择开始与结束日期"}</span><button type="button" data-range-shift="1" aria-label="下个月">›</button><button type="button" data-range-shift="12" aria-label="下一年">»</button></div><div class="date-months">${calendars}</div><div class="date-footer"><button type="button" data-range-clear>清空日期</button><span>${esc(start || "开始日期")} — ${esc(end || "结束日期")}</span></div>`;
}
function syncRange(form){const start=form.elements.start_date.value,end=form.elements.end_date.value;form.querySelector("[data-range-open]").textContent=start&&end ? `▦ ${start} — ${end}` : "▦ 开始日期 — 结束日期";}
for(const key of ["single","library"]){
  const filters=$(`${key}-filters`);
  if(key === "single") filters.insertAdjacentHTML("beforeend",'<input type="hidden" name="start_date"><input type="hidden" name="end_date">');
  else for(const name of ["start_date","end_date"]){const input=filters.elements[name];input.type="hidden";input.closest("label").hidden=true;}
  const label=document.createElement("label");label.className="range-field";label.innerHTML='<span>创建日期</span><button type="button" class="secondary" data-range-open>▦ 开始日期 — 结束日期</button>';
  const searchButton=filters.querySelector('button:not([type="button"])');
  searchButton.before(label);
  searchButton.textContent="⌕ 查询";
  label.querySelector("button").addEventListener("click",event=>{
    const start=filters.elements.start_date.value;const month=start ? new Date(Number(start.slice(0,4)),Number(start.slice(5,7))-1,1) : new Date();
    rangeState={form:filters,month,start,end:filters.elements.end_date.value};drawRange();rangePopup.hidden=false;
    const rect=event.currentTarget.getBoundingClientRect();rangePopup.style.left=`${Math.max(10,Math.min(rect.left,window.innerWidth-670))}px`;rangePopup.style.top=`${Math.max(10,Math.min(rect.bottom+6,window.innerHeight-430))}px`;
  });
  filters.addEventListener("reset",()=>{queueMicrotask(()=>syncRange(filters));rangePopup.hidden=true;});
}
rangePopup.addEventListener("click",event=>{
  const shift=event.target.closest("[data-range-shift]");if(shift){rangeState.month=new Date(rangeState.month.getFullYear(),rangeState.month.getMonth()+Number(shift.dataset.rangeShift),1);drawRange();return;}
  if(event.target.closest("[data-range-clear]")){rangeState.form.elements.start_date.value="";rangeState.form.elements.end_date.value="";syncRange(rangeState.form);rangePopup.hidden=true;return;}
  const day=event.target.closest("[data-range-day]");if(!day)return;
  const value=day.dataset.rangeDay;
  if(!rangeState.start||rangeState.end){rangeState.start=value;rangeState.end="";drawRange();return;}
  const [start,end]=[rangeState.start,value].sort();rangeState.form.elements.start_date.value=start;rangeState.form.elements.end_date.value=end;syncRange(rangeState.form);rangePopup.hidden=true;
});
// 日历重绘会移除原按钮，用事件原始传播路径判断内部点击，不能再查新 DOM 的 contains。
document.addEventListener("click",event=>{if(!event.composedPath().includes(rangePopup)&&!event.target.closest("[data-range-open]"))rangePopup.hidden=true;});
document.addEventListener("keydown",event=>{if(event.key === "Escape")rangePopup.hidden=true;});

// 列表可按页码跳转；已有上一页/下一页继续复用原逻辑。
document.addEventListener("monitor-page-loaded",event=>{
  const {key,result,page}=event.detail;
  const pagination=$(`${key}-page`);const count=Math.max(1,Math.ceil(result.total/Number($(`${key}-size`).value)));
  pagination.innerHTML=Array.from({length:Math.min(5,count)},(_,index)=>Math.max(1,Math.min(page-2,count-4))+index).filter(number=>number<=count).map(number=>`<button data-list-page="${number}" data-list-key="${key}" class="${number === page ? "current-page" : ""}">${number}</button>`).join("")+`<label class="page-jump">前往 <input type="number" min="1" max="${count}" value="${page}" data-page-jump="${key}" aria-label="${key === "single" ? "分析记录" : "项目库"}跳转页码"> / ${count} 页</label>`;
});
document.addEventListener("click",event=>{const button=event.target.closest("[data-list-page]");if(!button)return;monitorState[button.dataset.listKey === "single" ? "analysisPage" : "libraryPage"]=Number(button.dataset.listPage);perform(()=>loadMonitorPage(button.dataset.listKey),button);});
document.addEventListener("keydown",event=>{if(event.key !== "Enter"||!event.target.matches("[data-page-jump]"))return;event.preventDefault();const input=event.target;if(!input.checkValidity()){input.reportValidity();return;}monitorState[input.dataset.pageJump === "single" ? "analysisPage" : "libraryPage"]=Number(input.value);perform(()=>loadMonitorPage(input.dataset.pageJump));});

const analysisDialog=document.createElement("dialog");analysisDialog.className="analysis-dialog";analysisDialog.setAttribute("aria-labelledby","analysis-heading-title");analysisDialog.innerHTML='<div class="analysis-heading"><h2 id="analysis-heading-title">查看分析详情</h2><button id="analysis-close" aria-label="关闭分析详情">×</button></div><div id="analysis-body"></div>';document.body.append(analysisDialog);
$("analysis-close").addEventListener("click",()=>analysisDialog.close());
let analysisState=null;
let analysisRevision=0;
async function openAnalysis(batchId,offset=0){
  const revision=++analysisRevision;
  const detail=await api(`/monitor-batches/${batchId}/detail?limit=20&offset=${offset}`);
  if(revision!==analysisRevision)return;
  const evidenceOpen=analysisState?.batchId===batchId ? analysisState.evidenceOpen : true;
  analysisState={detail,offset,batchId,index:0,evidenceOpen};renderAnalysis();if(!analysisDialog.open)analysisDialog.showModal();
}
function renderAnalysis(){
  const {detail,offset,index,evidenceOpen}=analysisState;
  const answer=detail.answers[index];
  // 品牌标签必须与当前原文一一对应，不能混入同页其他回答的识别结果。
  const brands=Array.from(new Set((answer?.extraction || []).filter(e=>e.mentioned).map(e=>e.brand)));
  const statusText=detail.batch.status==="failed"
    ? `批次执行失败，已保存 ${detail.total_answers} 条回答。${detail.batch.error || "请到监测历史查看运行情况。"}`
    : ["pending","running"].includes(detail.batch.status)
      ? "批次尚未完成；当前仅展示已保存的回答，可刷新查看进度。"
      : `本批次已完成，共保存 ${detail.total_answers} 条回答。`;
  $("analysis-body").innerHTML=`
    <div class="analysis-title"><h3>${esc(answer?.question || detail.project.name)}</h3><span>批次 #${detail.batch.id} · ${esc(detail.batch.created_at.slice(0,10))}</span></div>
    <p class="analysis-status ${detail.batch.status==="failed" ? "is-error" : ""}">${badge(statuses[detail.batch.status],detail.batch.status==="failed" ? "red" : "blue")} ${esc(statusText)}</p>
    <article class="analysis-brands"><div><h3>⊕ 当前回答识别的品牌</h3><span>目标品牌：${badge(detail.project.brand)}</span></div>
      <div class="brand-pills">${brands.map(brand=>`<span>${esc(brand)}</span>`).join("") || '<span>当前回答未识别到词典内品牌</span>'}</div>
      <small>仅识别项目品牌词典；标签与右侧证据对应当前回答，汇总指标覆盖整个批次。</small></article>
    <div class="analysis-selection"><h3>选择回答</h3><span>${answer ? `当前第 ${offset+index+1} 条 / 共 ${detail.total_answers} 条` : "暂无已保存回答"}</span></div>
    <div class="analysis-answer-tabs" aria-label="选择要查看的回答">${detail.answers.map((item,i)=>`<button data-analysis-index="${i}" aria-pressed="${index===i}" class="${index===i ? "selected" : "secondary"}">${offset+i+1}. ${esc(item.model)}</button>`).join("")}</div>
    <div class="analysis-tools"><h3 class="evidence-title">对话原文与提取证据</h3><div>
      <button class="secondary" id="analysis-copy" ${answer ? "" : "disabled"}>复制回答原文</button>
      <button class="secondary" id="analysis-toggle" aria-expanded="${evidenceOpen}" aria-controls="analysis-evidence">${evidenceOpen ? "收起品牌证据" : "展开品牌证据"}</button>
    </div></div>
    <p id="analysis-feedback" role="status" aria-live="polite"></p>
    <div class="analysis-columns ${evidenceOpen ? "" : "evidence-collapsed"}">
      <article class="conversation-card"><header><strong>${esc(answer?.model || "暂无回答")} · 回答原文</strong>${badge(answer ? sources[answer.source] : "暂无数据",answer?.source==="mock" ? "amber" : "blue")}</header>
        <div class="conversation-body">${answer ? `<div class="user-bubble">${esc(answer.question)}</div><div class="model-answer"><pre>${esc(answer.answer)}</pre></div><small>采集日期：${esc(answer.collected_date || "未提供")} · 提取版本：${esc(answer.extractor_version)}</small>` : '<div class="analysis-empty"><strong>还没有可查看的回答</strong><p>执行中的批次可稍后刷新；失败批次请查看上方原因，再到运行监测页重新发起新批次。不会覆盖历史记录。</p></div>'}</div></article>
      <article class="analysis-evidence" id="analysis-evidence" ${evidenceOpen ? "" : "hidden"}><header><strong>当前回答 · 品牌证据</strong></header><div class="analysis-evidence-body">
        ${answer ? answer.extraction.map(e=>`<section><h4>${esc(e.brand)}</h4><p>提及 ${e.mentioned ? "是" : "否"} · 推荐 ${e.recommended ? "是" : "否"} · 排名 ${e.rank ?? "无明确编号"}</p>${e.evidence.map(text=>`<blockquote>${esc(text)}</blockquote>`).join("") || '<small>没有可引用的提取证据</small>'}</section>`).join("") : '<p>保存回答后才能提取品牌证据。</p>'}
        <section><h4>搜索引用信源 · 尚未提供</h4><p class="console-hint">本批次没有结构化搜索引用，不能验证网页来源；不把品牌知识库伪装成模型的联网引用。</p></section>
        <section><h4>整个批次汇总 · ${detail.metrics.sample_count} 条样本</h4>${detail.metrics.brands.map(b=>`<p>${esc(b.brand)}：提及 ${b.mention_count} 次 / 推荐 ${b.recommendation_count} 次</p>`).join("")}</section>
      </div></article>
    </div>
    <div class="analysis-footer"><button class="secondary" data-analysis-offset="${offset-20}" ${offset===0 ? "disabled" : ""}>上一页回答</button><span>本页 ${detail.answers.length ? offset+1 : 0}–${offset+detail.answers.length} / 共 ${detail.total_answers} 条</span><button class="secondary" data-analysis-offset="${offset+20}" ${offset+20>=detail.total_answers ? "disabled" : ""}>下一页回答</button><button class="secondary" id="analysis-refresh">刷新批次</button></div>`;
}
document.addEventListener("click",event=>{
  const button=event.target.closest('[data-monitor-action="analysis"]');if(button)perform(()=>openAnalysis(Number(button.dataset.batchId)),button);
  const index=event.target.closest("[data-analysis-index]");if(index){analysisState.index=Number(index.dataset.analysisIndex);renderAnalysis();document.querySelector(`[data-analysis-index="${analysisState.index}"]`).focus();}
  const offset=event.target.closest("[data-analysis-offset]");if(offset)perform(()=>openAnalysis(analysisState.batchId,Number(offset.dataset.analysisOffset)),offset);
  if(event.target.closest("#analysis-toggle")){
    analysisState.evidenceOpen=!analysisState.evidenceOpen;
    $("analysis-evidence").hidden=!analysisState.evidenceOpen;
    analysisDialog.querySelector(".analysis-columns").classList.toggle("evidence-collapsed",!analysisState.evidenceOpen);
    $("analysis-toggle").setAttribute("aria-expanded",String(analysisState.evidenceOpen));
    $("analysis-toggle").textContent=analysisState.evidenceOpen ? "收起品牌证据" : "展开品牌证据";
  }
  const refresh=event.target.closest("#analysis-refresh");if(refresh)perform(()=>openAnalysis(analysisState.batchId,analysisState.offset),refresh);
  const copy=event.target.closest("#analysis-copy");if(copy)copyAnalysisAnswer(copy);
});

async function copyAnalysisAnswer(button){
  const answer=analysisState?.detail.answers[analysisState.index];
  if(!answer || button.disabled)return;
  const feedback=$("analysis-feedback");
  button.disabled=true;
  try{
    // 仅复制用户当前选择的原文，不带提取标签、汇总指标或其他回答。
    await navigator.clipboard.writeText(answer.answer);
    feedback.textContent="回答原文已复制，可以直接粘贴。";
    feedback.className="";
  }catch{
    feedback.textContent="浏览器未允许复制，请在回答原文中选中文字后复制。";
    feedback.className="is-error";
  }finally{
    if(button.isConnected)button.disabled=false;
  }
}

const maintenancePanel=document.createElement("section");maintenancePanel.dataset.panel="maintenance";maintenancePanel.hidden=true;maintenancePanel.innerHTML='<div id="maintenance-content"></div>';guideMain.querySelector("footer").before(maintenancePanel);
let maintenanceState=null;
async function openMaintenance(projectId){
  const [project,questions,batches,documents]=await Promise.all([api(`/projects/${projectId}`),api(`/projects/${projectId}/questions`),api(`/projects/${projectId}/monitor-batches`),api(`/projects/${projectId}/knowledge/documents`)]);
  const profile=documents.find(d=>d.title === "品牌背景资料");
  const profileContent=profile ? await api(`/projects/${projectId}/knowledge/documents/${profile.id}`) : null;
  maintenanceState={projectId,profileContent};
  $("maintenance-content").innerHTML=`<article class="card maintenance-summary"><div>项目名称：<b>${esc(project.name)}</b><p>创建时间：${esc(project.created_at)}　最近更新：${esc(project.updated_at)}</p></div><button class="secondary" data-maintenance-history>监测历史</button></article><details class="card maintenance-section" open><summary>项目基本信息</summary><form id="maintenance-name-form" class="maintenance-field"><header><b>项目名称</b><button>保存名称</button></header><label>名称<input id="maintenance-name" required maxlength="100" value="${esc(project.name)}"></label></form><div class="maintenance-field"><header><b>项目状态</b>${badge(batches.length ? statuses[batches[0].status] : "草稿")}</header><p>状态取自最新执行批次，不允许手动伪造“运行中”或“已完成”。</p></div></details><details class="card maintenance-section" open><summary>品牌与背景资料</summary><div class="maintenance-field"><header><b>品牌词典（创建后固定）</b></header><p>目标品牌：${esc(project.brand)}</p><p>别名：${esc(project.aliases.join("、") || "未设置")}　竞品：${esc(project.competitors.join("、") || "未设置")}</p></div><form id="maintenance-profile-form" class="maintenance-field"><header><b>品牌背景摘要</b><button>保存资料新版本</button></header><label>背景资料<textarea id="maintenance-profile" rows="6" required maxlength="100000" placeholder="录入品牌定位、产品、目标用户和公开资料，不填写未核验的宣传结论">${esc(profileContent?.content || "")}</textarea></label><label>资料来源<input id="maintenance-profile-source" required maxlength="500" placeholder="公开页面地址或人工资料说明" value="${esc(profileContent?.source || "")}"></label><p>保存到品牌知识库，保留已有版本，不改变监测回答。资料内容由录入者核验。</p></form></details><details class="card maintenance-section" open><summary>核心问句与监测方式</summary><div class="maintenance-question-list">${questions.map(q=>`<div><span>${esc(q.text)}</span>${badge(q.enabled ? "启用" : "停用",q.enabled ? "green" : "amber")}<button class="secondary" data-maintenance-question="${q.id}" data-enable="${!q.enabled}">${q.enabled ? "停用" : "启用"}</button></div>`).join("") || '<p>尚未配置问句。点击下方进入运行监测添加。</p>'}</div><div class="maintenance-field"><header><b>已支持的监测方式</b></header><p>${badge("模拟适配器")} ${badge("CSV回答导入")}</p><p>手动执行，无自动监测周期；公共平台采集尚未接入。</p><button class="secondary" data-maintenance-run>管理问句 / 运行监测 →</button></div></details><details class="card maintenance-section"><summary>背景资料版本记录</summary>${documents.filter(d=>d.title === "品牌背景资料").map(d=>`<p>#${d.id} · ${esc(d.created_at)} · ${esc(d.source)}</p>`).join("") || '<p>暂无背景资料版本。</p>'}</details>`;
  form("maintenance-name-form",async()=>{await api(`/projects/${projectId}`,"PATCH",{name:$("maintenance-name").value});await openMaintenance(projectId);message("项目名称已保存");});
  form("maintenance-profile-form",async()=>{await api(`/projects/${projectId}/knowledge/documents`,"POST",{title:"品牌背景资料",source:$("maintenance-profile-source").value,content:$("maintenance-profile").value});await openMaintenance(projectId);message("品牌背景资料新版本已保存到知识库");});
  view("maintenance");
}
maintenancePanel.addEventListener("click",event=>{
  const button=event.target.closest("button");if(!button)return;const id=maintenanceState.projectId;
  if(button.hasAttribute("data-maintenance-history"))perform(()=>showHistory(id),button);
  if(button.hasAttribute("data-maintenance-run"))perform(async()=>{await openMonitor(id);goCollect();},button);
  if(button.dataset.maintenanceQuestion)perform(async()=>{await api(`/projects/${id}/questions/${button.dataset.maintenanceQuestion}`,"PATCH",{enabled:button.dataset.enable === "true"});await openMaintenance(id);},button);
});

// 创建助手是本地规则引导，不把表单交互冒充联网研究或模型推理。
const creationIntro=document.querySelector('[data-panel="setup"] .monitor-intro');
creationIntro.classList.add("agent-welcome");
creationIntro.innerHTML='<div class="agent-avatar" aria-hidden="true">G</div><div><h2>GEO 创建助手 · 品牌研究配置</h2><div class="agent-message"><p>你好，我是你的品牌研究助手，接下来会带你建立一个 GEO 数据监控项目。</p><p>我们先确认公司或产品名称、品牌别名和竞争品牌，再整理你希望向 AI 提出的核心问句，最后确定回答来源。你可以使用模拟演示熟悉流程，也可以导入自己采集并核验过的回答。</p><p>项目建立后，可以在「数据监控项目库」查看运行记录，比较品牌与竞品的提及情况，并回到原始回答核对证据。</p><p class="console-hint">当前是规则式配置助手，不会进行联网市场研究，不会自动采集公共平台或产生发布费用。</p></div></div>';
const creationCard=projectForm.closest("article");creationCard.classList.add("agent-creation-card");creationCard.querySelector("h2").hidden=true;creationCard.querySelector("p").hidden=true;
const wizardSteps=document.createElement("div");wizardSteps.className="wizard-steps";projectForm.before(wizardSteps);
const wizardConversation=document.createElement("div");wizardConversation.className="wizard-conversation";creationCard.before(wizardConversation);
const wizardBrand=document.createElement("div");wizardBrand.dataset.wizardPanel="0";
wizardBrand.append($("name").closest("label"),$("brand").closest("label"),optionalFields);
const wizardQuestions=document.createElement("div");wizardQuestions.dataset.wizardPanel="1";
wizardQuestions.append(questionsLabel);
wizardQuestions.insertAdjacentHTML("afterbegin",'<div class="agent-message"><p>品牌确定后，请确认想向 AI 提出的自然问句。可以分别覆盖通用推荐、品牌了解和竞品对比，但不要诱导它必须推荐目标品牌。</p></div>');
wizardQuestions.insertAdjacentHTML("beforeend",'<button type="button" id="suggest-questions" class="secondary">用当前品牌生成问句模板</button><div id="wizard-question-preview" class="question-category-preview"></div>');
const wizardConfig=document.createElement("div");wizardConfig.dataset.wizardPanel="2";
wizardConfig.innerHTML='<div class="agent-message"><p>问句准备好后，选择本次流程的执行方式。此处不是定时采集计划，不会自动产生平台费用。</p></div><div class="wizard-config-card"><h3>监测方式确认</h3><label class="wizard-mode"><input type="radio" name="wizard_mode" value="mock" checked><span><b>模拟演示</b><small>固定模拟适配器，免费验证流程。</small></span></label><label class="wizard-mode"><input type="radio" name="wizard_mode" value="import"><span><b>手动导入回答</b><small>收集完整回答后用 CSV 导入，来源由你声明。</small></span></label><h3>公共平台接入状态</h3><div class="platform-options"><span>豆包 · 未接入</span><span>通义千问 · 未接入</span><span>腾讯元宝 · 未接入</span><span>DeepSeek · 未接入</span></div><p class="console-hint">执行频率：手动运行。正式平台适配与定时任务尚未实现。</p></div><div id="wizard-review" class="wizard-review"></div>';
const wizardActions=document.createElement("div");wizardActions.className="wizard-actions";
const originalCreateButton=projectForm.querySelector('button:not([type="button"])');
originalCreateButton.textContent="确认配置并创建项目";
wizardActions.innerHTML='<button type="button" class="secondary" id="wizard-back">上一步</button><button type="button" id="wizard-next">确认并继续 →</button>';
wizardActions.append(originalCreateButton);projectForm.append(wizardBrand,wizardQuestions,wizardConfig,wizardActions);
let wizardIndex=0;
function renderWizard(){
  creationCard.dataset.step=String(wizardIndex);
  const confirmations=[`品牌已确认：${$("brand").value.trim()}。请继续配置核心问句。`,`已确认 ${$("initial-questions").value.split(/\n/).filter(line=>line.trim()).length} 条核心问句，请继续确认监测方式。`];
  wizardConversation.innerHTML=confirmations.slice(0,wizardIndex).map((text,index)=>`<div class="wizard-confirmed"><div><p>${esc(text)}</p><button type="button" class="secondary" data-wizard-return="${index}">修改${index===0 ? "品牌资料" : "核心问句"}</button></div><span aria-hidden="true">我</span></div>`).join("");
  wizardSteps.innerHTML=["确认品牌","确认核心问句","确认监测方式"].map((text,index)=>`<span class="${index === wizardIndex ? "active" : index < wizardIndex ? "done" : ""}"><b>${index+1}</b>${text}</span>`).join("");
  projectForm.querySelectorAll("[data-wizard-panel]").forEach(panel=>panel.hidden=Number(panel.dataset.wizardPanel)!==wizardIndex);
  // 隐藏步骤的输入不参与浏览器必填校验，但最终 API 仍完整校验全部配置。
  $("name").required=wizardIndex===0;$("brand").required=wizardIndex===0;$("initial-questions").required=wizardIndex===1;
  $("wizard-back").hidden=wizardIndex===0;$("wizard-next").hidden=wizardIndex===2;originalCreateButton.hidden=wizardIndex!==2;
  if(wizardIndex===1)renderQuestionPreview();
  if(wizardIndex===2)$("wizard-review").innerHTML=`<h3>本次项目确认</h3><p>项目：${esc($("name").value)}</p><p>品牌：${esc($("brand").value)}　竞品：${esc($("competitors").value.split(/\n/).filter(Boolean).join("、")||"未配置")}</p><p>问句数量：${$("initial-questions").value.split(/\n/).filter(line=>line.trim()).length} 条</p><p>确认后保存项目与问句，再进入运行监测页；不会直接执行付费任务。</p>`;
}
function wizardNext(){
  const fields=wizardIndex===0 ? [$("name"),$("brand")] : [$("initial-questions")];
  for(const input of fields)if(!input.checkValidity()){input.reportValidity();return;}
  if(wizardIndex===1){const questions=$("initial-questions").value.split(/\n/).map(s=>s.trim()).filter(Boolean);if(!questions.length||questions.length>100||questions.some(q=>q.length>500)){message("请填写1至100条问句，每条不超过500字。",true);return;}}
  wizardIndex=Math.min(2,wizardIndex+1);renderWizard();message("");
}
$("wizard-next").addEventListener("click",wizardNext);
$("wizard-back").addEventListener("click",()=>{wizardIndex=Math.max(0,wizardIndex-1);renderWizard();});
projectForm.addEventListener("submit",event=>{if(wizardIndex<2){event.preventDefault();event.stopImmediatePropagation();wizardNext();}},true);
function renderQuestionPreview(){
  const brand=$("brand").value.trim();const competitor=$("competitors").value.split(/\n/).find(s=>s.trim());
  $("wizard-question-preview").innerHTML=$("initial-questions").value.split(/\n/).filter(q=>q.trim()).map(q=>`<div><span>${badge(q.includes(brand)&&brand ? competitor&&q.includes(competitor.trim()) ? "竞品问句" : "品牌问句" : "通用问句")}</span><span>${esc(q)}</span></div>`).join("");
}
$("initial-questions").addEventListener("input",renderQuestionPreview);
$("suggest-questions").addEventListener("click",()=>{
  const brand=$("brand").value.trim(),competitor=$("competitors").value.split(/\n/).find(s=>s.trim());
  if(!brand){message("请先确认目标品牌。",true);return;}
  if($("initial-questions").value.trim()){message("已填写问句，保留你的内容不覆盖。可在下方直接调整。" );renderQuestionPreview();return;}
  $("initial-questions").value=`${brand}主要提供哪些产品或服务？\n${brand}适合哪些用户？\n${competitor ? `${brand}和${competitor.trim()}有哪些区别？` : `选择这类产品或服务时应该注意什么？`}`;
  renderQuestionPreview();message("已生成规则问句模板，不是模型研究结论，请按业务调整。");
});
document.addEventListener("workspace-view-changed",event=>{if(event.detail.name === "setup"){wizardIndex=0;renderWizard();}if(event.detail.name === "collect"){
  const mode=projectForm.elements.wizard_mode.value;
  questionCard.classList.toggle("preferred-mode",mode === "mock");importCard.classList.toggle("preferred-mode",mode === "import");
}});
renderWizard();

wizardConversation.addEventListener("click",event=>{
  const button=event.target.closest("[data-wizard-return]");if(!button)return;
  wizardIndex=Number(button.dataset.wizardReturn);renderWizard();creationCard.scrollIntoView({block:"start",behavior:"smooth"});
});

// 知识库与文章列表复用现有 API；界面不把资料摘录标成大模型生成文章。
const knowledgePanel=document.querySelector('[data-panel="knowledge"]');
const knowledgeEditor=document.createElement("details");knowledgeEditor.id="knowledge-editor";knowledgeEditor.className="console-editor";
knowledgeEditor.innerHTML='<summary>新增企业资料</summary>';
const knowledgeGrid=knowledgePanel.querySelector(".grid");
knowledgeEditor.append($("document-form").closest("article"));
const retrievalDetails=document.createElement("details");retrievalDetails.id="knowledge-retrieval";retrievalDetails.className="console-editor";
retrievalDetails.innerHTML='<summary>知识片段检索测试</summary>';
retrievalDetails.append($("retrieval-form").closest("article"));knowledgeGrid.remove();
knowledgePanel.prepend(knowledgeEditor);
knowledgePanel.append(retrievalDetails);
const knowledgeToolbar=document.createElement("div");knowledgeToolbar.className="monitor-toolbar";
knowledgeToolbar.innerHTML='<h2>企业知识库</h2><div><button type="button" class="secondary" id="knowledge-test">检索测试</button><button type="button" id="knowledge-new">＋ 新增资料</button></div>';
const knowledgeFilters=document.createElement("form");knowledgeFilters.className="card monitor-filters";
knowledgeFilters.innerHTML='<label>资料名称<input id="knowledge-search" placeholder="请输入资料标题或来源"></label><button>⌕ 查询</button><button type="reset" class="secondary">重置</button><span class="console-list-note" id="knowledge-total"></span>';
knowledgePanel.prepend(knowledgeToolbar,knowledgeFilters);
$("documents").closest("article").classList.add("monitor-table");
$("documents").closest("article").querySelector("h2").textContent="企业资料列表";
$("knowledge-new").addEventListener("click",()=>{knowledgeEditor.open=true;knowledgeEditor.scrollIntoView({block:"start",behavior:"smooth"});$("document-title").focus({preventScroll:true});});
$("knowledge-test").addEventListener("click",()=>{retrievalDetails.open=true;retrievalDetails.scrollIntoView({block:"start",behavior:"smooth"});$("query").focus({preventScroll:true});});
knowledgeFilters.addEventListener("submit",event=>{event.preventDefault();renderKnowledgeList();});
knowledgeFilters.addEventListener("reset",event=>{
  event.preventDefault();
  $("knowledge-search").value="";
  renderKnowledgeList();
});
const articlePanel=document.querySelector('[data-panel="content"]');
const articleEditor=document.createElement("details");articleEditor.id="article-editor";articleEditor.className="console-editor";
articleEditor.innerHTML='<summary>新建资料草稿 · 固定工作流</summary>';
articleEditor.append($("optimization-form").closest("article"));
articlePanel.prepend(articleEditor);
const articleToolbar=document.createElement("div");articleToolbar.className="monitor-toolbar";
articleToolbar.innerHTML='<h2>文章草稿与审核</h2><button type="button" id="article-new">＋ 新建草稿</button>';
articlePanel.prepend(articleToolbar);
$("runs").closest("article").classList.add("monitor-table");
$("runs").closest("article").querySelector("h2").textContent="草稿记录";
$("article-new").addEventListener("click",()=>{articleEditor.open=true;articleEditor.scrollIntoView({block:"start",behavior:"smooth"});$("target-query").focus({preventScroll:true});});
let consoleDocuments=[];
function renderKnowledgeList(){
  const query=$("knowledge-search").value.trim().toLocaleLowerCase();
  const documents=consoleDocuments.filter(item=>`${item.title} ${item.source}`.toLocaleLowerCase().includes(query));
  $("knowledge-total").textContent=`共 ${documents.length} 份资料`;
  $("documents").innerHTML=documents.length ? `<div class="table-wrap"><table><thead><tr><th>序号</th><th>资料名称</th><th>来源说明</th><th>知识片段</th><th>创建日期</th><th>操作</th></tr></thead><tbody>${documents.map((item,index)=>`<tr><td>${index+1}</td><td>${esc(item.title)}</td><td class="question-cell">${esc(item.source)}</td><td>${item.chunk_count} 个</td><td>${esc(item.created_at.slice(0,10))}</td><td><button type="button" class="secondary" data-document-id="${item.id}" data-document-project="${state.projectId}">查看原文</button></td></tr>`).join("")}</tbody></table></div>` : '<div class="monitor-empty"><strong>暂无匹配的企业资料</strong>点击「新增资料」录入品牌介绍、产品说明或 FAQ，并注明来源。</div>';
}
document.addEventListener("monitor-data-loaded",event=>{
  consoleDocuments=event.detail.documents;
  renderKnowledgeList();
  $("runs").innerHTML=event.detail.runs.length ? `<div class="table-wrap"><table><thead><tr><th>编号</th><th>目标问句</th><th>生成方式</th><th>审核状态</th><th>创建日期</th><th>操作</th></tr></thead><tbody>${event.detail.runs.map(run=>`<tr><td>#${run.id}</td><td class="question-cell">${esc(run.query)}</td><td>${badge("资料摘录草稿")}</td><td>${badge(run.review_status==="pending" ? "待审核" : statuses[run.review_status],run.review_status==="approved" ? "green" : run.review_status==="rejected" ? "red" : "amber")}</td><td>${esc(run.created_at.slice(0,10))}</td><td><button class="secondary" data-run="${run.id}">查看与审核</button></td></tr>`).join("")}</tbody></table></div>` : '<div class="monitor-empty"><strong>暂无草稿记录</strong>点击「新建草稿」，选择目标问句，基于企业资料生成可审核的摘录草稿。尚未接入大模型文章写作。</div>';
});
const documentDialog=document.createElement("dialog");documentDialog.className="monitor-dialog console-document-dialog";documentDialog.setAttribute("aria-labelledby","document-view-title");
documentDialog.innerHTML='<div class="analysis-heading"><h2 id="document-view-title">企业资料原文</h2><button type="button" id="document-view-close" aria-label="关闭企业资料原文">×</button></div><div id="document-view-body"></div>';
document.body.append(documentDialog);
$("document-view-close").addEventListener("click",()=>documentDialog.close());
$("documents").addEventListener("click",event=>{
  const button=event.target.closest("[data-document-id]");if(!button)return;
  perform(async()=>{
    const item=await api(`/projects/${button.dataset.documentProject}/knowledge/documents/${button.dataset.documentId}`);
    $("document-view-title").textContent=item.title;
    $("document-view-body").innerHTML=`<p>来源：${esc(item.source)}</p><p>创建时间：${esc(item.created_at)}</p><pre>${esc(item.content)}</pre>`;
    documentDialog.showModal();
  },button);
});
