<?php

$url = "https://example.com";

$html = file_get_contents($url);

if ($html === false) {
    echo "페이지를 가져오지 못했습니다\n";
    exit(1);
}

preg_match('/<title>(.*?)<\/title>/', $html, $matches);

echo "가져온 HTML 길이: " . strlen($html) . " 바이트\n";
echo "---------------\n";
echo substr($html,0,500);
echo "\n";
echo "--------------\n";
echo $matches[1];
echo "\n";
