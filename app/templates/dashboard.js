"use strict";
const dashboardState={projectId:null,question:"",model:"",offset:0,revision:0,metric:"mention_rate",data:null};
const dashboardPanel=document.createElement("div");dashboardPanel.className="geo-dashboard";
dashboardPanel.innerHTML=`<article class="dashboard-project"><h2 id="dashboard-brand">品牌监控数据</h2><span id="dashboard-range">按实际回答统计</span></article><form id="dashboard-filter" class="dashboard-filter"><div class="dashboard-dates"><label>时间范围<input id="dashboard-start" type="date" aria-label="看板开始日期"></label><span>—</span><input id="dashboard-end" type="date" aria-label="看板结束日期"><button>查询</button><button type="button" class="secondary" id="dashboard-reset">重置</button></div><div class="dashboard-actions"><button type="button" class="secondary" id="dashboard-records">监测记录</button><button type="button" class="secondary" id="dashboard-export">导出当前统计</button></div></form><div class="dashboard-layout"><article class="dashboard-card dashboard-wide"><h3>品牌可见性分布</h3><div class="dashboard-kpis" id="dashboard-kpis"></div></article><article class="dashboard-card"><h3>显式推荐位置分布</h3><div id="dashboard-ranks"></div><p class="dashboard-small">没有明确编号的回答不会强行排名。</p></article><article class="dashboard-card dashboard-wide"><div class="dashboard-card-head"><h3 id="dashboard-trend-title">品牌提及率趋势</h3><div><button type="button" data-dashboard-metric="mention_rate" class="selected">提及率</button><button type="button" data-dashboard-metric="recommendation_rate">推荐率</button></div></div><div id="dashboard-models" class="dashboard-pills"></div><div id="dashboard-trend"></div><p id="dashboard-date-basis" class="dashboard-small"></p></article><article class="dashboard-card"><div class="dashboard-card-head"><h3>监测问句</h3><button type="button" data-dashboard-question="">全部</button></div><p class="dashboard-small">点击问句切换指标、趋势和回答记录</p><div id="dashboard-questions" class="dashboard-question-pills"></div></article><article class="dashboard-card"><h3>回答来源分布</h3><div id="dashboard-sources"></div><p class="dashboard-small">来源由采集者声明；模型标识不代表已接入平台。</p></article><article class="dashboard-card dashboard-wide"><div class="dashboard-card-head"><h3>原始回答与证据</h3><span id="dashboard-total"></span></div><div id="dashboard-record-list"></div><div class="dashboard-record-pages"><button type="button" class="secondary" id="dashboard-prev">上一页</button><span id="dashboard-page"></span><button type="button" class="secondary" id="dashboard-next">下一页</button></div></article></div>`;
// 原始明细保留在折叠区，常用图表与记录成为数据页主体。
const advanced=document.createElement("details");advanced.className="dashboard-advanced";advanced.innerHTML='<summary>查看原版详细指标与证据</summary>';
for(const element of [monitorPanel.querySelector(".stats"),$("metrics").closest("article"),$("answers").closest("article")])advanced.append(element);
monitorPanel.append(dashboardPanel,advanced);
const dashboardLoading=document.createElement("p");dashboardLoading.className="dashboard-loading";dashboardLoading.setAttribute("role","status");dashboardLoading.setAttribute("aria-live","polite");dashboardLoading.hidden=true;
dashboardPanel.querySelector(".dashboard-layout").before(dashboardLoading);
$("dashboard-reset").textContent="重置看板筛选";
$("dashboard-reset").title="清除日期、问句和模型筛选，保留上方的批次与来源";
$("dashboard-records").textContent="查看监测历史";
$("dashboard-export").textContent="导出统计摘要";
resultHelp.hidden=true;
$("guide-result-empty").hidden=true;
function dashboardPercent(value,count){return count ? `${(value*100).toFixed(1)}%` : "—";}
async function loadDashboard(){
  if(!state.projectId){$("dashboard-record-list").innerHTML='<div class="dashboard-empty">先创建项目，再运行监测或导入回答。</div>';return;}
  if(dashboardState.projectId!==state.projectId){dashboardState.projectId=state.projectId;dashboardState.question="";dashboardState.model="";dashboardState.offset=0;}
  const revision=++dashboardState.revision,params=new URLSearchParams();
  if($("source").value)params.set("source",$("source").value);
  if(state.batchId)params.set("batch_id",state.batchId);
  for(const [name,id] of [["start_date","dashboard-start"],["end_date","dashboard-end"]])if($(id).value)params.set(name,$(id).value);
  if(dashboardState.question)params.set("question",dashboardState.question);
  if(dashboardState.model)params.set("model",dashboardState.model);
  params.set("offset",dashboardState.offset);
  // 导出沿用实际查询的口径，不能把尚未点击查询的日期写进旧结果。
  const applied={brand:guideData?.project.brand||"品牌",source:$("source").value,batch:state.batchId,question:dashboardState.question,model:dashboardState.model,start:$("dashboard-start").value,end:$("dashboard-end").value};
  $("dashboard-export").disabled=true;
  dashboardPanel.setAttribute("aria-busy","true");dashboardLoading.hidden=false;dashboardLoading.textContent="正在更新统计，请稍候……";
  let data;
  try{data=await api(path(`/monitor-dashboard?${params}`));}
  catch(error){if(revision===dashboardState.revision)dashboardLoading.textContent="统计更新失败，当前仍是上次结果。请检查筛选后重新查询。";throw error;}
  finally{if(revision===dashboardState.revision)dashboardPanel.removeAttribute("aria-busy");}
  if(revision!==dashboardState.revision)return;
  if(!data.answers.length&&dashboardState.offset){dashboardState.offset=0;return loadDashboard();}
  dashboardState.data=data;dashboardState.applied=applied;renderDashboard(data);$("dashboard-export").disabled=!data.total;dashboardLoading.hidden=true;
}
function renderDashboard(data){
  const target=data.metrics.brands[0],count=data.total;
  $("dashboard-brand").textContent=guideData?.project.brand || target.brand;
  $("dashboard-range").textContent=count ? `${count} 条回答 · ${state.batchId ? `批次 #${state.batchId}` : "全部批次"} · ${$("source").value ? sources[$("source").value]+"来源" : "混合来源"}` : "当前筛选暂无回答";
  $("dashboard-kpis").innerHTML=[["品牌提及率",target.mention_rate,"green",`${target.mention_count} 条回答明确提及`],["规则推荐率",target.recommendation_rate,"blue",`${target.recommendation_count} 条回答识别出推荐`],["未提及率",count ? 1-target.mention_rate : 0,"red",`${count-target.mention_count} 条回答未提及`]].map(([title,value,tone,note])=>`<div class="dashboard-kpi ${tone}"><span>${title}</span><b>${dashboardPercent(value,count)}</b><div class="dashboard-progress"><i style="width:${count ? Math.max(0,Math.min(100,value*100)) : 0}%"></i></div><small>${note}</small></div>`).join("");
  $("dashboard-ranks").innerHTML=Object.entries(data.rank_counts).map(([name,number],i)=>`<div class="dashboard-rank"><span>${esc(name)}</span><div><i class="rank-${i}" style="width:${count ? number/count*100 : 0}%"></i></div><b>${number} 条</b></div>`).join("");
  $("dashboard-models").innerHTML=`<button type="button" data-dashboard-model="" class="${!dashboardState.model ? "selected" : ""}">全部模型</button>`+data.models.map(item=>`<button type="button" data-dashboard-model="${esc(item.model)}" class="${dashboardState.model===item.model ? "selected" : ""}">${esc(item.model)}</button>`).join("");
  $("dashboard-questions").innerHTML=data.questions.map(item=>`<button type="button" data-dashboard-question="${esc(item.question)}" class="${dashboardState.question===item.question ? "selected" : ""}">${esc(item.question)} <small>${item.sample_count}条</small></button>`).join("")||'<p class="dashboard-small">此范围暂无问句回答。请先运行或导入。</p>';
  dashboardPanel.querySelectorAll("[data-dashboard-question]").forEach(button=>{const selected=button.dataset.dashboardQuestion===dashboardState.question;button.classList.toggle("selected",selected);button.setAttribute("aria-pressed",String(selected));});
  dashboardPanel.querySelectorAll("[data-dashboard-model]").forEach(button=>button.setAttribute("aria-pressed",String(button.dataset.dashboardModel===dashboardState.model)));
  $("dashboard-range").textContent+=[dashboardState.question ? "已筛选问句" : "",dashboardState.model].filter(Boolean).map(text=>` · ${text}`).join("");
  $("dashboard-sources").innerHTML=Object.entries(data.metrics.source_counts).map(([source,number])=>`<div class="dashboard-source"><span>${sources[source]}回答</span><div class="dashboard-progress"><i style="width:${count ? number/count*100 : 0}%"></i></div><b>${number} 条</b></div>`).join("");
  $("dashboard-total").textContent=`共 ${count} 条`;
  $("dashboard-record-list").innerHTML=data.answers.length ? `<div class="table-wrap"><table><thead><tr><th>采样日期</th><th>问句 / 模型</th><th>目标品牌</th><th>来源</th><th>操作</th></tr></thead><tbody>${data.answers.map(answer=>{const e=answer.extraction.find(item=>item.brand===target.brand);return `<tr><td>${esc(answer.collected_date||answer.created_at.slice(0,10))}</td><td class="dashboard-question-cell">${esc(answer.question)}<small>${esc(answer.model)}</small></td><td>${badge(e.mentioned ? "已提及" : "未提及",e.mentioned ? "green" : "amber")}</td><td>${badge(sources[answer.source],answer.source === "mock" ? "amber" : "blue")}</td><td><button type="button" class="secondary" data-dashboard-answer="${answer.id}">查看原文</button></td></tr>`;}).join("")}</tbody></table></div>` : '<div class="dashboard-empty">当前筛选暂无回答。请调整时间、来源，或进入“运行监测”导入回答。</div>';
  $("dashboard-prev").disabled=dashboardState.offset===0;$("dashboard-next").disabled=dashboardState.offset+20>=count;
  $("dashboard-page").textContent=`${Math.floor(dashboardState.offset/20)+1} / ${Math.max(1,Math.ceil(count/20))}`;
  $("dashboard-date-basis").textContent=data.date_basis;
  drawDashboardTrend();
}
function drawDashboardTrend(){
  const data=dashboardState.data;if(!data)return;
  const points=data.trend.slice(-60),metric=dashboardState.metric;
  $("dashboard-trend-title").textContent=metric === "mention_rate" ? "品牌提及率趋势" : "规则推荐率趋势";
  if(!points.length){$("dashboard-trend").innerHTML='<div class="dashboard-empty">没有可绘制的样本。未采样不等于指标为零。</div>';return;}
  const width=800,height=250,left=45,right=18,top=22,bottom=52;
  const coordinates=points.map((point,index)=>[left+(points.length===1 ? (width-left-right)/2 : index*(width-left-right)/(points.length-1)),top+(1-point[metric])*(height-top-bottom)]);
  const lines=[0,25,50,75,100].map(value=>{const y=top+(1-value/100)*(height-top-bottom);return `<line x1="${left}" y1="${y}" x2="${width-right}" y2="${y}" stroke="#e5edf6" stroke-dasharray="4 3"/><text x="${left-9}" y="${y+4}" text-anchor="end" fill="#90a0b8" font-size="10">${value}%</text>`;}).join("");
  const labels=points.map((point,index)=>{if(points.length>8&&index%Math.ceil(points.length/6)!==0&&index!==points.length-1)return "";const anchor=points.length===1 ? "middle" : index===0 ? "start" : index===points.length-1 ? "end" : "middle";return `<text x="${coordinates[index][0]}" y="${height-20}" text-anchor="${anchor}" fill="#8d9eb7" font-size="10">${esc(point.date)}</text>`;}).join("");
  const color=metric === "mention_rate" ? "#16bd6d" : "#4388ff";
  $("dashboard-trend").innerHTML=`<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="${esc($("dashboard-trend-title").textContent)}，只包含实际有回答的日期"><defs><linearGradient id="dashboard-gradient" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="${color}" stop-opacity=".22"/><stop offset="100%" stop-color="${color}" stop-opacity=".02"/></linearGradient></defs>${lines}${points.length>1 ? `<polygon points="${left},${height-bottom} ${coordinates.map(p=>p.join(",")).join(" ")} ${width-right},${height-bottom}" fill="url(#dashboard-gradient)"/><polyline points="${coordinates.map(p=>p.join(",")).join(" ")}" fill="none" stroke="${color}" stroke-width="3"/>` : ''}${coordinates.map(([x,y],index)=>`<circle cx="${x}" cy="${y}" r="4" fill="${color}"><title>${esc(points[index].date)}：${dashboardPercent(points[index][metric],points[index].sample_count)} / ${points[index].sample_count}条样本</title></circle>`).join("")}${labels}</svg><small class="dashboard-small">${points.length===1 ? "仅一个采样日期，不生成虚构趋势线。" : "按有样本日期连线，日期间距按采样点排列；无样本日期不补零。"}${data.trend.length>60 ? "当前绘制最近60个采样日期。" : ''}</small>`;
}
form("dashboard-filter",async()=>{dashboardState.offset=0;await loadDashboard();});
$("dashboard-reset").addEventListener("click",()=>{$("dashboard-filter").reset();dashboardState.question="";dashboardState.model="";dashboardState.offset=0;perform(loadDashboard);});
$("dashboard-records").addEventListener("click",()=>perform(()=>showHistory(state.projectId)));
for(const [id,delta] of [["dashboard-prev",-20],["dashboard-next",20]])$(id).addEventListener("click",event=>perform(async()=>{dashboardState.offset+=delta;await loadDashboard();},event.currentTarget));
dashboardPanel.addEventListener("click",event=>{
  const model=event.target.closest("[data-dashboard-model]");const question=event.target.closest("[data-dashboard-question]");
  if(model||question){if(model)dashboardState.model=model.dataset.dashboardModel;if(question)dashboardState.question=question.dataset.dashboardQuestion;dashboardState.offset=0;perform(loadDashboard);}
  const metric=event.target.closest("[data-dashboard-metric]");if(metric){dashboardState.metric=metric.dataset.dashboardMetric;dashboardPanel.querySelectorAll("[data-dashboard-metric]").forEach(button=>button.classList.toggle("selected",button===metric));drawDashboardTrend();}
  const answer=event.target.closest("[data-dashboard-answer]");if(answer)perform(async()=>{
    const record=dashboardState.data.answers.find(row=>row.id===Number(answer.dataset.dashboardAnswer));
    const all=await api(`/projects/${state.projectId}/answers?batch_id=${record.batch_id}&limit=500`);
    const index=all.findIndex(row=>row.id===record.id);if(index<0)throw new Error("记录超出批次快捷定位范围，请从分析记录分页查看");
    await openAnalysis(record.batch_id,Math.floor(index/20)*20);analysisState.index=index%20;renderAnalysis();
  },answer);
});
$("dashboard-export").addEventListener("click",()=>perform(async()=>{
  if(!dashboardState.data)throw new Error("请先加载看板数据");
  const data=dashboardState.data,applied=dashboardState.applied;const text=`# ${applied.brand} 当前监测统计\n\n样本数：${data.total}\n时间范围：${applied.start||"不限"} 至 ${applied.end||"不限"}\n来源：${applied.source ? sources[applied.source] : "混合"}\n批次：${applied.batch||"全部"}\n问句：${applied.question||"全部"}\n模型：${applied.model||"全部"}\n\n${data.metrics.brands.map(b=>`${b.brand}：提及 ${b.mention_count} 次，推荐 ${b.recommendation_count} 次，提及率 ${dashboardPercent(b.mention_rate,data.total)}`).join("\n")}\n\n${data.date_basis}\n${data.metrics.warning}\n`;
  const url=URL.createObjectURL(new Blob([text],{type:"text/markdown;charset=utf-8"}));const link=document.createElement("a");link.href=url;link.download="当前监测统计.md";link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
}));
document.addEventListener("monitor-data-loaded",()=>{dashboardState.offset=0;perform(loadDashboard);});
document.addEventListener("workspace-view-changed",event=>{if(event.detail.name === "monitor")perform(loadDashboard);});
// 通用按钮操作结束后，以分页边界为准，避免 finally 误启用“下一页”。
document.addEventListener("workspace-action-finished",()=>{if(dashboardState.data){$("dashboard-prev").disabled=dashboardState.offset===0;$("dashboard-next").disabled=dashboardState.offset+20>=dashboardState.data.total;}});
