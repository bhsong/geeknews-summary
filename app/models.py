"""pydantic 스키마 - 도메인 데이터 구조와 요청/응답 모델"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, PositiveInt


class ChatTurn(BaseModel):
    """
    Gemini에 보낼 대화 턴 하나.

    role은 Gemini SDK 규약을 따름 - "assistant"가 아니라 "model".
    DB에 저장된 메시지 행(2-4의 ChatMessage)과는 역할이 다름.
    이쪽은 "SDK로 나가는 페이로드"이고, 저쪽은 "저장된 이력"
    """

    role: Literal["user", "model"]
    content: str


class Summary(BaseModel):
    """summaries 테이블의 한 행. 스키마 원본은 Alembic 리비전"""

    topic_id: int
    url: str
    title: str
    summary: str
    model: str
    created_at: datetime
    updated_at: datetime


class Article(BaseModel):
    """articles 테이블의 한 행. 스키마 원본은 Alembic 리비전"""

    topic_id: int
    title: str
    content: str
    crawled_at: datetime


class ArticleSearchHit(BaseModel):
    """FULLTEXT 검색 결과 한 건 - articles LEFT JOIN summaries

    Article과 모양이 다름. 요약이 아직 없는 기사도 검색에 걸리므로
    summary가 nullable이고, crawled_at은 검색 결과 쓸 일이 없어 빠져 있음
    """

    topic_id: int
    title: str
    content: str
    summary: str | None


class SummarizeRequest(BaseModel):
    """
    POST /api/summarize 요청. topic_id만 받음
    PositiveInt라 0/음수는 검증 실패. 정수형 문자열은
    lax 강제 변환으로 통과하고, "1.5"/"abc"/URL 문자열은 실패
    FastAPI 기본 422는 main의 exception handler가 계약 봉투(400 + {"error"})로 변환
    """

    topic_id: PositiveInt


class SummarizeResponse(BaseModel):
    """POST /api/summarize 응답. cached=True면 Gemini/페치 없이 저장분 반환"""

    url: str
    summary: str
    cached: bool
