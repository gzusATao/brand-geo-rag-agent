import json

from fastapi import HTTPException

from app.services.knowledge_service import KnowledgeService
from app.services.project_service import ProjectService
from app.services.task_service import TaskService
from app.utils.date_utils import timestamp


class ArticleTaskService:
    def __init__(self, database):
        self.database = database

    def create(self, project_id, request):
        project = ProjectService(self.database).get(project_id)
        monitor = TaskService(self.database)
        real = monitor.metrics(project_id, "real")
        history = monitor.metrics(project_id, "historical")
        hits = KnowledgeService(self.database).retrieve(project_id, request.query, request.top_k)
        count = real["sample_count"] + history["sample_count"]
        target_count = real["brands"][0]["mention_count"] + history["brands"][0]["mention_count"]
        diagnosis = (
            f"当前项目有{count}条非模拟回答，其中{target_count}条提及目标品牌。"
            "此为项目整体规则统计，不能证明目标问句效果或推断内容优化的因果关系。"
            if count
            else "暂无非模拟监测回答，不能判断真实品牌可见性；仅展示资料整理流程。"
        )
        suggestions = ["人工核对品牌提取结果和资料事实，再决定是否补充面向目标问句的FAQ。"]
        if not hits:
            suggestions.append("当前未检索到相关资料，请补充公开品牌说明，不能凭空生成产品事实。")
        else:
            suggestions.append("以下片段仅按词面相关性检索，需核查是否真正回答目标问句。")
        trace = [
            {"tool": "指标查询", "status": "已完成", "summary": f"统计{count}条非模拟回答，排除Mock"},
            {"tool": "品牌知识检索", "status": "已完成", "summary": f"词面检索命中{len(hits)}个片段"},
            {"tool": "草稿组装", "status": "已完成", "summary": "固定工作流摘录原文，未调用大模型"},
        ]
        draft = f"# {project['brand']}资料整理草稿\n\n目标问句：{request.query}\n\n"
        draft += "此为固定工作流演示草稿，需人工核实，不构成品牌推荐或发布成稿。\n\n"
        if hits:
            for hit in hits:
                draft += f"## 资料片段 [{hit['chunk_id']}]\n\n{hit['text']}\n\n"
                draft += f"来源：{hit['title']}；{hit['source']}\n\n"
        else:
            draft += "证据不足：当前知识库没有相关片段。请补充资料后重新运行。\n"
        now = timestamp()
        with self.database.connect() as connection:
            cursor = connection.execute(
                "INSERT INTO optimizations(project_id,query,mode,diagnosis,suggestions,citations,trace,draft,"
                "created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
                (
                    project_id,
                    request.query,
                    "固定工具工作流演示",
                    diagnosis,
                    json.dumps(suggestions, ensure_ascii=False),
                    json.dumps(hits, ensure_ascii=False),
                    json.dumps(trace, ensure_ascii=False),
                    draft,
                    now,
                    now,
                ),
            )
            run_id = cursor.lastrowid
        return self.get(run_id)

    def get(self, run_id):
        with self.database.connect() as connection:
            row = connection.execute("SELECT * FROM optimizations WHERE id=?", (run_id,)).fetchone()
        if row is None:
            raise HTTPException(404, "辅助优化运行不存在")
        result = dict(row)
        for key in ("suggestions", "citations", "trace"):
            result[key] = json.loads(result[key])
        return result

    def list(self, project_id):
        ProjectService(self.database).get(project_id)
        with self.database.connect() as connection:
            ids = [
                row["id"]
                for row in connection.execute(
                    "SELECT id FROM optimizations WHERE project_id=? ORDER BY id DESC LIMIT 100",
                    (project_id,),
                )
            ]
        return [self.get(run_id) for run_id in ids]

    def review(self, run_id, request):
        self.get(run_id)
        now = timestamp()
        with self.database.connect() as connection:
            row = connection.execute("SELECT draft FROM optimizations WHERE id=?", (run_id,)).fetchone()
            draft = request.draft if request.draft is not None else row["draft"]
            # 审核历史与当前状态一起提交，后续修改不能抹去之前的人工审核证据。
            connection.execute(
                "INSERT INTO reviews(optimization_id,status,note,draft,created_at,updated_at) VALUES(?,?,?,?,?,?)",
                (run_id, request.status, request.note, draft, now, now),
            )
            connection.execute(
                "UPDATE optimizations SET draft=?,review_status=?,review_note=?,updated_at=? WHERE id=?",
                (draft, request.status, request.note, now, run_id),
            )
        return self.get(run_id)

    def export(self, run_id):
        run = self.get(run_id)
        if run["review_status"] != "approved":
            raise HTTPException(409, "草稿尚未审核通过，不能导出")
        return run["draft"]
