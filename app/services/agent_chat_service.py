import asyncio
import copy
import logging
import time
from threading import Lock
from uuid import uuid4

from fastapi import HTTPException

from app.libs.qwen_client import QwenClient
from app.services.agent_roles_service import RagAgent, SummaryAgent, SupervisorAgent, ToolAgent
from app.services.project_service import ProjectService
from app.utils.date_utils import timestamp

logger = logging.getLogger(__name__)


class AgentChatService:
    def __init__(self, database):
        self.database = database
        self.sessions = {}
        self.runs = {}
        self.lock = Lock()
        self.model = QwenClient()

    def config(self):
        return {
            "configured": self.model.configured(),
            "model": self.model.model,
            "provider": "阿里云百炼",
            "notice": "发送会将本轮消息、近期对话、项目品牌、相关知识片段和监测汇总传给百炼。配置完成不等于已验证连通性；不会自动发布或修改监测数据。",
        }

    def submit(self, project_id, request):
        ProjectService(self.database).get(project_id)
        if not self.model.configured():
            raise HTTPException(
                503, "尚未配置百炼 API Key，请在本地运行 python -m scripts.configure_llm 后重启服务"
            )
        with self.lock:
            self.prune()
            if sum(run["status"] in {"pending", "running"} for run in self.runs.values()) >= 2:
                raise HTTPException(429, "当前已有两个智能体任务，请等待完成后再发送")
            session_id = request.session_id or uuid4().hex
            session = self.sessions.get(session_id)
            if request.session_id and (session is None or session["project_id"] != project_id):
                raise HTTPException(404, "会话不存在或已过期，请开始新对话")
            if session and session["busy"]:
                raise HTTPException(409, "当前对话还有任务执行中，请等待本轮完成")
            if session and len(session["messages"]) >= 24:
                raise HTTPException(409, "当前对话已达到十二轮上限，请开始新对话")
            if not session and len(self.sessions) >= 50:
                raise HTTPException(429, "当前会话数量已达上限，请稍后再试")
            if session is None:
                session = {
                    "project_id": project_id,
                    "messages": [],
                    "busy": False,
                    "touched": time.monotonic(),
                }
                self.sessions[session_id] = session
            session["busy"] = True
            session["touched"] = time.monotonic()
            now = timestamp()
            run = {
                "id": uuid4().hex,
                "session_id": session_id,
                "project_id": project_id,
                "status": "pending",
                "answer": None,
                "error": None,
                "citations": [],
                "trace": [
                    {"agent": name, "status": "pending", "summary": "等待主管分派任务"}
                    for name in ("supervisor", "rag", "tool", "summary")
                ],
                "created_at": now,
                "updated_at": now,
            }
            self.runs[run["id"]] = run
            return copy.deepcopy(run)

    async def execute(self, run_id, message):
        with self.lock:
            run = self.runs[run_id]
            run["status"] = "running"
            history = copy.deepcopy(self.sessions[run["session_id"]]["messages"][-8:])
        try:
            # 一轮最多主管、检索、摘要三次模型调用；不自动重试，避免失控费用和递归工具调用。
            answer, citations = await asyncio.wait_for(self.run_agents(run_id, message, history), timeout=120)
            with self.lock:
                run.update(status="completed", answer=answer, citations=citations, updated_at=timestamp())
                self.sessions[run["session_id"]]["messages"].extend(
                    [
                        {"role": "user", "content": message},
                        {"role": "assistant", "content": answer},
                    ]
                )
        except Exception as error:
            reason = (
                error.detail
                if isinstance(error, HTTPException)
                else "多智能体执行超时，请稍后重试"
                if isinstance(error, asyncio.TimeoutError)
                else "多智能体执行失败，本轮未保存为成功结果"
            )
            with self.lock:
                run.update(status="failed", error=reason, updated_at=timestamp())
                for step in run["trace"]:
                    if step["status"] == "running":
                        step.update(status="failed", summary=reason)
                    elif step["status"] == "pending":
                        step.update(status="skipped", summary="上游任务失败，本步骤未执行")
            logger.warning("多智能体任务失败：%s", run_id)
        finally:
            with self.lock:
                self.sessions[run["session_id"]].update(busy=False, touched=time.monotonic())

    async def run_agents(self, run_id, message, history):
        project_id = self.runs[run_id]["project_id"]
        project = await asyncio.to_thread(ProjectService(self.database).get, project_id)
        context = {"品牌": project["brand"], "近期对话": history, "本轮要求": message}
        self.progress(run_id, "supervisor", "running", "正在识别意图并分派专业智能体")
        plan = await SupervisorAgent(self.model).run(context)
        selected = set(plan.agents)
        if plan.intent in {"knowledge", "article"}:
            selected.add("rag")
        if plan.intent == "analysis":
            selected.add("tool")
        self.progress(run_id, "supervisor", "completed", "已完成意图识别，按白名单分派检索和指标任务")
        results = {}

        async def rag():
            self.progress(run_id, "rag", "running", "正在检索当前项目的企业资料并核对引用")
            results["rag"] = await RagAgent(self.database, self.model).run(project_id, plan.query, context)
            result = results["rag"]
            self.progress(
                run_id,
                "rag",
                "completed",
                f"检索到{result['命中片段数']}个片段，引用{len(result['引用'])}个；词面检索基线",
            )

        async def tool():
            self.progress(run_id, "tool", "running", "正在读取真实、历史与模拟来源的品牌指标")
            results["tool"] = await ToolAgent(self.database).run(project_id)
            self.progress(run_id, "tool", "completed", "已按来源分别统计；模拟数据不参与真实效果结论")

        jobs = []
        for name, action in (("rag", rag), ("tool", tool)):
            if name in selected:
                jobs.append(action())
            else:
                self.progress(run_id, name, "skipped", "主管判断本轮不需要该专业任务")
        # 等待所有已派发分支结束再处理失败，避免失败后残留分支继续改写轨迹。
        outcomes = await asyncio.gather(*jobs, return_exceptions=True)
        for outcome in outcomes:
            if isinstance(outcome, BaseException):
                raise outcome
        self.progress(run_id, "summary", "running", "正在整合专业结果并生成有证据边界的答复")
        answer, citations = await SummaryAgent(self.model).run(context, plan.intent, results)
        self.progress(run_id, "summary", "completed", "答复已汇总，引用编号已核对；内容仍需人工审核")
        return answer, citations

    def progress(self, run_id, agent, status, summary):
        with self.lock:
            run = self.runs[run_id]
            next(step for step in run["trace"] if step["agent"] == agent).update(
                status=status, summary=summary
            )
            run["updated_at"] = timestamp()

    def get(self, project_id, run_id):
        with self.lock:
            run = self.runs.get(run_id)
            if run is None or run["project_id"] != project_id:
                raise HTTPException(404, "多智能体任务不存在或不属于当前项目")
            return copy.deepcopy(run)

    def session(self, project_id, session_id):
        with self.lock:
            self.prune()
            session = self.sessions.get(session_id)
            if session is None or session["project_id"] != project_id:
                raise HTTPException(404, "会话不存在或已过期，请开始新对话")
            session["touched"] = time.monotonic()
            return {
                "session_id": session_id,
                "project_id": project_id,
                "messages": copy.deepcopy(session["messages"]),
            }

    def prune(self):
        expired = [
            key
            for key, session in self.sessions.items()
            if not session["busy"] and time.monotonic() - session["touched"] > 3600
        ]
        for key in expired:
            self.sessions.pop(key)
        for key, run in list(self.runs.items()):
            if run["session_id"] not in self.sessions or (
                len(self.runs) >= 100 and run["status"] in {"completed", "failed"}
            ):
                self.runs.pop(key)
