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
