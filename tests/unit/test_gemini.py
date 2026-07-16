"""app.gemini.GeminiClient 단위 테스트.

Pest에 대응 테스트가 없어 신규 작성이지만, src/gemini.php의 동작(callGemini,
callGeminiChat, 키 누락·응답 파싱 실패 시 예외)을 characterization으로 승계한다.

httpx.MockTransport를 client_args로 주입해 SDK가 실제로 내보내는 HTTP 요청을
가로챈다. 덕분에 네트워크·실 API 키 없이 돌아가고, "키가 URL이 아니라 헤더로
간다"(2-3 완료 조건)와 "타임아웃이 명시된다"(이식 스펙)를 SDK 문서에 대한
신뢰가 아니라 실제 요청으로 검증할 수 있다.
"""

import json
from collections.abc import Callable
from typing import Any

import httpx
import pytest

from app.gemini import GeminiClient, GeminiError
from app.models import ChatTurn


def _reply(text: str) -> dict[str, object]:
    """Gemini generateContent 성공 응답 본문."""
    return {"candidates": [{"content": {"parts": [{"text": text}], "role": "model"}}]}


def _client(
    handler: Callable[[httpx.Request], httpx.Response],
    *,
    api_key: str = "TEST-KEY",
) -> GeminiClient:
    """MockTransport를 물린 GeminiClient. timeout_ms는 기본값을 그대로 흘린다."""
    return GeminiClient(
        api_key=api_key,
        model="gemini-2.5-flash",
        client_args={"transport": httpx.MockTransport(handler)},
    )


def test_generate_returns_response_text() -> None:
    """generate()는 응답의 텍스트를 돌려준다(구 callGemini 대응)."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=_reply("요약 결과"))

    assert _client(handler).generate("아무 프롬프트") == "요약 결과"


def test_api_key_is_sent_as_header_not_in_url() -> None:
    """API 키는 URL이 아니라 x-goog-api-key 헤더로 전달된다(2-3 완료 조건).

    구 PHP는 ?key={$apiKey}로 쿼리스트링에 실어 로그·리퍼러 노출 위험이 있었다
    (구 1-4). SDK의 헤더 전달 동작에 의존하고 있음을 못박는 회귀 테스트.
    """
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["key_header"] = request.headers.get("x-goog-api-key", "")
        return httpx.Response(200, json=_reply("ok"))

    _client(handler, api_key="SECRET-KEY-123").generate("질문")

    assert "SECRET-KEY-123" not in captured["url"]
    assert captured["key_header"] == "SECRET-KEY-123"


def test_request_has_explicit_timeout() -> None:
    """모든 요청에 타임아웃이 명시된다(이식 스펙 승계).

    구 PHP curl은 타임아웃이 없어 무한 대기가 가능했다. timeout_ms 기본값이
    실제 요청까지 흐르는지 확인해야 하므로, 이 테스트는 transport만 갈아끼우고
    timeout은 기본값을 그대로 쓴다(그래서 http_options 통째 주입이 아니라
    client_args seam이 필요하다).
    """
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["timeout"] = request.extensions["timeout"]
        return httpx.Response(200, json=_reply("ok"))

    _client(handler).generate("질문")

    # SDK가 밀리초를 받아 httpx의 초 단위로 변환한다. None이면 타임아웃 없음.
    assert captured["timeout"] == {
        "connect": 30.0,
        "read": 30.0,
        "write": 30.0,
        "pool": 30.0,
    }


def test_chat_sends_history_with_roles() -> None:
    """chat()은 대화 이력을 role과 함께 순서대로 보낸다(구 callGeminiChat 대응).

    role은 SDK 규약상 "user"/"model"이다("assistant" 아님). 구 PHP의
    ["role" => ..., "content" => ...] 배열을 ChatTurn 리스트로 승계한다.
    """
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json=_reply("답변"))

    answer = _client(handler).chat(
        [
            ChatTurn(role="user", content="Q1"),
            ChatTurn(role="model", content="A1"),
            ChatTurn(role="user", content="Q2"),
        ]
    )

    assert answer == "답변"
    assert captured["body"]["contents"] == [
        {"parts": [{"text": "Q1"}], "role": "user"},
        {"parts": [{"text": "A1"}], "role": "model"},
        {"parts": [{"text": "Q2"}], "role": "user"},
    ]


def test_raises_when_response_has_no_text() -> None:
    """응답에 텍스트가 없으면 GeminiError를 던진다.

    구 "Gemini Response Parsing Fail" 대응. 안전 필터 차단 등으로 candidates가
    비면 SDK의 response.text가 None이 되는데, 그대로 반환하면 None이 프롬프트나
    DB로 흘러간다.
    """

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"candidates": []})

    with pytest.raises(GeminiError):
        _client(handler).generate("질문")


def test_missing_api_key_raises_without_env_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """api_key가 비면 ValueError. 주변 환경변수로 조용히 폴백하지 않는다.

    구 "GEMINI_API_KEY가 설정되지 않았습니다" 대응이되, 한 가지를 더 막는다:
    SDK는 api_key가 비면 os.environ의 GEMINI_API_KEY/GOOGLE_API_KEY를 알아서
    집어 쓴다. 그러면 Settings(.env)가 설정의 단일 출처라는 전제가 깨지고,
    설정을 빠뜨렸는데도 엉뚱한 키로 호출이 나갈 수 있다. 그래서 환경변수가
    있는 상태에서도 거부하는지 확인한다(환경변수를 지우고 검증하면 SDK가
    알아서 던지므로 우리 가드가 없어도 통과해버려 무의미하다).
    """
    monkeypatch.setenv("GEMINI_API_KEY", "AMBIENT-KEY")

    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("키가 없으면 요청이 나가면 안 된다")

    with pytest.raises(ValueError):
        _client(handler, api_key="")
