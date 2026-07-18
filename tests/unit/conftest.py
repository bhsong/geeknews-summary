"""tests/unit 공용 fixture.

db_session: 트랜잭션 롤백으로 테스트 간 DB 상태를 격리한다(구 Pest 테스트 DB
방식보다 빠르고 안전). 실제 테스트 MySQL이 필요하며, APP_ENV=testing이 아니거나
DB에 연결할 수 없으면 skip한다(운영 DB 보호 — 운영 원칙 7).

    APP_ENV=testing uv run pytest tests/unit
"""

from collections.abc import Iterator

import pytest
from sqlalchemy.orm import Session


@pytest.fixture
def require_test_db() -> None:
    """운영 DB 보호 가드: APP_ENV=testing이 아니거나 연결 불가면 skip."""
    # app.db가 아직 없는 케이스(Red)에도 conftest import가 깨지지 않도록 지연 import.
    from sqlalchemy import exc

    from app.config import Settings
    from app.db import engine

    if Settings().app_env != "testing":
        pytest.skip("APP_ENV=testing 아님 — 운영 DB 보호를 위해 건너뜁니다.")

    try:
        engine.connect().close()
    except exc.OperationalError:
        pytest.skip("테스트 DB에 연결할 수 없습니다.")


@pytest.fixture
def db_session(require_test_db: None) -> Iterator[Session]:
    from app.db import engine

    # 바깥 트랜잭션을 열고 세션을 그 커넥션에 묶은 뒤, 끝나면 통째로 롤백한다.
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


# 검색 케이스 전용 시드. 원본 Pest가 쓰던 값 그대로 — ngram 파서가 CJK를 바이그램으로
# 쪼개므로, 일반 문서에 우연히 등장하지 않을 만큼 긴 키워드여야 오탐이 없다.
SEARCH_TOPIC_ID = 999000001
SEARCH_KEYWORD = "검색전용키워드프레스토파랑고양이"


@pytest.fixture
def committed_article(require_test_db: None) -> Iterator[tuple[int, str]]:
    """검색 케이스 전용 — db_session 롤백 전략의 유일한 예외.

    InnoDB는 FULLTEXT 인덱스를 **실제 커밋 시점에** 갱신한다. 따라서 db_session의
    롤백 트랜잭션 안에서 INSERT한 행은 일반 SELECT로는 보여도 MATCH ... AGAINST로는
    찾을 수 없다(2-4에서 실측 확인). 그래서 여기서만 진짜로 커밋하고 teardown에서
    명시적으로 지운다 — 원본 Pest의 beforeEach/afterEach 방식 그대로다.

    커밋하는 fixture이므로 teardown이 반드시 돌아야 테스트 DB에 잔여물이 남지 않는다.
    """
    from sqlalchemy import text

    from app.db import engine

    with engine.begin() as connection:
        connection.execute(
            text("""
                INSERT INTO articles (topic_id, title, content)
                VALUES (:topic_id, :title, :content)
                ON DUPLICATE KEY UPDATE
                    title = VALUES(title), content = VALUES(content)
                """),
            {
                "topic_id": SEARCH_TOPIC_ID,
                "title": "검색 테스트용 기사 제목",
                "content": (
                    "검색 테스트를 위해 삽입된 임시 기사 본문입니다. "
                    f"{SEARCH_KEYWORD}가 포함되어 있습니다."
                ),
            },
        )

    try:
        yield SEARCH_TOPIC_ID, SEARCH_KEYWORD
    finally:
        with engine.begin() as connection:
            connection.execute(
                text("DELETE FROM articles WHERE topic_id = :topic_id"),
                {"topic_id": SEARCH_TOPIC_ID},
            )


# --- 라우터 테스트용 seam (2-4) ---------------------------------------------
# 라우터 단위 테스트는 세 seam만 가짜로 갈아끼운다: 세션(롤백), Gemini(스파이),
# 페치(스텁). DB는 실테스트DB에 그대로 두고 db_session 롤백으로 격리한다.


class FakeGemini:
    """Gemini 호출 스파이. generate/chat 호출을 기록하고 정해진 답을 돌려준다.

    - generate_calls: generate에 넘어온 prompt들(캐시 히트 시 0건이어야 함)
    - chat_calls: chat에 넘어온 messages 스냅샷들(history 순서·저장 내용 검증용)
    """

    def __init__(self) -> None:
        self.generate_calls: list[str] = []
        self.chat_calls: list[list[object]] = []
        self.generate_return = "가짜 요약 응답"
        self.chat_return = "가짜 챗 응답"

    def generate(self, prompt: str) -> str:
        self.generate_calls.append(prompt)
        return self.generate_return

    def chat(self, messages: object) -> str:
        self.chat_calls.append(list(messages))  # type: ignore[arg-type]
        return self.chat_return


class FakeFetch:
    """페치 스텁. 호출 URL을 기록하고 정해진 HTML을 돌려준다(캐시 히트 시 0건).

    error를 세팅하면 그 예외를 던져 페치 실패(500) 경로를 재현한다.
    """

    def __init__(self) -> None:
        self.calls: list[str] = []
        self.return_html = "<html><body>스텁 본문</body></html>"
        self.error: Exception | None = None

    def __call__(self, url: str) -> str:
        self.calls.append(url)
        if self.error is not None:
            raise self.error
        return self.return_html


@pytest.fixture
def fake_gemini() -> FakeGemini:
    return FakeGemini()


@pytest.fixture
def fake_fetch() -> FakeFetch:
    return FakeFetch()


@pytest.fixture
def router_client(
    db_session: Session, fake_gemini: FakeGemini, fake_fetch: FakeFetch
) -> Iterator["object"]:
    """세 seam을 오버라이드한 TestClient.

    app.dependencies/app.fetcher가 아직 없는 Red 단계에서는 이 import가 실패해
    라우터 테스트만 에러가 나고 다른 테스트 수집은 깨지지 않는다(지연 import).
    """
    from fastapi.testclient import TestClient

    from app.db import get_session
    from app.dependencies import get_fetch, get_gemini_client
    from app.main import app

    app.dependency_overrides[get_session] = lambda: db_session
    app.dependency_overrides[get_gemini_client] = lambda: fake_gemini
    app.dependency_overrides[get_fetch] = lambda: fake_fetch
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.clear()
