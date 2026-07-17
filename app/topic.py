"""GeekNews topic 식별자 -> URL 조립

대상 URL을 만드는 유일한 경로. 호스트는 서버가 상수로 고정하고
인자는 정수만 받으므로, 클라이언트 입력이 호스트에 닿는 경로 없음
(SSRF 스펙 승계)
"""

TOPIC_URL_BASE = "https://news.hada.io/topic?id="


def topic_url(topic_id: int) -> str:
    return f"{TOPIC_URL_BASE}{topic_id}"
