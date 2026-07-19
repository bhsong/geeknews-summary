"""summarize 라우터 — POST /api/summarize.

세 seam(세션·Gemini·페치)만 오버라이드하고 DB는 실테스트DB 롤백으로 격리한다.
E2E(tests/e2e)가 밖에서 본 계약이라면, 여기서는 호출 횟수·저장 부작용 같은
안에서 본 로직을 검증한다.

    APP_ENV=testing uv run pytest tests/unit -k summarize
"""

import httpx
import pytest

from app.repositories import ArticleRepository, SummaryRepository
from app.topic import topic_url

# repo 테스트(999000001/2)·committed_article(999000001)과 겹치지 않는 id.
FRESH_TOPIC_ID = 999000050
CACHED_TOPIC_ID = 999000051
STRING_TOPIC_ID = 999000052
PROMPT_TOPIC_ID = 999000053
FETCH_FAIL_TOPIC_ID = 999000054


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


def test_캐시_히트는_외부호출_없이_저장분을_반환한다(
    router_client, fake_gemini, fake_fetch, db_session
):
    # 캐시를 미리 심는다. 라우터가 같은 db_session을 쓰므로 이 요약을 조회한다.
    cached_url = topic_url(CACHED_TOPIC_ID)
    SummaryRepository(db_session).save(
        CACHED_TOPIC_ID,
        cached_url,
        "캐시된 제목",
        "미리 저장된 요약",
        "gemini-2.5-flash",
    )

    res = router_client.post("/api/summarize", json={"topic_id": CACHED_TOPIC_ID})

    assert res.status_code == 200
    body = res.json()
    assert body["cached"] is True
    assert body["url"] == cached_url
    assert body["summary"] == "미리 저장된 요약"

    # 히트 경로: 페치·Gemini generate 모두 0회(E2E 밖에선 안 보이는 계약).
    assert fake_fetch.calls == []
    assert fake_gemini.generate_calls == []


def test_정수형_문자열_topic_id는_허용된다(router_client, fake_fetch):
    # S1의 "1.5"/"abc"와 달리, 정수로 강제 변환 가능한 문자열은 200.
    res = router_client.post("/api/summarize", json={"topic_id": str(STRING_TOPIC_ID)})

    assert res.status_code == 200
    body = res.json()
    assert body["cached"] is False
    assert body["url"] == topic_url(STRING_TOPIC_ID)
    # int로 변환됐음의 증거: 서버가 int로 조립한 URL로 페치했다.
    assert fake_fetch.calls == [topic_url(STRING_TOPIC_ID)]


def test_프롬프트는_지정_형식이고_본문을_8000자로_자른다(
    router_client, fake_gemini, fake_fetch
):
    # 공백 없는 CJK 반복 → _normalize가 건드리지 않아 추출 본문이 정확히 예측된다.
    body_text = "가" * 10000
    fake_fetch.return_html = (
        f'<html><body><div class="topic_contents">{body_text}</div></body></html>'
    )

    res = router_client.post("/api/summarize", json={"topic_id": PROMPT_TOPIC_ID})
    assert res.status_code == 200

    assert len(fake_gemini.generate_calls) == 1
    prompt = fake_gemini.generate_calls[0]

    prefix = "다음 글을 한국어 3문장으로 요약해줘:\n\n"
    assert prompt.startswith(prefix)

    sent_body = prompt[len(prefix) :]
    assert sent_body == "가" * 8000  # 8000자에서 절단
    assert len(sent_body) == 8000


def test_페치_실패는_500(router_client, fake_gemini, fake_fetch):
    fake_fetch.error = httpx.ConnectError("연결 실패")

    res = router_client.post("/api/summarize", json={"topic_id": FETCH_FAIL_TOPIC_ID})

    assert res.status_code == 500
    assert res.json()["error"]
    # 페치가 먼저 터지므로 Gemini는 호출되지 않는다.
    assert fake_gemini.generate_calls == []
