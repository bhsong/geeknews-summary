<?php

function extractBody(string $html): string
{
    $start = strpos($html, "class='topictitle");
    if ($start !== false) {
        // 마커 지정 이후 첫 '>'까지 건너뛰어 태그를 온전히 통과
        $gt = strpos($html, ">", $start);
        $html = substr($html, $gt == false ? $start : $gt + 1);
    }

    foreach (["함께보면 좋은 글", "댓글과 토론", "class='comment_thread"] as $marker) {
        $pos = strpos($html, $marker);
        if ($pos !== false) {
            $html = substr($html, 0, $pos);
        }
    }

    $html = preg_replace('/<script\b[^>]*>.*?<\/script>/is', '', $html);
    $html = preg_replace('/<style\b[^>]*>.*?<\/style>/is', '', $html);
    $text = strip_tags($html);
    $text = preg_replace('/\s+/', ' ', $text);
    return trim($text);
}

function extractTitle(string $html): string
{
    // 제목 h1은 .topictitle 블록 안에 있다. 마커가 없으면 문서의 첫 h1로 폴백.
    $scope = $html;
    $start = strpos($html, "class='topictitle");
    if ($start !== false) {
        $scope = substr($html, $start);
    }

    if (preg_match('/<h1\b[^>]*>(.*?)<\/h1>/is', $scope, $m) !== 1) {
        return '';
    }

    // string_tags 먼저, 엔티티 디코드는 나중에 (디코드로 생긴 <. >가 태그로 오인되지 않도록)
    $title = html_entity_decode(strip_tags($m[1]), ENT_QUOTES | ENT_HTML5, 'UTF-8');
    $title = (string) preg_replace('/\s+/u', ' ', $title);

    return trim($title);
}
