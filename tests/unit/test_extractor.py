"""app.extractor 단위 테스트.

tests/Feature/ArticleExtractorTest.php(Pest 13케이스)의 이식본. 원본은 문자열
마커 절단 방식이었으나, 실제 GeekNews 마크업이 아래 구조임을 픽스처
(tests/fixtures/topic_real.html)로 확인하고 CSS 셀렉터 기반으로 재작성했다.

    article
    ├─ div.topic
    │  ├─ div.vote
    │  ├─ div.topictitle.link   ← 제목 (a > h1) + span.topicurl
    │  ├─ div.topicinfo         ← "40P by baeba 10시간전 | 댓글 2개"
    │  └─ div.topic_contents    ← 본문
    ├─ div.related-topics       ← 구 "함께보면 좋은 글" (해당 문자열은 이제 없음)
    ├─ h2.visually-hidden       ← "댓글과 토론"
    └─ .comment_thread

절단 마커 3종이 전부 div.topic 바깥이라 마커 절단 자체가 불필요해졌다. 따라서
extract_body는 .topic_contents만, extract_title은 .topictitle h1만 담당하고,
요약 프롬프트의 제목 조립은 호출부(2-3/2-4)가 맡는다.

원본 Pest 대응:
  #3 "함께보면 좋은 글" 절단  → 삭제 (실제 페이지에 문자열 없음)
  #4 "댓글과 토론" 절단       → 삭제 (div.topic 바깥이라 스코프 밖)
  #5 comment_thread 절단      → 재작성 (절단이 아니라 "애초에 미포함"을 검증)
  #1 topictitle 이전 제거     → 재작성 (제목·메타를 body에서 제외)
"""

from pathlib import Path

from app.extractor import extract_body, extract_title

FIXTURES = Path(__file__).parent.parent / "fixtures"


def test_extracts_title_and_body_from_real_page() -> None:
    """실제 GeekNews 페이지(topic?id=31479)에서 제목과 본문을 추출한다."""
    html = (FIXTURES / "topic_real.html").read_text(encoding="utf-8")

    assert extract_title(html) == "「Machine Learning Study 혼자 해보기」"

    body = extract_body(html)
    assert body.startswith("1. 문서의 목적과 구성")

    # 제목·메타·출처·댓글이 본문에 섞이지 않는다(셀렉터 스코프 검증).
    assert "혼자 해보기" not in body  # 제목 — title 컬럼이 따로 담당
    assert "baeba" not in body  # div.topicinfo
    assert "teddylee777" not in body  # span.topicurl
    assert "댓글과 토론" not in body  # div.topic 바깥


def test_parses_despite_attribute_order_and_whitespace_changes() -> None:
    """마크업 소폭 변경(속성 순서·따옴표·공백·클래스 추가)에도 파싱된다.

    원본 PHP의 strpos("class='topictitle") 방식은 아래 마크업 전부에서 깨진다.
    """
    html = (
        '<div class="topic">'
        '<div id="x" class = "link topictitle"  >'  # 클래스 순서 뒤바뀜, = 주변 공백
        "<a class='bold ud' href='#'>"  # 따옴표 혼용
        "<h1>  제목 </h1></a></div>"
        '<div  data-n="1"  class="topic_contents keepall">'  # 속성 순서, 클래스 추가
        "<p>본문 내용</p></div>"
        "</div>"
    )

    assert extract_title(html) == "제목"
    assert extract_body(html) == "본문 내용"


def test_extract_body_collects_only_topic_contents() -> None:
    """본문은 .topic_contents만 수집한다 — vote·제목·메타는 제외.

    제목은 extract_title이 별도로 담당하고 articles.title 컬럼에 따로 저장되므로,
    본문에 중복시키지 않는다(요약 프롬프트의 제목 조립은 호출부 책임).
    """
    html = (
        "<div class='topic'>"
        "<div class='vote'>40</div>"
        "<div class='topictitle link'><a href='#'><h1>제목</h1></a> "
        "<span class=topicurl>(example.com)</span></div>"
        "<div class='topicinfo'>40P by baeba 10시간전</div>"
        "<div class='topic_contents'><p>본문 내용</p></div>"
        "</div>"
    )

    assert extract_body(html) == "본문 내용"


def test_extract_body_falls_back_to_whole_text_without_topic_contents() -> None:
    """.topic_contents가 없으면 문서 전체 텍스트로 폴백한다."""
    html = "<p>마커 없이 시작하는 본문</p>"

    assert extract_body(html) == "마커 없이 시작하는 본문"


def test_extract_body_excludes_comment_area() -> None:
    """댓글 영역은 본문에 포함되지 않는다.

    원본 Pest는 comment_thread 마커에서 "절단"하는 동작을 검증했으나, 실제
    마크업에서 댓글 영역은 div.topic 바깥에 있어 .topic_contents 스코프에
    애초에 들어오지 않는다. 절단이 아니라 "미포함"을 검증한다.
    """
    html = (
        "<article>"
        "<div class='topic'><div class='topic_contents'><p>본문 내용</p></div></div>"
        "<h2 class='visually-hidden'>댓글과 토론</h2>"
        "<div class='comment_thread'>댓글</div>"
        "</article>"
    )

    assert extract_body(html) == "본문 내용"


def test_extract_body_removes_script_and_style_blocks() -> None:
    """script·style 블록의 내용은 본문에 섞이지 않는다.

    bs4가 script/style 내용을 Script·Stylesheet 타입으로 감싸고 get_text()는
    NavigableString·CData만 수집하므로, 별도 제거 없이 걸러진다(bs4 4.9+).
    이 동작에 의존하고 있음을 못박아두는 회귀 테스트.
    """
    html = (
        "<p>본문</p><script>alert('x')</script><style>.a{color:red}</style><p>내용</p>"
    )

    assert extract_body(html) == "본문내용"


def test_extract_body_collapses_whitespace_and_trims() -> None:
    """본문의 연속 공백·개행을 공백 하나로 접고 앞뒤를 trim한다."""
    html = "  <p>여러   줄에\n\n걸친   내용</p>  "

    assert extract_body(html) == "여러 줄에 걸친 내용"


def test_extract_title_reads_h1_in_topictitle_block() -> None:
    """제목은 .topictitle 블록 안의 h1에서 읽는다(news.hada.io 실제 마크업 구조)."""
    html = (
        "<div class='topictitle link'><span id='dead25000'></span>"
        "<a href='https://github.com/DevSymphony/sym-cli' class='bold ud'>"
        "<h1>Show GN: LLM 기반의 코드 컨벤션 린터를 만들었습니다.</h1></a> "
        "<span class=topicurl>(github.com/DevSymphony)</span></div>"
    )

    assert extract_title(html) == "Show GN: LLM 기반의 코드 컨벤션 린터를 만들었습니다."


def test_extract_title_ignores_topicurl_suffix() -> None:
    """제목 옆 span.topicurl은 h1 바깥이므로 제목에 섞이지 않는다."""
    html = (
        "<div class='topictitle link'><a href='#'><h1>제목</h1></a>"
        "<span class=topicurl>(example.com)</span></div>"
    )

    assert extract_title(html) == "제목"


def test_extract_title_strips_inner_tags_and_decodes_entities() -> None:
    """제목의 내부 태그(em 등)는 벗기고 HTML 엔티티는 디코드한다."""
    html = (
        "<div class='topictitle'><h1><em>A</em> &amp; B&#39;s &lt;guide&gt;</h1></div>"
    )

    assert extract_title(html) == "A & B's <guide>"


def test_extract_title_collapses_whitespace_and_trims() -> None:
    """제목의 연속 공백·개행을 공백 하나로 접고 앞뒤를 trim한다."""
    html = "<div class='topictitle'><h1>\n  여러   줄\n  제목  \n</h1></div>"

    assert extract_title(html) == "여러 줄 제목"


def test_extract_title_falls_back_to_first_h1_without_topictitle() -> None:
    """.topictitle 블록이 없으면 문서의 첫 h1으로 폴백한다."""
    html = "<article><h1>마커 없는 제목</h1><p>본문</p></article>"

    assert extract_title(html) == "마커 없는 제목"


def test_extract_title_returns_empty_string_when_no_h1() -> None:
    """h1이 없으면 빈 문자열을 반환한다."""
    assert extract_title("<p>제목이 없는 페이지</p>") == ""
