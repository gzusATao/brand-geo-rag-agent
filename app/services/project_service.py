import json
import re

from fastapi import HTTPException

from app.utils.date_utils import timestamp


class ProjectService:
    def __init__(self, database):
        self.database = database

    def create(self, request):
        now = timestamp()
        questions = getattr(request, "initial_questions", [])
        normalized_questions = [re.sub(r"[\W_]+", "", text.strip().casefold()) for text in questions]
        if any(not key or len(text.strip()) > 500 for text, key in zip(questions, normalized_questions)):
            raise HTTPException(422, "每条监测问句需包含文字或数字，且不能超过500个字符")
        if len(set(normalized_questions)) != len(normalized_questions):
            raise HTTPException(422, "监测问句不能重复，请检查标点、空白和大小写差异")
        with self.database.connect() as connection:
            cursor = connection.execute(
                "INSERT INTO projects(name,brand,aliases,competitors,created_at,updated_at) VALUES(?,?,?,?,?,?)",
                (
                    request.name,
                    request.brand,
                    json.dumps(request.aliases, ensure_ascii=False),
                    json.dumps(request.competitors, ensure_ascii=False),
                    now,
                    now,
                ),
            )
            project_id = cursor.lastrowid
            # 引导页的项目和首批问句一次提交，校验失败不能留下空项目。
            for text, normalized in zip(questions, normalized_questions):
                connection.execute(
                    "INSERT INTO questions(project_id,text,normalized,created_at,updated_at) VALUES(?,?,?,?,?)",
                    (project_id, text.strip(), normalized, now, now),
                )
        return self.get(project_id)

    def get(self, project_id):
        with self.database.connect() as connection:
            row = connection.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
        if row is None:
            raise HTTPException(404, "品牌项目不存在")
        result = dict(row)
        for key in ("aliases", "competitors"):
            result[key] = json.loads(result[key])
        return result

    def list(self):
        with self.database.connect() as connection:
            ids = [
                row["id"] for row in connection.execute("SELECT id FROM projects ORDER BY id DESC LIMIT 200")
            ]
        return [self.get(project_id) for project_id in ids]

    def add_question(self, project_id, text):
        self.get(project_id)
        now = timestamp()
        # 中文标点、大小写和空白差异不应制造重复监测问句。
        normalized = re.sub(r"[\W_]+", "", text.casefold())
        if not normalized:
            raise HTTPException(422, "问句必须包含文字或数字")
        try:
            with self.database.connect() as connection:
                cursor = connection.execute(
                    "INSERT INTO questions(project_id,text,normalized,created_at,updated_at) VALUES(?,?,?,?,?)",
                    (project_id, text, normalized, now, now),
                )
                question_id = cursor.lastrowid
        except self.database.integrity_errors:
            raise HTTPException(409, "该项目已存在相同监测问句") from None
        return next(item for item in self.questions(project_id) if item["id"] == question_id)

    def page(self, name, brand, status, start_date, end_date, page, page_size):
        if start_date and end_date and start_date > end_date:
            raise HTTPException(422, "开始日期不能晚于结束日期")
        # 状态来自最新批次，而非虚构的自动监测计划；无批次的项目为草稿。
        query = "SELECT p.*, COALESCE((SELECT status FROM batches WHERE project_id=p.id ORDER BY id DESC LIMIT 1),'draft') AS status, (SELECT COUNT(*) FROM questions WHERE project_id=p.id AND enabled=1) AS question_count FROM projects p"
        conditions, parameters = [], []
        for column, value in (("name", name), ("brand", brand)):
            if value:
                conditions.append(f"{column} LIKE ?")
                parameters.append(f"%{value}%")
        if status:
            conditions.append("status=?")
            parameters.append(status)
        if start_date:
            conditions.append("created_at>=?")
            parameters.append(f"{start_date} 00:00:00")
        if end_date:
            conditions.append("created_at<=?")
            parameters.append(f"{end_date} 23:59:59")
        filtered = f"FROM ({query}) monitor_projects" + (
            " WHERE " + " AND ".join(conditions) if conditions else ""
        )
        with self.database.connect() as connection:
            total = connection.execute(f"SELECT COUNT(*) AS total {filtered}", parameters).fetchone()["total"]
            rows = connection.execute(
                f"SELECT * {filtered} ORDER BY id DESC LIMIT ? OFFSET ?",
                (*parameters, page_size, (page - 1) * page_size),
            ).fetchall()
        items = []
        for row in rows:
            item = dict(row)
            for key in ("aliases", "competitors"):
                item[key] = json.loads(item[key])
            items.append(item)
        return {"items": items, "total": total}

    def rename(self, project_id, name):
        self.get(project_id)
        # 品牌词典保持不变，避免历史提取结果与新词典混用。
        with self.database.connect() as connection:
            connection.execute(
                "UPDATE projects SET name=?,updated_at=? WHERE id=?", (name, timestamp(), project_id)
            )
        return self.get(project_id)

    def questions(self, project_id):
        self.get(project_id)
        with self.database.connect() as connection:
            return [
                dict(row)
                for row in connection.execute(
                    "SELECT id,project_id,text,enabled,created_at,updated_at FROM questions WHERE project_id=? ORDER BY id",
                    (project_id,),
                )
            ]

    def update_question(self, project_id, question_id, enabled):
        self.get(project_id)
        with self.database.connect() as connection:
            cursor = connection.execute(
                "UPDATE questions SET enabled=?,updated_at=? WHERE id=? AND project_id=?",
                (int(enabled), timestamp(), question_id, project_id),
            )
            if cursor.rowcount == 0:
                raise HTTPException(404, "当前项目不存在该问句")
        return next(item for item in self.questions(project_id) if item["id"] == question_id)
