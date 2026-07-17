"""topic_url — 대상 URL을 만드는 유일한 경로.

원본 Unit/TopicTest.php의 topicUrl 2케이스를 옮겼다. 같은 파일의 parseTopicId
6케이스는 pydantic(topic_id: PositiveInt)이 대신하므로 라우터의 400 테스트
(test_summarize.py)로 흡수했다.

호스트는 서버가 상수로 들고 있고 인자는 정수뿐이라, 클라이언트가 호스트를
주입할 경로가 구조적으로 없다(SSRF 스펙 승계).
"""

from app.topic import topic_url


def test_topic_url은_geeknews_호스트로만_조립한다():
    assert topic_url(123) == "https://news.hada.io/topic?id=123"


def test_topic_url은_정수만_받으므로_호스트가_바뀌지_않는다():
    # 라우터에서 pydantic 검증을 통과한 값(양의 정수)만 여기 도달한다.
    assert topic_url(456).startswith("https://news.hada.io/topic?id=")
    assert topic_url(456) == "https://news.hada.io/topic?id=456"
