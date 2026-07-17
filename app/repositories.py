"""DB 접근 계층

세션은 생성자로 주입받음(FastAPI Depends가 조립)
전역 getDb() 대신 세션을 넘겨받으므로 테스트에서 롤백 트랜잭션에 묶을 수 있음

pydantic 모델이라 ORM 매핑이 없고, 스키마의 단일 출처는 Alembic 리비전.
따라서 쿼리는 text()로 직접 씀
"""

from typing import Literal

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models import ChatTurn, Summary


class SummaryRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def find(self, topic_id: int) -> Summary | None:
        row = (
            self._session.execute(
                text("SELECT * FROM summaries WHERE topic_id = :topic_id"),
                {"topic_id": topic_id},
            )
            .mappings()
            .one_or_none()
        )

        return None if row is None else Summary.model_validate(dict(row))

    def save(
        self, topic_id: int, url: str, title: str, summary: str, model: str
    ) -> None:
        """upsert - 재요약 시 같은 topic_id 행을 덮어씀"""
        self._session.execute(
            text("""
                INSERT INTO summaries (topic_id, url, title,summary, model)
                VALUES(:topic_id, :url, :title, :summary, :model)
                ON DUPLICATE KEY UPDATE
                    url = VALUES(url), title = VALUES(title),
                    summary = VALUES(summary), model = VALUES(model)
                """),
            {
                "topic_id": topic_id,
                "url": url,
                "title": title,
                "summary": summary,
                "model": model,
            },
        )
        self._session.commit()

    def delete(self, topic_id: int) -> None:
        self._session.execute(
            text("DELETE FROM summaries WHERE topic_id = :topic_id"),
            {"topic_id": topic_id},
        )
        self._session.commit()

    def list(self, limit: int = 50) -> list[Summary]:
        """최신 갱신순. 3-2의 GET /api/summaries가 호출부"""
        rows = (
            self._session.execute(
                text("SELECT * FROM summaries ORDER BY updated_at DESC LIMIT :limit"),
                {"limit": limit},
            )
            .mappings()
            .all()
        )

        return [Summary.model_validate(dict(row)) for row in rows]


class ChatRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create_session(self) -> int:
        result = self._session.execute(text("INSERT INTO chat_session () VALUES ()"))
        self._session.commit()

        return result.lastrowid

    def session_exists(self, session_id: int) -> bool:
        row = self._session.execute(
            text("SELECT 1 FROM chat_session WHERE id = :id"),
            {"id": session_id},
        ).first()

        return row is not None

    def add_message(
        self, session_id: int, role: Literal["user", "model"], content: str
    ) -> None:
        self._session.execute(
            text("""
                INSERT INTO chat_message (session_id, role, content)
                VALUES (:session_id, :role, :content)
            """),
            {"session_id": session_id, "role": role, "content": content},
        )
        self._session.commit()

    def get_recent_messages(self, session_id: int, limit: int = 20) -> list[ChatTurn]:
        """최근 limit개를 시간순으로. 오래된 건 잘라내 토큰을 아낌.
        id DESC로 최근 것을 고른 뒤 바깥에서 ASC로 되돌림 - 안쪽
        정렬은 '무엇을 남길지', 바깥 정렬은 '어떤 순서로 줄지'라 둘 다 필요
        """
        rows = (
            self._session.execute(
                text("""
                    SELECT role, content FROM (
                        SELECT role, content, id FROM chat_message
                        WHERE session_id = :session_id ORDER BY id DESC LIMIT :limit
                    ) t ORDER BY id ASC
                """),
                {"session_id": session_id, "limit": limit},
            )
            .mappings()
            .all()
        )

        return [ChatTurn.model_validate(dict(row)) for row in rows]
