import math
import re
from collections import Counter

from fastapi import HTTPException

from app.services.project_service import ProjectService
from app.utils.date_utils import timestamp


class KnowledgeService:
    def __init__(self, database):
        self.database = database
        self.projects = ProjectService(database)

    def add_document(self, project_id, request):
        self.projects.get(project_id)
        # 非重叠固定分段基线，保留片段ID及来源；后续替换为Dify/向量检索。
        chunks = [request.content[start : start + 450] for start in range(0, len(request.content), 450)]
        now = timestamp()
        with self.database.connect() as connection:
            cursor = connection.execute(
                "INSERT INTO documents(project_id,title,source,content,chunk_count,created_at,updated_at) VALUES(?,?,?,?,?,?,?)",
                (project_id, request.title, request.source, request.content, len(chunks), now, now),
            )
            document_id = cursor.lastrowid
            connection.executemany(
                "INSERT INTO chunks(document_id,ordinal,text,created_at,updated_at) VALUES(?,?,?,?,?)",
                [(document_id, index + 1, chunk, now, now) for index, chunk in enumerate(chunks)],
            )
        return next(item for item in self.documents(project_id) if item["id"] == document_id)

    def documents(self, project_id):
        self.projects.get(project_id)
        with self.database.connect() as connection:
            return [
                dict(row)
                for row in connection.execute(
                    "SELECT id,project_id,title,source,chunk_count,created_at,updated_at "
                    "FROM documents WHERE project_id=? ORDER BY id DESC",
                    (project_id,),
                )
            ]

    def retrieve(self, project_id, query, top_k):
        self.projects.get(project_id)
        query_tokens = tokenize(query)
        hits = []
        with self.database.connect() as connection:
            rows = connection.execute(
                "SELECT c.id AS chunk_id,d.id AS document_id,d.title,d.source,c.text "
                "FROM chunks c JOIN documents d ON d.id=c.document_id WHERE d.project_id=?",
                (project_id,),
            )
            for row in rows:
                score = similarity(query_tokens, tokenize(row["text"]))
                if score > 0:
                    hits.append({**dict(row), "score": round(score, 6)})
        return sorted(hits, key=lambda hit: (-hit["score"], hit["chunk_id"]))[:top_k]

    def document(self, project_id, document_id):
        self.projects.get(project_id)
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT * FROM documents WHERE project_id=? AND id=?", (project_id, document_id)
            ).fetchone()
        if row is None:
            raise HTTPException(404, "当前项目不存在该品牌资料")
        return dict(row)


def tokenize(text):
    tokens = re.findall(r"[a-z0-9]+|[\u4e00-\u9fff]+", text.casefold())
    return Counter(
        piece
        for token in tokens
        for piece in (
            [token]
            if not re.fullmatch(r"[\u4e00-\u9fff]{2,}", token)
            else [token[index : index + 2] for index in range(len(token) - 1)]
        )
    )


def similarity(left, right):
    denominator = math.sqrt(
        sum(value * value for value in left.values()) * sum(value * value for value in right.values())
    )
    return sum(value * right.get(key, 0) for key, value in left.items()) / denominator if denominator else 0
