"""app.db 단위 테스트 — src/db.php::getDb() 이식.

세션 격리 fixture(db_session)와 FastAPI Depends용 get_session을 검증한다.
실제 테스트 MySQL이 필요하다(미연결 시 db_session이 skip 처리).
"""

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session


def test_db_session_executes_query(db_session: Session) -> None:
    """db_session fixture가 테스트 DB에 연결되어 쿼리를 실행한다."""
    result = db_session.execute(text("SELECT 1")).scalar_one()

    assert result == 1


def test_get_session_yields_usable_session(require_test_db: None) -> None:
    """get_session Depends는 사용 가능한 Session을 yield하고 소진 시 정리한다."""
    from app.db import get_session

    gen = get_session()
    session = next(gen)
    assert isinstance(session, Session)
    assert session.execute(text("SELECT 1")).scalar_one() == 1

    # 제너레이터를 소진해 teardown(세션 정리)을 에러 없이 실행시킨다.
    with pytest.raises(StopIteration):
        next(gen)
