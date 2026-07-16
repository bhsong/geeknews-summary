"""GeekNews topic 페이지에서 제목/본문을 추출한다.

BeautifulSoup(lxml) DOM 셀렉터로 처리
"""

import re

from bs4 import BeautifulSoup


def _normalize(text: str) -> str:
    """연속 공백/개행을 공백 하나로 접고 앞뒤를 trim"""
    return re.sub(r"\s+", " ", text).strip()


def extract_title(html: str) -> str:
    """
    .topictitle 블록의 h1애서 제목 읽음.
    없으면 문서의 첫 h1으로 폴백.
    """
    soup = BeautifulSoup(html, "lxml")

    heading = soup.select_one(".topictitle h1") or soup.select_one("h1")
    if heading is None:
        return ""

    return _normalize(heading.get_text())


def extract_body(html: str) -> str:
    """
    topic_contents에서 본문 텍스트 읽음.
    없으면 문서 전체로 폴백
    """
    soup = BeautifulSoup(html, "lxml")

    contents = soup.select_one(".topic_contents")
    scope = soup if contents is None else contents

    return _normalize(scope.get_text())
