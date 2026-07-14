"""POST /api/summarize 계약.

입력은 topic_id(양의 정수)뿐이다. URL을 넘겨도 통과하지 못한다(SSRF 방지 스펙).
"""

import pytest


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
def test_잘못된_입력은_400(client, api_path, payload):
    res = client.post(api_path("summarize"), json=payload)

    assert res.status_code == 400
    assert res.json()["error"]


def test_캐시_미스_후_히트(client, api_path, fresh_topic):
    miss = client.post(api_path("summarize"), json={"topic_id": fresh_topic})

    assert miss.status_code == 200
    body = miss.json()
    assert body["cached"] is False
    assert body["url"] == f"https://news.hada.io/topic?id={fresh_topic}"
    assert body["summary"].strip()

    # 같은 topic을 다시 요청하면 Gemini 호출 없이 저장된 요약을 그대로 돌려준다.
    hit = client.post(api_path("summarize"), json={"topic_id": fresh_topic})

    assert hit.status_code == 200
    cached = hit.json()
    assert cached["cached"] is True
    assert cached["url"] == body["url"]
    assert cached["summary"] == body["summary"]

    # 정수형 문자열도 양의 정수로 통과한다 (캐시 히트라 Gemini 호출 없음).
    as_string = client.post(api_path("summarize"), json={"topic_id": str(fresh_topic)})

    assert as_string.status_code == 200
    assert as_string.json()["cached"] is True
