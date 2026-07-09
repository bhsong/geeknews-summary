<?php
header("Content-Type: application/json; charset=UTF-8");

$html = file_get_contents("https://news.hada.io");
if ($html === false) {
    $http_response_code(500);
    echo json_encode(["error" => "목록을 가져오지 못했습니다."], JSON_UNESCAPED_UNICODE);
    exit;
}

preg_match_all('/<h2[^>]*topic-title-heading[^>]*>(.*?)<\/h2>.*?topic\?id=(\d+)&go=comments/is', $html, $m, PREG_SET_ORDER);

$items = [];
$seen = [];
foreach ($m as $match) {
    $id = $match[2];
    $title = trim(strip_tags(html_entity_decode($match[1])));
    if (isset($seen[$id]) || $title === "") continue;
    $seen[$id] = true;
    $items[] = [
        "url" => "https://news.hada.io/topic?id=" . $id,
        "title" => $title
    ];
    if (count($items) >= 10) break;
}

echo json_encode(["items" => $items, "count" => count($items)], JSON_UNESCAPED_UNICODE);
