"""Repository 3종 — 구 src/*_repo.php 이식.

원본 Pest는 테스트 DB에 쓰고 afterEach로 지웠지만, 여기서는 db_session이
트랜잭션을 통째로 롤백하므로 정리 코드가 필요 없다(2-1에서 도입한 fixture).

    APP_ENV=testing uv run pytest tests/unit
"""

from sqlalchemy.orm import Session

from app.models import ChatTurn
from app.repositories import ChatRepository, SummaryRepository
from app.topic import topic_url

TOPIC_ID = 999000002
MODEL = "gemini-2.5-flash"


def test_find는_요약이_없으면_None(db_session: Session):
    repo = SummaryRepository(db_session)

    assert repo.find(TOPIC_ID) is None


def test_save한_요약을_find로_읽어온다(db_session: Session):
    repo = SummaryRepository(db_session)

    repo.save(TOPIC_ID, topic_url(TOPIC_ID), "테스트 제목", "테스트 요약", MODEL)
    summary = repo.find(TOPIC_ID)

    assert summary is not None
    assert summary.topic_id == TOPIC_ID
    assert summary.url == topic_url(TOPIC_ID)
    assert summary.title == "테스트 제목"
    assert summary.summary == "테스트 요약"
    assert summary.model == MODEL


def test_같은_topic_id로_다시_save하면_덮어쓴다(db_session: Session):
    repo = SummaryRepository(db_session)

    repo.save(TOPIC_ID, topic_url(TOPIC_ID), "첫 제목", "첫 요약", MODEL)
    repo.save(TOPIC_ID, topic_url(TOPIC_ID), "수정된 제목", "수정된 요약", MODEL)
    summary = repo.find(TOPIC_ID)

    assert summary is not None
    assert summary.title == "수정된 제목"
    assert summary.summary == "수정된 요약"


def test_delete하면_요약이_사라진다(db_session: Session):
    repo = SummaryRepository(db_session)
    repo.save(TOPIC_ID, topic_url(TOPIC_ID), "제목", "요약", MODEL)

    repo.delete(TOPIC_ID)

    assert repo.find(TOPIC_ID) is None


def test_list는_방금_저장한_요약을_맨_앞에_둔다(db_session: Session):
    repo = SummaryRepository(db_session)
    repo.save(TOPIC_ID, topic_url(TOPIC_ID), "제목", "요약", MODEL)

    summaries = repo.list()

    assert summaries[0].topic_id == TOPIC_ID


def test_create_session은_id를_돌려주고_session_exists가_찾는다(db_session: Session):
    repo = ChatRepository(db_session)

    session_id = repo.create_session()

    assert session_id > 0
    assert repo.session_exists(session_id) is True


def test_session_exists는_모르는_id면_False(db_session: Session):
    repo = ChatRepository(db_session)

    assert repo.session_exists(999999999) is False


def test_add_message한_메시지를_시간순으로_읽어온다(db_session: Session):
    repo = ChatRepository(db_session)
    session_id = repo.create_session()

    repo.add_message(session_id, "user", "첫 번째 질문")
    repo.add_message(session_id, "model", "첫 번째 답변")
    repo.add_message(session_id, "user", "두 번째 질문")

    messages = repo.get_recent_messages(session_id)

    assert messages == [
        ChatTurn(role="user", content="첫 번째 질문"),
        ChatTurn(role="model", content="첫 번째 답변"),
        ChatTurn(role="user", content="두 번째 질문"),
    ]


def test_get_recent_messages는_limit_만큼_최근_것만_시간순으로(db_session: Session):
    repo = ChatRepository(db_session)
    session_id = repo.create_session()
    for i in range(1, 6):
        repo.add_message(session_id, "user", f"메시지 {i}")

    messages = repo.get_recent_messages(session_id, 2)

    assert [m.content for m in messages] == ["메시지 4", "메시지 5"]
