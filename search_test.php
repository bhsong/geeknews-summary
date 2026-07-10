<?php
require_once __DIR__ . "/article_repo.php";

$query = $argv[1] ?? null;
if ($query === null) {
    echo "사용법: php search_test.php \"검색어\"\n";
    exit(1);
}

$results = searchArticles($query);

if (count($results) === 0) {
    echo "검색 결과 없음\n";
    exit;
}

foreach ($results as $r) {
    printf("[%.2f] #%d %s\n", $r["score"], $r["topic_id"], $r["title"]);
    echo "  요약: " . mb_substr($r["summary"] ?? "(없음)", 0, 80) . "...\n\n";
}