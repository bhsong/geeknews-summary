<?php
require_once __DIR__ . "/gemini.php";
require_once __DIR__ . "/summary_repo.php";
require_once __DIR__ . "/article_repo.php";
require_once __DIR__ . "/article_extractor.php";
require_once __DIR__ . "/api.php";

jsonHeader();

// POST 본문의 JSON 읽기 (CLI의 $argv[1] 대신)
$input = jsonInput();
$url = $input["url"] ?? null;

if ($url === null) {
    jsonError(400, "url 필드가 필요합니다.");
}

// $url = $argv[1];
// URL에서 topic_id 추출
if (!preg_match('/topic\?id=(\d+)/', $url, $m)) {
    jsonError(400, "topic id를 찾을 수 없습니다.");
}
$topicId = (int)$m[1];
$title = $input["title"] ?? "";

// 캐시 확인: 있으면 Gemini 호출 없이 즉시 반환
$cached = findSummary($topicId);
if ($cached !== null) {
    echo json_encode([
        "url" => $cached["url"],
        "summary" => $cached["summary"],
        "cached" => true
    ], JSON_UNESCAPED_UNICODE);
    exit;
}

$html = file_get_contents($url);

if ($html === false) {
    jsonError(500, "페이지를 가져오지 못했습니다.");
}

$text = extractBody($html);

saveArticle($topicId, $title, $text);
$prompt = "다음 글을 한국어 3문장으로 요약해줘:\n\n" . mb_substr($text, 0, 8000);

try {
    $answer = callGemini($prompt);
} catch (RuntimeException $e) {
    jsonError(500, $e->getMessage());
}

saveSummary($topicId, $url, $title, $answer, env("GEMINI_MODEL", "gemini-2.5-flash"));

echo json_encode([
    "url" => $url,
    "summary" => $answer,
    "cached" => false
], JSON_UNESCAPED_UNICODE);


