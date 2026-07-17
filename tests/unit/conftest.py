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
