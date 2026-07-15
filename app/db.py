"""SQLAlchemy 엔진/세션

create_engine의 커넥션 풀이 구 1-2(PDO 재사용) 문제를 구조적으로 소멸시킴
엔진은 애플리케이션 수명 동안 1개(풀 보유)이며, database_url이 AP_ENV=testing
분기를 상속하므로 테스트 시 자동으로 테스트 DB에 연결됨
"""

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import Settings

settings = Settings()
engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_session() -> Iterator[Session]:
    """FastAPI Depends용 세션 의존성. 요청 종료 시 세션 닫기"""
    with SessionLocal() as session:
        yield session
