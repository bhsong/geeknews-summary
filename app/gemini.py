"""Gemini API 클라이언트

google-genai 공식 SDK
API 키는 SDK가 x-goog-api-key 헤더로 전달하므로 URL 쿼리스트링에
노출되지 않는다
"""

from collections.abc import Sequence

from google import genai
from google.genai import types
from google.genai.types import GenerateContentResponse

from app.models import ChatTurn

DEFAULT_TIMEOUT_MS = 30_000


class GeminiError(RuntimeError):
    """Gemini 응답을 해석할 수 없을 때"""


def _text_of(response: GenerateContentResponse) -> str:
    """응답에서 텍스트 꺼냄. 없으면 GeminiError"""
    if response.text is None:
        raise GeminiError("Gemini 응답에 텍스트가 없습니다")
    return response.text


class GeminiClient:
    """Gemini 호출 담당. 키/모델/HTTP 클라이언트 상태 보유"""

    def __init__(
        self,
        api_key: str,
        model: str,
        *,
        timeout_ms: int = DEFAULT_TIMEOUT_MS,
        client_args: dict[str, object] | None = None,
    ) -> None:
        # SDK는 api_key가 비면 os.environ의 GEMINI_API_KEY/GOOGLE_API_KEY로
        # 폴백함. 설정 출처를 Settings(.env) 하나로 유지하기 위해 먼저 막음
        if not api_key:
            raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다.")

        self._model = model
        self._client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(
                timeout=timeout_ms,
                client_args=client_args,
            ),
        )

    def generate(self, prompt: str) -> str:
        """단발 프롬프트로 텍스트 생성"""
        response = self._client.models.generate_content(
            model=self._model,
            contents=prompt,
        )
        return _text_of(response)

    def chat(self, messages: Sequence[ChatTurn]) -> str:
        """대화 이력 포함해 텍스트 생성"""
        contents = [
            types.Content(role=turn.role, parts=[types.Part(text=turn.content)])
            for turn in messages
        ]
        response = self._client.models.generate_content(
            model=self._model,
            contents=contents,
        )
        return _text_of(response)
