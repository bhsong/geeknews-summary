"""pydantic 스키마 - 도메인 데이터 구조와 요청/응답 모델"""

from typing import Literal

from pydantic import BaseModel


class ChatTurn(BaseModel):
    """
    Gemini에 보낼 대화 턴 하나.

    role은 Gemini SDK 규약을 따름 - "assistant"가 아니라 "model".
    DB에 저장된 메시지 행(2-4의 ChatMessage)과는 역할이 다름.
    이쪽은 "SDK로 나가는 페이로드"이고, 저쪽은 "저장된 이력"
    """

    role: Literal["user", "model"]
    content: str
