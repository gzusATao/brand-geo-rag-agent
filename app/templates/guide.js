"use strict";
let guideData = null;
const guideMain = document.querySelector("main");
const guideHome = document.createElement("section");
const homeAgentTeam={
  supervisor:{name:"老大",english:"Skipper",role:"主管 · 任务调度",portraitX:237,portraitY:147,description:"识别你的目标，拆分任务，指挥小队协作。"},
  rag:{name:"科瓦斯基",english:"Kowalski",role:"检索 · 企业知识",portraitX:200,portraitY:57,description:"检索企业资料，核对片段，提供可追溯证据。"},
  tool:{name:"菜鸟",english:"Private",role:"工具 · 监测数据",portraitX:110,portraitY:163,description:"调用只读指标工具，区分真实、历史与模拟数据。"},
  summary:{name:"瑞科",english:"Rico",role:"摘要 · 结果汇总",portraitX:350,portraitY:124,description:"整合专业结果，提炼建议，整理最终答复。"}
};

function homeAgentPortrait(agent,decorative=false){
  // 直接对用户原图取景，不重绘；共享坐标保证角色卡与执行轨迹不会张冠李戴。
  return `<span class="home-agent-portrait" style="--portrait-x:${agent.portraitX}px;--portrait-y:${agent.portraitY}px"><img src="/static/assets/agents/penguin-team-reference.png" alt="${decorative?"":`${agent.name} · ${agent.english}，原图人物头像`}" width="478" height="360" decoding="async"></span>`;
}
guideHome.dataset.panel = "home";
guideHome.innerHTML = `
  <div class="home-stat-grid" aria-label="当前项目数据概览">
    <article><span>启用监测问句</span><strong id="home-question-count">—</strong><small>当前项目</small></article>
    <article><span>近期批次回答</span><strong id="home-answer-count">—</strong><small>最近100批次，含模拟</small></article>
    <article><span>企业资料数量</span><strong id="home-document-count">—</strong><small>当前项目知识库</small></article>
    <article><span>近期草稿记录</span><strong id="home-draft-count">—</strong><small>最多100条，含待审核</small></article>
  </div>
  <div class="home-feature-grid">
    <button type="button" class="secondary" data-guide="collect"><b><i>D</i> 数据监控 <span>›</span></b><small>配置监测问句，运行模拟或导入回答，查看品牌表现与原文证据。</small></button>
    <button type="button" class="secondary" data-home-view="knowledge"><b><i>K</i> 企业知识库 <span>›</span></b><small>整理企业介绍、产品说明与 FAQ，保留资料来源和可检索片段。</small></button>
    <button type="button" class="secondary" data-home-view="content"><b><i>S</i> 策略与内容草稿 <span>›</span></b><small>结合监测指标与知识片段整理草稿，当前使用固定摘录工作流。</small></button>
    <button type="button" class="secondary" data-home-view="content"><b><i>R</i> 人工审核与导出 <span>›</span></b><small>核对资料、修改草稿并保存审核记录，通过后导出，不自动发布。</small></button>
  </div>
  <article class="home-launch">
    <h2>GEO 品牌研究工作台</h2>
    <p class="home-launch-subtitle">从品牌数据到内容优化，让每一步都有原始证据。</p>
    <p class="home-launch-tagline"><span aria-hidden="true">✦</span> 一键开启 AI 品牌优化对话</p>
    <form id="home-launch-form" class="home-composer">
      <label for="home-brand" class="home-input-label">品牌研究问题或公司名称</label>
      <textarea id="home-brand" required maxlength="2000" rows="3" placeholder="告诉我你想优化什么，例如：分析当前品牌的可见性，结合企业资料提出改进建议。&#10;也可以继续追问，或让智能体整理一份有来源的内容草稿。&#10;请先在顶栏选择本次对话所属的品牌项目。" aria-describedby="home-task-description"></textarea>
      <div class="home-composer-footer">
        <label class="home-task-label">任务类型<select id="home-task"><option value="auto">启动 AI 自动 GEO · 多 Agent</option><option value="monitor">创建数据监控项目</option><option value="draft">整理企业资料草稿</option></select></label>
        <div class="home-creation-settings"><span>创作设置</span><div><button type="button" class="secondary" disabled title="当前尚未接入联网搜索">联网搜索 · 未接入</button><button type="button" class="secondary" data-home-view="knowledge">▤ 知识库</button></div></div>
        <button id="home-launch-submit" type="submit" aria-label="发送消息" title="发送消息，Ctrl + Enter 也可提交" disabled><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 20V4m-7 7 7-7 7 7"/></svg></button>
      </div>
    </form>
    <p id="home-task-description" class="home-task-description">发送将把本轮消息、近期对话、相关企业资料片段和监测汇总传给阿里云百炼。每轮最多3次模型调用，不自动发布。</p>
    <p id="home-model-status" class="home-task-description" role="status">正在检查百炼模型配置……</p>
    <p id="home-launch-feedback" role="status" aria-live="polite"></p>
    <button type="button" class="secondary" id="home-resume" hidden>继续未完成的配置 →</button>
    <section class="home-agent-team" aria-labelledby="home-agent-team-title"><div class="home-agent-team-heading"><h3 id="home-agent-team-title">你的企鹅特工小队</h3><p>四位专员，各司其职 · 按任务需要协作执行</p></div><div class="home-agent-team-grid">${Object.entries(homeAgentTeam).map(([id,agent])=>`<article class="home-agent-persona" data-agent-persona="${id}">${homeAgentPortrait(agent)}<h4>${agent.english}</h4><span class="home-agent-chinese-name">${agent.name}</span><span class="home-agent-role">${agent.role}</span><p>${agent.description}</p></article>`).join("")}</div></section>
    <section class="home-chat" aria-label="AI 品牌优化对话"><div class="home-chat-heading"><div><h3>AI 优化对话</h3><span id="home-chat-project">请先选择品牌项目</span></div><button type="button" class="secondary" id="home-new-chat">新对话</button></div><p class="home-chat-memory">近期对话保存在服务内存中，最多12轮；页面刷新将开启新的会话，服务重启不保留。这里只展示执行摘要，不展示模型内部思维链。</p><div id="home-chat-messages"><p class="home-chat-empty">发送问题后，主管 Agent 会按需调度知识检索和指标工具，再由摘要 Agent 汇总回复。</p></div><div id="home-agent-trace" aria-label="智能体执行过程"></div><p id="home-chat-status" role="status" aria-live="polite"></p><button type="button" class="secondary" id="home-chat-refresh" hidden>刷新当前任务进度</button></section>
    <div class="home-quick-actions"><button type="button" class="secondary" id="guide-primary" data-guide="start">继续当前项目 →</button><button type="button" class="secondary" data-guide="example">使用虚构示例</button></div>
  </article>
  <article class="card guide-next"><div><span class="guide-kicker">当前项目 · 下一步</span><h2 id="guide-next-title">还没有项目，先从一个品牌开始</h2><p id="guide-next-description">填写品牌名称后，确认项目资料与监测问句即可开始。</p></div><button data-guide="next" id="guide-next-button">开始创建</button></article>`;
guideMain.querySelector("footer").before(guideHome);
const guideNav = document.createElement("button");
guideNav.dataset.view = "home";
guideNav.textContent = "⌂ 开始使用";
guideNav.addEventListener("click",()=>view("home"));
document.querySelector("nav").prepend(guideNav);
const collectNav = document.createElement("button");
collectNav.dataset.view = "collect";
collectNav.textContent = "▷ 运行监测";
collectNav.addEventListener("click",()=>goCollect());
document.querySelector('nav [data-view="monitor"]').before(collectNav);
document.querySelector('nav [data-view="monitor"]').textContent = "▥ 查看监测结果";
const setupNav=document.querySelector('nav [data-view="setup"]');
const resultsNav=document.querySelector('nav [data-view="monitor"]');
const recordsNav=document.querySelector('nav [data-view="single"]');
const libraryNav=document.querySelector('nav [data-view="library"]');
setupNav.textContent="01 创建项目"; collectNav.textContent="02 运行监测"; resultsNav.textContent="03 查看结果";
recordsNav.textContent="分析记录"; libraryNav.textContent="项目管理";
menuGroup.after(setupNav,collectNav,resultsNav,recordsNav,libraryNav);

const collectPanel = document.createElement("section");
collectPanel.dataset.panel = "collect";
collectPanel.hidden = true;
collectPanel.innerHTML = '<div class="guide-collection-head"><div><span class="guide-kicker">第二步 · 获得回答</span><h2 id="collect-project">请先创建或选择项目</h2><p>首次使用建议先运行模拟演示，熟悉结果页后再导入实际回答。</p></div><button class="secondary" data-guide="results">查看已有结果 →</button></div>';
const monitorPanel = document.querySelector('[data-panel="monitor"]');
collectPanel.append(monitorPanel.querySelector(".grid"));
collectPanel.append($("batches").closest("article"));
guideMain.querySelector("footer").before(collectPanel);
const questionCard = $("question-form").closest("article");
questionCard.querySelector("h2").textContent = "方式一：模拟演示（不花钱）";
const mockExplanation = document.createElement("p");
mockExplanation.className = "guide-help";
mockExplanation.textContent = "使用当前启用的问句生成固定模拟回答，检查分析流程。不会请求豆包、千问等平台，也不能用于证明优化效果。";
questionCard.querySelector("h2").after(mockExplanation);
$("mock").textContent = "运行模拟演示，查看结果 →";
$("mock").classList.remove("secondary");
$("question-form").querySelector("label").firstChild.textContent = "补充监测问句";
$("question-form").querySelector("button").textContent = "保存问句";
const importCard = $("csv").closest("article");
importCard.querySelector("h2").textContent = "方式二：导入已有回答";
importCard.querySelector("p").textContent = "把你在 AI 平台获得的完整回答整理成 CSV。上传后会自动提取品牌证据并进入结果页；本版不能直接替你采集公共平台。";
const template = document.createElement("button");
template.type = "button";
template.className = "secondary";
template.textContent = "↓ 下载 CSV 示例模板";
template.addEventListener("click",()=>{
  const csv = '\ufeffquestion,answer,model,source,collected_date\n"适合小团队的协作工具有哪些？","【模拟示例】推荐星河协作作为候选方案。","示例模拟器",mock,\n';
  const url=URL.createObjectURL(new Blob([csv],{type:"text/csv;charset=utf-8"}));
  const link=document.createElement("a"); link.href=url; link.download="回答导入模板-模拟示例.csv"; link.click(); setTimeout(()=>URL.revokeObjectURL(url),1000);
});
$("csv").before(template);
$("import").textContent = "上传并分析回答 →";
$("csv").setAttribute("aria-label","选择 UTF-8 CSV 回答文件");
const fileHint=document.createElement("p");fileHint.id="csv-selection";fileHint.className="guide-help";fileHint.setAttribute("aria-live","polite");
$("csv").after(fileHint);$("csv").setAttribute("aria-describedby","csv-selection");
function updateCollectControls(){
  const file=$("csv").files[0],busy=$("import").getAttribute("aria-busy")==="true";
  const valid=Boolean(file&&/\.csv$/i.test(file.name)&&file.size>0&&file.size<=500000);
  $("import").disabled=busy||!state.projectId||!valid;
  fileHint.textContent=!file ? "先选择 CSV 文件，再导入。UTF-8 编码，最多 500 条、500KB。" : !valid ? "文件不符合要求：请选择非空 CSV 文件，大小不超过 500KB。" : `已选择：${file.name}（${Math.ceil(file.size/1000)}KB），可开始导入。`;
  $("mock").disabled=$("mock").getAttribute("aria-busy")==="true"||!state.projectId||!state.questions.some(q=>q.enabled);
  $("mock").title=state.questions.some(q=>q.enabled) ? "仅生成模拟样本，不调用付费平台" : "请先添加至少一条启用的监测问句";
}
$("csv").addEventListener("change",updateCollectControls);
document.addEventListener("workspace-action-finished",updateCollectControls);
document.addEventListener("workspace-ready",updateCollectControls);
document.addEventListener("monitor-data-loaded",updateCollectControls);
updateCollectControls();
importCard.querySelector("details").innerHTML = '<summary>每一列应该怎么填？</summary><dl class="guide-columns"><dt>question</dt><dd>你向 AI 提出的完整问句。</dd><dt>answer</dt><dd>原始回答，不要只留下品牌相关片段。</dd><dt>model</dt><dd>回答来自哪个平台或模型，由你填写。</dd><dt>source</dt><dd>real 为本次实际回答；historical 为历史回答；mock 为模拟样本。请如实标注。</dd><dt>collected_date</dt><dd>采集日期，如 2026-09-29；没有记录可以留空。</dd></dl><p>用表格软件编辑后另存为 UTF-8 CSV，最多500行、500KB。示例模板的内容是模拟数据，不要改成真实来源。</p>';

const projectForm = $("project-form");
const questionsLabel = document.createElement("label");
questionsLabel.textContent = "你希望向 AI 提什么问题？（每行一条）";
questionsLabel.innerHTML += '<textarea id="initial-questions" required rows="4" placeholder="例如：适合小团队的协作工具有哪些？\n星河协作和云帆办公有什么区别？"></textarea><small class="guide-help">建议先填1～3条。使用自然问句，不要要求 AI 必须推荐你的品牌。</small>';
const optionalFields = document.createElement("details");
optionalFields.innerHTML = '<summary>选填：品牌别名与竞品</summary>';
for(const id of ["aliases","competitors"]) optionalFields.append($(id).closest("label"));
projectForm.querySelector("button").before(questionsLabel,optionalFields);
projectForm.querySelector("button").textContent = "保存项目与问句，下一步 →";
document.querySelector('[data-panel="setup"] .monitor-intro').innerHTML = '<span class="guide-kicker">第一步 · 一次填好</span><h2>选择一个品牌，写下你想研究的问题</h2><p>下方保存后会进入运行监测页，不需要再到别的页面找添加问句的入口。</p><button type="button" class="secondary" data-guide="example">不知道怎么填？使用虚构示例</button>';
$("name").placeholder="例如：星河协作品牌可见性研究";
$("brand").placeholder="例如：星河协作（填写完整品牌名称）";

const resultHelp = document.createElement("article");
resultHelp.className="guide-result-help";
resultHelp.innerHTML='<div><span class="guide-kicker">第三步 · 解读结果</span><h2>先看指标，再展开原始回答核对</h2><p>提及率＝出现品牌的回答数 ÷ 当前样本数；推荐率来自保守规则判断，需要人工确认。没有明确编号，就不会给品牌硬排位。</p></div><button data-guide="collect" class="secondary">再运行一次 / 导入回答</button>';
monitorPanel.prepend(resultHelp);
const resultEmpty = document.createElement("div");
resultEmpty.id="guide-result-empty";
resultEmpty.className="card guide-next";
resultEmpty.innerHTML='<div><h2>这个筛选范围还没有回答</h2><p>已有模拟结果时，把来源切到“模拟回答”；也可以新运行一次或导入回答。</p></div><button data-guide="collect">去运行监测 →</button>';
monitorPanel.querySelector(".stats").after(resultEmpty);

function goCollect() {
  if(!state.projectId) {view("setup"); message("先填写品牌和问句，保存后就能运行监测。"); return;}
  view("collect");
}
function updateHomeTask(){
  updateHomeSendControl();
  const auto=$("home-task").value==="auto";
  $("home-brand").maxLength=auto ? 2000 : 100;
  $("home-launch-submit").setAttribute("aria-label",auto ? "发送消息" : "开始配置");
  $("home-launch-submit").title=auto ? "发送消息，Ctrl + Enter 也可提交" : "开始配置，Ctrl + Enter 也可提交";
  $("home-brand").placeholder=auto ? "告诉我你想优化什么，例如：分析当前品牌的可见性，结合企业资料提出改进建议。\n也可以继续追问，或让智能体整理一份有来源的内容草稿。\n请先在顶栏选择本次对话所属的品牌项目。" : "请输入公司或产品名称，进入项目配置或现有资料草稿流程。";
  const descriptions={
    auto:"发送将把本轮消息、近期对话、相关企业资料片段和监测汇总传给阿里云百炼。每轮最多3次模型调用，不自动发布。",
    monitor:"填写品牌后进入项目配置，确认核心问句，再选择模拟监测或导入已有回答。",
    draft:"名称匹配当前项目时进入草稿页；其他品牌先建立项目。草稿仍使用固定摘录工作流。"
  };
  $("home-task-description").textContent=descriptions[$("home-task").value];
  $("home-launch-feedback").textContent="";$("home-resume").hidden=true;
}
$("home-brand").addEventListener("input",updateHomeTask);
$("home-task").addEventListener("change",updateHomeTask);
$("home-brand").addEventListener("keydown",event=>{
  if(event.key==="Enter"&&(event.ctrlKey||event.metaKey)&&!event.isComposing){event.preventDefault();$("home-launch-form").requestSubmit();}
});
$("home-resume").addEventListener("click",()=>view("setup"));
form("home-launch-form",async()=>{
  if($("home-task").value==="auto"){await sendHomeChat();return;}
  const brand=$("home-brand").value.trim().replace(/\s+/g," "),task=$("home-task").value;
  if(!brand){$("home-launch-feedback").textContent="请先填写公司或产品名称。";return;}
  if(brand.length>100){$("home-launch-feedback").textContent="公司或产品名称最多100字，请精简后再进入配置。";return;}
  const project=guideData?.project;
  const matches=project&&[project.brand,...project.aliases].some(name=>name.toLocaleLowerCase()===brand.toLocaleLowerCase());
  if(task==="draft"&&matches){
    view("content");
    if(!$("target-query").value.trim())$("target-query").value=`${project.brand}主要提供哪些产品或服务？`;
    $("article-new").click();
    message("已进入当前项目的草稿配置，请确认目标问句后执行；本次未自动生成或发布文章。");
    return;
  }
  // 首页只填充配置，不直接建库；切换品牌不能悄悄覆盖创建页尚未保存的词典和问句。
  const configuredBrand=$("brand").value.trim();
  if(configuredBrand&&configuredBrand.toLocaleLowerCase()!==brand.toLocaleLowerCase()){
    $("home-launch-feedback").textContent=`创建页还有「${configuredBrand}」的未保存配置。请先继续处理，不会覆盖你的资料。`;
    $("home-resume").hidden=false;return;
  }
  $("brand").value=brand;
  if(!$("name").value.trim())$("name").value=`${brand} · ${task==="monitor" ? "品牌监测" : "GEO 优化研究"}`.slice(0,100);
  view("setup");
  message(task==="auto" ? "品牌已带入，尚未保存。请确认品牌、核心问句和监测方式；多 Agent 自动执行尚未接入。" : "品牌已带入，尚未保存。请完成项目配置，再运行监测或整理草稿。");
});
const homeChatState={projectId:null,sessionId:null,messages:[],run:null,runId:null,busy:false,revision:0};
function updateHomeSendControl(){
  $("home-launch-submit").disabled=!$("home-brand").value.trim()||homeChatState.busy||Boolean(homeChatState.runId);
  $("home-task").disabled=homeChatState.busy||Boolean(homeChatState.runId);
  $("home-new-chat").disabled=homeChatState.busy||Boolean(homeChatState.runId);
}
function renderHomeChat(){
  $("home-chat-messages").innerHTML=homeChatState.messages.length ? homeChatState.messages.map(item=>`<article class="home-chat-message ${item.role}"><span class="home-chat-avatar">${item.role==="user" ? "你" : item.role==="error" ? "!" : "GEO"}</span><div><b>${item.role==="user" ? "你" : item.role==="error" ? "系统提示" : "多 Agent 助理"}</b><div class="home-chat-text">${esc(item.content)}</div>${(item.citations||[]).map(citation=>`<details class="home-chat-citation"><summary>[${citation.chunk_id}] ${esc(citation.title)}</summary><p>来源：${esc(citation.source)}</p><blockquote>${esc(citation.text)}</blockquote></details>`).join("")}</div></article>`).join("") : '<p class="home-chat-empty">发送问题后，主管 Agent 会按需调度知识检索和指标工具，再由摘要 Agent 汇总回复。</p>';
  const statusNames={pending:"等待",running:"执行中",completed:"完成",skipped:"未执行",failed:"失败"};
  $("home-agent-trace").innerHTML=homeChatState.run ? `<div class="home-agent-heading">本轮执行过程 <small>#${homeChatState.run.id.slice(0,8)}</small></div><div class="home-agent-steps">${homeChatState.run.trace.map(step=>{const agent=homeAgentTeam[step.agent];return `<div class="home-agent-step ${step.status}"><div class="home-agent-step-head">${homeAgentPortrait(agent,true)}<div><b>${agent.name} · ${agent.english}</b><small>${agent.role}</small></div></div><span>${statusNames[step.status]}</span><p>${esc(step.summary)}</p></div>`;}).join("")}</div>` : "";
  $("home-chat-refresh").hidden=!homeChatState.runId||homeChatState.busy;
  updateHomeSendControl();
}
async function sendHomeChat(){
  const text=$("home-brand").value.trim();
  if(!text||homeChatState.busy||homeChatState.runId)return;
  if(!state.projectId){$("home-launch-feedback").textContent="请先创建或在顶栏选择品牌项目。可把任务类型切换到「创建数据监控项目」。";return;}
  const projectId=state.projectId,revision=homeChatState.revision;
  homeChatState.busy=true;$("projects").disabled=true;updateHomeSendControl();
  $("home-chat-status").textContent="正在提交任务……";
  try{
    const run=await api(`/projects/${projectId}/agent-chat`,"POST",{message:text,session_id:homeChatState.sessionId});
    if(revision!==homeChatState.revision)return;
    homeChatState.sessionId=run.session_id;homeChatState.runId=run.id;homeChatState.run=run;
    homeChatState.messages.push({role:"user",content:text});$("home-brand").value="";
    renderHomeChat();
    $("home-chat-messages").lastElementChild?.scrollIntoView({block:"nearest",behavior:"smooth"});
    await pollHomeChat(projectId,revision);
  }catch(error){
    if(revision===homeChatState.revision){
      if(error.status===404){homeChatState.runId=null;homeChatState.sessionId=null;}
      $("home-chat-status").textContent=error.message;
      $("home-chat-status").scrollIntoView({block:"nearest",behavior:"smooth"});
    }
  }finally{
    if(revision===homeChatState.revision){homeChatState.busy=false;renderHomeChat();}
    $("projects").disabled=homeChatState.busy;
  }
}
async function pollHomeChat(projectId,revision){
  for(let attempt=0;attempt<135;attempt++){
    if(revision!==homeChatState.revision)return;
    const run=await api(`/projects/${projectId}/agent-chat/${homeChatState.runId}`);
    if(revision!==homeChatState.revision)return;
    homeChatState.run=run;renderHomeChat();
    if(["completed","failed"].includes(run.status)){
      homeChatState.messages.push({role:run.status==="completed" ? "assistant" : "error",content:run.answer||run.error,citations:run.citations});
      homeChatState.runId=null;
      $("home-chat-status").textContent=run.status==="completed" ? "本轮已完成，可以继续追问。模型内容仍需人工核对。" : "本轮未成功，不会将失败结果写入模型对话记忆；可重新发送。";
      renderHomeChat();return;
    }
    $("home-chat-status").textContent="智能体正在执行，可在下方查看各角色的进度……";
    await new Promise(resolve=>setTimeout(resolve,1000));
  }
  $("home-chat-status").textContent="本轮暂未返回最终结果。点击刷新进度查询，不会重复提交模型任务。";
}
$("home-chat-refresh").addEventListener("click",async()=>{
  if(!homeChatState.runId||homeChatState.busy)return;
  const revision=homeChatState.revision;
  homeChatState.busy=true;$("projects").disabled=true;renderHomeChat();
  try{await pollHomeChat(state.projectId,revision);}catch(error){
    if(revision===homeChatState.revision){
      if(error.status===404){homeChatState.runId=null;homeChatState.sessionId=null;}
      $("home-chat-status").textContent=error.message;
    }
  }
  finally{if(revision===homeChatState.revision){homeChatState.busy=false;renderHomeChat();}$("projects").disabled=homeChatState.busy;}
});
$("home-new-chat").addEventListener("click",()=>{
  if(homeChatState.busy||homeChatState.runId)return;
  homeChatState.sessionId=null;homeChatState.messages=[];homeChatState.run=null;homeChatState.revision++;
  $("home-chat-status").textContent="已开启新对话。旧会话将在服务内存中过期，不影响企业资料和监测记录。";
  renderHomeChat();
});
document.addEventListener("workspace-action-finished",updateHomeSendControl);
document.addEventListener("monitor-data-loaded",event=>{
  if(homeChatState.projectId!==event.detail.projectId){
    Object.assign(homeChatState,{projectId:event.detail.projectId,sessionId:null,messages:[],run:null,runId:null,busy:false,revision:homeChatState.revision+1});
    $("home-chat-status").textContent="已切换品牌项目，当前对话上下文已清空。";renderHomeChat();
  }
  $("home-chat-project").textContent=`当前项目：${event.detail.project.name}`;
});
document.addEventListener("workspace-ready",()=>perform(async()=>{
  const config=await api("/agent-chat/config");
  $("home-model-status").textContent=`${config.provider} · ${config.model} · ${config.configured ? "已配置，首次调用将验证连通性" : "尚未配置密钥，请运行本地模型配置脚本"}`;
}));
guideHome.addEventListener("click",event=>{
  const button=event.target.closest("[data-home-view]");if(!button)return;
  if(!state.projectId){$("home-launch-feedback").textContent="请先创建或在顶栏选择品牌项目，再管理企业资料与草稿。";return;}
  view(button.dataset.homeView);
});
function updateGuide() {
  const enabled=state.questions.filter(q=>q.enabled).length;
  $("home-question-count").textContent=String(enabled);
  $("home-answer-count").textContent=guideData ? guideData.batches.reduce((count,batch)=>count+batch.completed,0).toLocaleString("zh-CN") : "0";
  $("home-document-count").textContent=String(guideData?.documents.length || 0);
  $("home-draft-count").textContent=String(guideData?.runs.length || 0);
  $("guide-primary").textContent=state.projectId ? "继续当前项目 →" : "创建第一个项目 →";
  $("collect-project").textContent=guideData ? `${guideData.project.name} · ${enabled} 条启用问句` : "请先创建或选择项目";
  if(!state.projectId) return;
  const latest=guideData?.batches.find(b=>b.status === "completed");
  $("guide-next-title").textContent=guideData ? guideData.project.name : "当前品牌项目";
  $("guide-next-description").textContent=latest ? `已有完成批次 #${latest.id}，共 ${latest.completed} 条回答。可以查看证据，也可以继续运行或导入。` : enabled ? `已准备好 ${enabled} 条问句。现在选择模拟演示，或上传你收集的回答。` : "还没有启用问句。进入运行监测页，添加一条问句后即可开始。";
  $("guide-next-button").textContent=latest ? "查看最新结果 →" : "进入运行监测 →";
  $("guide-result-empty").hidden=Boolean(guideData?.metrics.sample_count);
}
document.addEventListener("click",event=>{
  const button=event.target.closest("[data-guide]"); if(!button)return;
  const action=button.dataset.guide;
  if(action === "example") {
    view("setup"); $("name").value="星河协作 · 模拟流程体验"; $("brand").value="星河协作"; $("aliases").value="星河"; $("competitors").value="云帆办公";
    $("initial-questions").value="适合小团队的协作工具有哪些？\n星河协作和云帆办公有什么区别？\n选择协作工具时应该关注什么？";
    message("已填写虚构示例，尚未保存。依次确认品牌、核心问句与监测方式后，才会创建项目。"); return;
  }
  if(action === "start" || action === "collect") return goCollect();
  if(action === "results" || action === "next") {
    const latest=guideData?.batches.find(b=>b.status === "completed");
    if(latest) return perform(()=>openMonitor(state.projectId,latest.id,latest.source),button);
    return goCollect();
  }
});
document.addEventListener("monitor-data-loaded",event=>{guideData=event.detail; updateGuide();});
document.addEventListener("workspace-ready",()=>updateGuide());
document.addEventListener("workspace-view-changed",event=>{
  const descriptions={home:"按步骤完成第一次监测，不需要先读接口文档。",setup:"填好品牌和问句，一次保存即可开始。",collect:"模拟演示用于熟悉流程；实际研究请导入你核验过的回答。",monitor:"指标只针对当前来源和批次，不等于全平台的品牌表现。",single:"这里保存运行和导入记录；首次使用请从“开始使用”进入。",library:"管理已有品牌项目，进入后可以运行监测并查看结果。"};
  if(descriptions[event.detail.name]) $("subtitle").textContent=descriptions[event.detail.name];
});
view("home");
