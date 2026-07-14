"""POST /api/chat 계약.

question이 필수이고, 응답은 session_id / answer / sources 세 키를 가진다.
sources는 검색된 기사가 없으면 빈 배열일 수 있다.
"""

import pytest

# seeded_topic이 시딩하는 기사(GeekNews 사이트 오픈)에 FULLTEXT로 매칭되는 질문.
QUESTION = "GeekNews 사이트는 어떤 곳이야?"


@pytest.fixture(scope="module")
def answer(client, api_path, seeded_topic) -> dict:
    """Gemini를 실제로 부르는 유일한 지점. 모듈 전체가 이 응답 하나를 공유한다."""
    res = client.post(api_path("chat"), json={"question": QUESTION})

    assert res.status_code == 200
    return res.json()


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param({}, id="question 누락"),
        pytest.param({"question": ""}, id="빈 문자열"),
        pytest.param({"question": "   "}, id="공백뿐"),
    ],
)
def test_question이_없으면_400(client, api_path, payload):
    res = client.post(api_path("chat"), json=payload)

    assert res.status_code == 400
    assert res.json()["error"]


def test_응답_구조(answer):
    assert isinstance(answer["session_id"], int)
    assert answer["answer"].strip()
    assert isinstance(answer["sources"], list)


def test_sources_항목_구조(answer, seeded_topic):
    sources = answer["sources"]

    # 빈 배열이면 아래 검증이 통째로 무의미해진다.
    assert sources, "검색된 기사가 없어 sources 계약을 검증하지 못했다"
    assert seeded_topic in [s["topic_id"] for s in sources]

    for source in sources:
        assert isinstance(source["topic_id"], int)
        assert isinstance(source["title"], str)
        assert source["url"] == f"https://news.hada.io/topic?id={source['topic_id']}"


def test_session_id를_넘기면_같은_세션이_유지된다(client, api_path, answer):
    res = client.post(
        api_path("chat"),
        json={"question": "방금 뭐라고 했어?", "session_id": answer["session_id"]},
    )

    assert res.status_code == 200
    assert res.json()["session_id"] == answer["session_id"]
