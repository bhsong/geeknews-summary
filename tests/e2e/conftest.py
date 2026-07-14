"""E2E 계약 테스트 공용 fixture.

같은 테스트를 PHP 서버와 FastAPI 서버 양쪽에 실행한다(1-1 characterization).

    # PHP (레거시)
    APP_ENV=testing php -S localhost:8000 -t public
    E2E_BASE_URL=http://localhost:8000 E2E_API_SUFFIX=.php uv run pytest tests/e2e

    # FastAPI (2-4 이후)
    E2E_BASE_URL=http://localhost:8000 uv run pytest tests/e2e
"""

import os

import httpx
import pymysql
import pytest
from dotenv import load_dotenv

# src/env.php와 같은 순서: .env 다음 .env.local이 덮어쓴다 (비밀값은 .env.local).
load_dotenv(".env")
load_dotenv(".env.local", override=True)

# PHP는 api/summarize.php, FastAPI는 /api/summarize 로 서빙한다.
API_SUFFIX = os.getenv("E2E_API_SUFFIX", "")

# 캐시 미스 경로를 검증할 GeekNews topic. 실제로 존재하는 id여야 한다.
TOPIC_ID = int(os.getenv("E2E_TOPIC_ID", "1"))


@pytest.fixture(scope="session")
def api_path():
    """엔드포인트 이름을 서버 구현에 맞는 경로로 바꾼다."""

    def path(name: str) -> str:
        return f"/api/{name}{API_SUFFIX}"

    return path


def _test_db_name() -> str:
    """src/db.php의 getDbName()과 동일한 규칙 (APP_ENV=testing 가정)."""
    name = os.getenv("DB_NAME_TEST") or f"{os.getenv('DB_NAME', '')}_test"
    if not name or name == "_test":
        pytest.skip("DB_NAME_TEST 또는 DB_NAME이 설정되지 않았습니다.")
    if name == os.getenv("DB_NAME"):
        pytest.fail("테스트 DB명이 운영 DB명과 같습니다. DB_NAME_TEST를 분리하세요.")
    return name


@pytest.fixture(scope="session")
def base_url() -> str:
    url = os.getenv("E2E_BASE_URL")
    if not url:
        pytest.skip("E2E_BASE_URL이 없어 E2E를 건너뜁니다.")
    return url.rstrip("/")


@pytest.fixture(scope="session")
def client(base_url: str):
    # 요약은 크롤링 + Gemini 호출이라 느리다. 넉넉히 잡는다.
    with httpx.Client(base_url=base_url, timeout=60.0) as c:
        yield c


@pytest.fixture(scope="session")
def db():
    conn = pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", ""),
        password=os.getenv("DB_PASS", ""),
        database=_test_db_name(),
        charset="utf8mb4",
        autocommit=True,
    )
    with conn:
        yield conn


@pytest.fixture
def fresh_topic(db) -> int:
    """TOPIC_ID의 요약/본문 행을 지워 캐시 미스 상태를 만든다.

    삭제 엔드포인트가 없어 블랙박스만으로는 캐시 미스를 재현할 수 없다.
    이 fixture 덕에 몇 번을 돌려도 같은 결과가 나온다.
    """
    with db.cursor() as cur:
        cur.execute("DELETE FROM summaries WHERE topic_id = %s", (TOPIC_ID,))
        cur.execute("DELETE FROM articles WHERE topic_id = %s", (TOPIC_ID,))
    return TOPIC_ID


@pytest.fixture(scope="session")
def seeded_topic(client, api_path) -> int:
    """chat이 검색할 기사를 보장한다.

    articles가 비어 있으면 chat의 sources가 항상 빈 배열이라 계약을 검증할 수 없다.
    이미 요약돼 있으면 캐시 히트라 Gemini를 부르지 않는다.
    """
    res = client.post(api_path("summarize"), json={"topic_id": TOPIC_ID})

    assert res.status_code == 200, "chat 테스트용 기사 시딩 실패"
    return TOPIC_ID
