<?php

require_once __DIR__ . '/../../src/article_extractor.php';

test('extractBody strips everything before the topictitle marker', function () {
    $html = "<div>노이즈</div><h1 class='topictitle'>제목</h1><p>본문 내용</p>";

    expect(extractBody($html))->toBe('제목본문 내용');
});

test('extractBody keeps content as-is when no topictitle marker is present', function () {
    $html = '<p>마커 없이 시작하는 본문</p>';

    expect(extractBody($html))->toBe('마커 없이 시작하는 본문');
});

test('extractBody cuts off content at the "함께보면 좋은 글" marker', function () {
    $html = "<p>본문 내용</p>함께보면 좋은 글<p>관련 글 목록</p>";

    expect(extractBody($html))->toBe('본문 내용');
});

test('extractBody cuts off content at the "댓글과 토론" marker', function () {
    $html = "<p>본문 내용</p>댓글과 토론<p>댓글 목록</p>";

    expect(extractBody($html))->toBe('본문 내용');
});

test('extractBody cuts off content at the comment_thread marker', function () {
    $html = "<p>본문 내용</p><div class='comment_thread'>댓글</div>";

    expect(extractBody($html))->toBe('본문 내용');
});

test('extractBody removes script and style blocks', function () {
    $html = "<p>본문</p><script>alert('x')</script><style>.a{color:red}</style><p>내용</p>";

    expect(extractBody($html))->toBe('본문내용');
});

test('extractBody collapses whitespace and trims the result', function () {
    $html = "  <p>여러   줄에\n\n걸친   내용</p>  ";

    expect(extractBody($html))->toBe('여러 줄에 걸친 내용');
});

test('extractTitle reads the h1 inside the topictitle block', function () {
    // news.hada.io/topic?id=N 의 실제 마크업 구조
    $html = "<div class='topictitle link'><span id='dead25000'></span>"
        . "<a href='https://github.com/DevSymphony/sym-cli' class='bold ud'>"
        . "<h1>Show GN: LLM 기반의 코드 컨벤션 린터를 만들었습니다.</h1></a> "
        . "<span class=topicurl>(github.com/DevSymphony)</span></div>";

    expect(extractTitle($html))->toBe('Show GN: LLM 기반의 코드 컨벤션 린터를 만들었습니다.');
});

test('extractTitle ignores the topicurl suffix next to the title', function () {
    $html = "<div class='topictitle link'><a href='#'><h1>제목</h1></a>"
        . "<span class=topicurl>(example.com)</span></div>";

    expect(extractTitle($html))->toBe('제목');
});

test('extractTitle strips inner tags and decodes html entities', function () {
    $html = "<div class='topictitle'><h1><em>A</em> &amp; B&#39;s &lt;guide&gt;</h1></div>";

    expect(extractTitle($html))->toBe("A & B's <guide>");
});

test('extractTitle collapses whitespace and trims the result', function () {
    $html = "<div class='topictitle'><h1>\n  여러   줄\n  제목  \n</h1></div>";

    expect(extractTitle($html))->toBe('여러 줄 제목');
});

test('extractTitle falls back to the first h1 when the topictitle marker is missing', function () {
    $html = '<article><h1>마커 없는 제목</h1><p>본문</p></article>';

    expect(extractTitle($html))->toBe('마커 없는 제목');
});

test('extractTitle returns an empty string when no h1 exists', function () {
    expect(extractTitle('<p>제목이 없는 페이지</p>'))->toBe('');
});
