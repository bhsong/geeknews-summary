"""summarize 라우터 — POST /api/summarize.

세 seam(세션·Gemini·페치)만 오버라이드하고 DB는 실테스트DB 롤백으로 격리한다.
E2E(tests/e2e)가 밖에서 본 계약이라면, 여기서는 호출 횟수·저장 부작용 같은
안에서 본 로직을 검증한다.

    APP_ENV=testing uv run pytest tests/unit -k summarize
"""

import pytest

from app.repositories import ArticleRepository, SummaryRepository
from app.topic import topic_url

# repo 테스트(999000001/2)·committed_article(999000001)과 겹치지 않는 id.
FRESH_TOPIC_ID = 999000050


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param({}, id="topic_id 누락"),
        pytest.param({"topic_id": 0}, id="0"),
        pytest.param({"topic_id": -1}, id="음수"),
        pytest.param({"topic_id": "abc"}, id="비정수 문자열"),
        pytest.param({"topic_id": "1.5"}, id="소수"),
        pytest.param({"topic_id": "https://news.hada.io/topic?id=1"}, id="URL 문자열"),
        pytest.param({"topic_id": "http://169.254.169.254/"}, id="내부 URL"),
    ],
)
def test_잘못된_입력은_400(router_client, payload):
    res = router_client.post("/api/summarize", json=payload)

    assert res.status_code == 400
    assert res.json()["error"]


def test_캐시_미스는_생성하고_저장한다(
    router_client, fake_gemini, fake_fetch, db_session
):
    res = router_client.post("/api/summarize", json={"topic_id": FRESH_TOPIC_ID})

    assert res.status_code == 200
    body = res.json()
    assert body["cached"] is False
    assert body["url"] == topic_url(FRESH_TOPIC_ID)
    assert body["summary"] == fake_gemini.generate_return

    # 미스 경로: 서버가 조립한 URL로 페치 1회, Gemini generate 1회.
    assert fake_fetch.calls == [topic_url(FRESH_TOPIC_ID)]
    assert len(fake_gemini.generate_calls) == 1

    # 부작용: article과 summary가 저장됐다(같은 db_session으로 확인).
    assert ArticleRepository(db_session).find(FRESH_TOPIC_ID) is not None
    saved = SummaryRepository(db_session).find(FRESH_TOPIC_ID)
    assert saved is not None
    assert saved.summary == fake_gemini.generate_return
    assert saved.url == topic_url(FRESH_TOPIC_ID)
