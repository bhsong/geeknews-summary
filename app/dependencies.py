"""FastAPI Depends 의존성 조립

세션(get_session)은 db.py에 있다. 여기서는 Gemini 클라이언트와 페치함수를
제공하고, 테스트는 이 심볼들을 app.dependency_overrides로 갈아끼움
"""

from collections.abc import Callable
from functools import lru_cache

from app.config import Settings
from app.fetcher import fetch_html
from app.gemini import GeminiClient


@lru_cache
def get_settings() -> Settings:
    return Settings()


def get_gemini_client() -> GeminiClient:
    settings = get_settings()
    return GeminiClient(settings.gemini_api_key, settings.gemini_model)


def get_fetch() -> Callable[[str], str]:
    """페치 함수를 주입 가능한 형태로 반환 (테스트 seam)"""
    return fetch_html
