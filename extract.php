<?php

// $url = "https://news.hada.io/topic?id=31099";
$url = $argv[1];

$html = file_get_contents($url);

if ($html === false) {
    echo "페이지를 가져오지 못했습니다\n";
    exit(1);
}

// 1) script, style 태그는 내용까지 통째로 제거
$html = preg_replace('/<script\b[^>]*>.*?<\/script>/is', '', $html);
$html = preg_replace('/<style\b[^>]*>.*?<\/style/is', '', $html);

// 2) 나머지 태그 제거 -> 텍스트만 남음
$text = strip_tags($html);

// 3) 공백 정리: 연속된 공백/줄바꿈을 하나로
$text = preg_replace('/\s+/', ' ', $text);
$text = trim($text);

echo "추출된 텍스트 길이: " . mb_strlen($text) . " 자\n";
echo "----------\n";
echo mb_substr($text, 0, 1000) . "\n";
