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
