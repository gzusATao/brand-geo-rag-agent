import csv
import io
import json
import logging
from datetime import datetime

from fastapi import HTTPException

from app.services.extraction_service import extract_brands
from app.services.project_service import ProjectService
from app.utils.date_utils import timestamp

logger = logging.getLogger(__name__)


class TaskService:
    def __init__(self, database):
        self.database = database
        self.projects = ProjectService(database)

    def import_csv(self, project_id, content):
        project = self.projects.get(project_id)
        rows = self.parse_csv(content)
        sources = {row["source"] for row in rows}
        source = sources.pop() if len(sources) == 1 else "mixed"
        now = timestamp()
        # 全部行校验后再开始事务，坏行不会留下半个批次或半份统计数据。
        with self.database.connect() as connection:
            cursor = connection.execute(
                "INSERT INTO batches(project_id,source,status,total,completed,created_at,updated_at) VALUES(?,?,?,?,?,?,?)",
                (project_id, source, "completed", len(rows), len(rows), now, now),
            )
            batch_id = cursor.lastrowid
            for row in rows:
                self.save_answer(connection, batch_id, project, row, now)
        return self.batch(batch_id)

    def create_mock(self, project_id, question_ids):
        project = self.projects.get(project_id)
        available = {row["id"]: row for row in self.projects.questions(project_id) if row["enabled"]}
        if any(question_id not in available for question_id in question_ids):
            raise HTTPException(422, "问句不存在、已停用或不属于当前项目")
        snapshots = [available[question_id]["text"] for question_id in question_ids]
        now = timestamp()
        with self.database.connect() as connection:
            cursor = connection.execute(
                "INSERT INTO batches(project_id,source,status,total,created_at,updated_at) VALUES(?,?,?,?,?,?)",
                (project_id, "mock", "pending", len(snapshots), now, now),
            )
            batch_id = cursor.lastrowid
        return self.batch(batch_id), project, snapshots

    def run_mock(self, batch_id, project, snapshots):
        try:
            with self.database.connect() as connection:
                connection.execute(
                    "UPDATE batches SET status='running',updated_at=? WHERE id=?", (timestamp(), batch_id)
                )
            for index, question in enumerate(snapshots):
                # 人工构造的固定样本只验证流程，绝不称为真实模型采集结果。
                if index % 3 == 0:
                    answer = f"【模拟回答】\n1. 推荐{project['brand']}作为候选方案。"
                elif index % 3 == 1:
                    alternative = project["competitors"][0] if project["competitors"] else "其他方案"
                    answer = f"【模拟回答】\n推荐{alternative}。{project['brand']}可供进一步了解。"
                else:
                    answer = "【模拟回答】应核对需求、服务范围和公开资料后作出选择。"
                now = timestamp()
                with self.database.connect() as connection:
                    self.save_answer(
                        connection,
                        batch_id,
                        project,
                        {
                            "question": question,
                            "answer": answer,
                            "model": "模拟适配器",
                            "source": "mock",
                            "collected_date": None,
                        },
                        now,
                    )
                    connection.execute(
                        "UPDATE batches SET completed=completed+1,updated_at=? WHERE id=?", (now, batch_id)
                    )
            with self.database.connect() as connection:
                connection.execute(
                    "UPDATE batches SET status='completed',updated_at=? WHERE id=?", (timestamp(), batch_id)
                )
        except Exception:
            logger.error("模拟监测失败，批次ID=%s", batch_id)
            with self.database.connect() as connection:
                connection.execute(
                    "UPDATE batches SET status='failed',error=?,updated_at=? WHERE id=?",
                    ("模拟监测执行失败，请检查数据库并重新创建批次", timestamp(), batch_id),
                )

    def batch(self, batch_id):
        with self.database.connect() as connection:
            row = connection.execute("SELECT * FROM batches WHERE id=?", (batch_id,)).fetchone()
        if row is None:
            raise HTTPException(404, "监测批次不存在")
        return dict(row)

    def analysis_page(self, brand, question, status, source, page, page_size, start_date=None, end_date=None):
        if start_date and end_date and start_date > end_date:
            raise HTTPException(422, "开始日期不能晚于结束日期")
        conditions, parameters = [], []
        if brand:
            conditions.append("p.brand LIKE ?")
            parameters.append(f"%{brand}%")
        if question:
            conditions.append("EXISTS (SELECT 1 FROM answers a WHERE a.batch_id=b.id AND a.question LIKE ?)")
            parameters.append(f"%{question}%")
        for column, value in (("status", status), ("source", source)):
            if value:
                conditions.append(f"b.{column}=?")
                parameters.append(value)
        if start_date:
            conditions.append("b.created_at>=?")
            parameters.append(f"{start_date} 00:00:00")
        if end_date:
            conditions.append("b.created_at<=?")
            parameters.append(f"{end_date} 23:59:59")
        query = "FROM batches b JOIN projects p ON p.id=b.project_id" + (
            " WHERE " + " AND ".join(conditions) if conditions else ""
        )
        with self.database.connect() as connection:
            total = connection.execute(f"SELECT COUNT(*) AS total {query}", parameters).fetchone()["total"]
            rows = connection.execute(
                f"SELECT b.*,p.brand,p.name AS project_name,(SELECT question FROM answers WHERE batch_id=b.id ORDER BY id LIMIT 1) AS question {query} ORDER BY b.id DESC LIMIT ? OFFSET ?",
                (*parameters, page_size, (page - 1) * page_size),
            ).fetchall()
        items = [dict(row) for row in rows]
        for item in items:
            item["question"] = item["question"] or "尚无已保存回答"
        return {"items": items, "total": total}

    def batches(self, project_id):
        self.projects.get(project_id)
        with self.database.connect() as connection:
            return [
                dict(row)
                for row in connection.execute(
                    "SELECT * FROM batches WHERE project_id=? ORDER BY id DESC LIMIT 100", (project_id,)
                )
            ]

    def detail(self, batch_id, limit, offset):
        batch = self.batch(batch_id)
        project_id = batch["project_id"]
        metrics = self.metrics(project_id, batch_id=batch_id)
        return {
            "batch": batch,
            "project": self.projects.get(project_id),
            "metrics": metrics,
            "answers": self.answers(project_id, batch_id=batch_id, limit=limit, offset=offset),
            "total_answers": metrics["sample_count"],
        }

    def answers(self, project_id, source=None, batch_id=None, limit=200, offset=0):
        self.projects.get(project_id)
        query, parameters = self.answer_filter(project_id, source, batch_id)
        with self.database.connect() as connection:
            rows = connection.execute(
                f"SELECT * FROM answers WHERE {query} ORDER BY id DESC LIMIT ? OFFSET ?",
                (*parameters, limit, offset),
            ).fetchall()
        results = []
        for row in rows:
            result = dict(row)
            result["extraction"] = json.loads(result["extraction"])
            results.append(result)
        return results

    def metrics(self, project_id, source=None, batch_id=None):
        project = self.projects.get(project_id)
        query, parameters = self.answer_filter(project_id, source, batch_id)
        brands = {
            name: {
                "brand": name,
                "mention_count": 0,
                "recommendation_count": 0,
                "mention_rate": 0.0,
                "recommendation_rate": 0.0,
                "rank_distribution": {},
            }
            for name in [project["brand"], *project["competitors"]]
        }
        count = 0
        source_counts = {"real": 0, "historical": 0, "mock": 0}
        with self.database.connect() as connection:
            for row in connection.execute(f"SELECT source,extraction FROM answers WHERE {query}", parameters):
                count += 1
                source_counts[row["source"]] += 1
                for item in json.loads(row["extraction"]):
                    metric = brands[item["brand"]]
                    metric["mention_count"] += int(item["mentioned"])
                    metric["recommendation_count"] += int(item["recommended"])
                    if item["rank"] is not None:
                        rank = str(item["rank"])
                        metric["rank_distribution"][rank] = metric["rank_distribution"].get(rank, 0) + 1
        for metric in brands.values():
            if count:
                metric["mention_rate"] = round(metric["mention_count"] / count, 6)
                metric["recommendation_rate"] = round(metric["recommendation_count"] / count, 6)
        return {
            "sample_count": count,
            "source_counts": source_counts,
            "brands": list(brands.values()),
            "warning": "当前为规则提取基线，需人工核验；模拟数据仅验证流程，不代表公共模型效果。",
        }

    def interrupt_incomplete(self):
        # 进程内后台任务不能保证重启恢复；明确标记中断，不让页面永久显示运行中。
        with self.database.connect() as connection:
            connection.execute(
                "UPDATE batches SET status='failed',error=?,updated_at=? WHERE status IN ('pending','running')",
                ("服务重启导致任务中断，已保存的回答保留，请重新创建批次", timestamp()),
            )

    def answer_filter(self, project_id, source, batch_id):
        query = "project_id=?"
        parameters = [project_id]
        if source:
            query += " AND source=?"
            parameters.append(source)
        if batch_id is not None:
            batch = self.batch(batch_id)
            if batch["project_id"] != project_id:
                raise HTTPException(404, "当前项目不存在该监测批次")
            query += " AND batch_id=?"
            parameters.append(batch_id)
        return query, parameters

    def save_answer(self, connection, batch_id, project, row, now):
        connection.execute(
            "INSERT INTO answers(batch_id,project_id,question,answer,model,source,collected_date,extraction,"
            "extractor_version,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            (
                batch_id,
                project["id"],
                row["question"],
                row["answer"],
                row["model"],
                row["source"],
                row["collected_date"],
                json.dumps(extract_brands(row["answer"], project), ensure_ascii=False),
                "保守规则-v1",
                now,
                now,
            ),
        )

    def parse_csv(self, content):
        reader = csv.DictReader(io.StringIO(content.lstrip("\ufeff")), strict=True)
        required = {"question", "answer", "model", "source"}
        try:
            headers = reader.fieldnames or []
            if not required <= set(headers) or len(headers) != len(set(headers)):
                raise HTTPException(422, "CSV表头必须包含且不能重复：question、answer、model、source")
            rows = []
            for index, row in enumerate(reader, 2):
                if len(rows) >= 500:
                    raise HTTPException(422, "单次导入不能超过500条回答")
                if None in row or any(not (row.get(key) or "").strip() for key in required):
                    raise HTTPException(422, f"CSV第{index}行列数错误或必填内容为空")
                item = {key: (row.get(key) or "").strip() for key in required}
                if len(item["question"]) > 500 or len(item["answer"]) > 20_000 or len(item["model"]) > 100:
                    raise HTTPException(422, f"CSV第{index}行内容超出长度限制")
                if item["source"] not in {"mock", "historical", "real"}:
                    raise HTTPException(422, f"CSV第{index}行来源必须为mock、historical或real")
                collected = (row.get("collected_date") or "").strip()
                if collected:
                    try:
                        parsed = datetime.strptime(collected, "%Y-%m-%d")
                        if parsed.strftime("%Y-%m-%d") != collected:
                            raise ValueError("采集日期格式不正确")
                    except ValueError:
                        raise HTTPException(422, f"CSV第{index}行采集日期必须为YYYY-MM-DD") from None
                item["collected_date"] = collected or None
                rows.append(item)
        except csv.Error:
            raise HTTPException(422, "CSV格式错误，请检查引号和列分隔符") from None
        if not rows:
            raise HTTPException(422, "CSV没有可导入的回答")
        return rows
