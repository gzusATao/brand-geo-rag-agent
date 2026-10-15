import json
from collections import Counter

from fastapi import HTTPException

from app.services.project_service import ProjectService
from app.services.task_service import TaskService


class DashboardService:
    def __init__(self, database):
        self.database = database

    def get(self, project_id, source, batch_id, start_date, end_date, question, model, limit, offset):
        project = ProjectService(self.database).get(project_id)
        if start_date and end_date and start_date > end_date:
            raise HTTPException(422, "开始日期不能晚于结束日期")
        query, parameters = TaskService(self.database).answer_filter(project_id, source, batch_id)
        if start_date:
            query += " AND COALESCE(collected_date,SUBSTR(created_at,1,10))>=?"
            parameters.append(str(start_date))
        if end_date:
            query += " AND COALESCE(collected_date,SUBSTR(created_at,1,10))<=?"
            parameters.append(str(end_date))
        with self.database.connect() as connection:
            rows = connection.execute(
                f"SELECT * FROM answers WHERE {query} ORDER BY id DESC", parameters
            ).fetchall()
        # 选项只受时间、来源和批次影响，避免选中某问句后其他选项突然消失。
        questions = Counter(row["question"] for row in rows)
        models = Counter(row["model"] for row in rows)
        selected = [
            dict(row)
            for row in rows
            if (not question or row["question"] == question) and (not model or row["model"] == model)
        ]
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
        dates = {}
        ranks = {"第一位": 0, "第二至第三位": 0, "其他显式编号": 0, "无明确编号": 0}
        sources = {"mock": 0, "historical": 0, "real": 0}
        for row in selected:
            row["extraction"] = json.loads(row["extraction"])
            sources[row["source"]] += 1
            day = row["collected_date"] or row["created_at"][:10]
            point = dates.setdefault(
                day, {"date": day, "sample_count": 0, "mentions": 0, "recommendations": 0}
            )
            point["sample_count"] += 1
            target = next(item for item in row["extraction"] if item["brand"] == project["brand"])
            point["mentions"] += int(target["mentioned"])
            point["recommendations"] += int(target["recommended"])
            rank = target["rank"]
            ranks[
                "无明确编号"
                if rank is None
                else "第一位"
                if rank == 1
                else "第二至第三位"
                if rank <= 3
                else "其他显式编号"
            ] += 1
            for item in row["extraction"]:
                metric = brands[item["brand"]]
                metric["mention_count"] += int(item["mentioned"])
                metric["recommendation_count"] += int(item["recommended"])
                if item["rank"] is not None:
                    value = str(item["rank"])
                    metric["rank_distribution"][value] = metric["rank_distribution"].get(value, 0) + 1
        count = len(selected)
        for metric in brands.values():
            if count:
                metric["mention_rate"] = round(metric["mention_count"] / count, 6)
                metric["recommendation_rate"] = round(metric["recommendation_count"] / count, 6)
        trend = [
            {
                "date": day,
                "sample_count": point["sample_count"],
                "mention_rate": round(point["mentions"] / point["sample_count"], 6),
                "recommendation_rate": round(point["recommendations"] / point["sample_count"], 6),
            }
            for day, point in sorted(dates.items())
        ]
        return {
            "metrics": {
                "sample_count": count,
                "source_counts": sources,
                "brands": list(brands.values()),
                "warning": "模拟数据只验证流程；推荐与编号为规则提取结果，需要人工核验。",
            },
            "trend": trend,
            "rank_counts": ranks,
            "answers": selected[offset : offset + limit],
            "total": count,
            "questions": [{"question": text, "sample_count": number} for text, number in questions.items()],
            "models": [{"model": text, "sample_count": number} for text, number in models.items()],
            "date_basis": "优先使用采集日期；未提供时使用回答入库日期。只绘制有样本的日期，不补造无数据日期的指标。",
        }
