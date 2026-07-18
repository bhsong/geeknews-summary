"""POST /api/summarize
캐시 히트면 제미나이/페치 없이 저장분 반환
미스면 서버가 조립한 URL을 페치 -> 제목/본문 추출
-> article 저장 -> 프롬프트 -> Gemini -> summary 저장
입력은 topic_id뿐
"""

from collections.abc import Callable

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import Settings
from app.db import get_session
from app.dependencies import get_fetch, get_gemini_client, get_settings
from app.extractor import extract_body, extract_title
from app.gemini import GeminiClient
from app.models import SummarizeRequest, SummarizeResponse
from app.repositories import ArticleRepository, SummaryRepository
from app.topic import topic_url

router = APIRouter(prefix="/api", tags=["summarize"])

PROMPT_PREFIX = "다음 글을 한국어 3문장으로 요약해줘:\n\n"
BODY_LIMIT = 8000


@router.post("/summarize", response_model=SummarizeResponse)
def summarize(
    req: SummarizeRequest,
    session: Session = Depends(get_session),
    gemini: GeminiClient = Depends(get_gemini_client),
    fetch: Callable[[str], str] = Depends(get_fetch),
    settings: Settings = Depends(get_settings),
) -> SummarizeResponse:
    url = topic_url(req.topic_id)
    summaries = SummaryRepository(session)

    cached = summaries.find(req.topic_id)
    if cached is not None:
        return SummarizeResponse(url=cached.url, summary=cached.summary, cached=True)

    try:
        html = fetch(url)
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=500, detail="페이지를 가져오지 못했습니다."
        ) from exc

    # 제목/본문 모두 서버가 추출
    title = extract_title(html)
    body = extract_body(html)
    ArticleRepository(session).save(req.topic_id, title, body)

    answer = gemini.generate(PROMPT_PREFIX + body[:BODY_LIMIT])

    summaries.save(req.topic_id, url, title, answer, settings.gemini_model)
    return SummarizeResponse(url=url, summary=answer, cached=False)
