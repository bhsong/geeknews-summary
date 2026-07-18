"""외부 페이지 페치

모든 외부 HTTP에 타임아웃 명시.
USER-Agent 명시 (크롤링 에티켓).
라우터/3-1 크롬 CLI 공용. 4xx/5xx면 httpx가 예외 던지고 라우터가 500으로 매핑
"""

import httpx

FETCH_TIMEOUT_S = 10.0
USER_AGENT = "geeknews-summary/0.1 (+https://news.hada.io)"


def fetch_html(url: str) -> str:
    """url의 HTML을 텍스트로 가져옴"""
    with httpx.Client(
        timeout=FETCH_TIMEOUT_S,
        headers={"User-Agent": USER_AGENT},
        follow_redirects=True,
    ) as client:
        response = client.get(url)
        response.raise_for_status()
        return response.text
