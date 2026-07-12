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
