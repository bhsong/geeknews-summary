<?php

require_once __DIR__ . "/../../src/gemini.php";
require_once __DIR__ . "/../../src/summary_repo.php";
require_once __DIR__ . "/../../src/article_repo.php";
require_once __DIR__ . "/../../src/article_extractor.php";
require_once __DIR__ . "/../../src/topic.php";
require_once __DIR__ . "/../../src/api.php";

jsonHeader();

$input = jsonInput();
$topicId = parseTopicId($input["topic_id"] ?? null);

if ($topicId === null) {
    jsonError(400, "topic_id(양의 정수)가 필요합니다.");
}

// 대상 URL은 서버가 조립. 클라이언트가 준 URL은 어디에도 쓰지 않음
$url = topicUrl($topicId);

// 캐시 확인: 있으면 Gemini 호출 없이 즉시 반환
$cached = findSummary($topicId);
if ($cached !== null) {
    echo json_encode([
        "url" => $cached["url"],
        "summary" => $cached["summary"],
        "cached" => true,
    ], JSON_UNESCAPED_UNICODE);
    exit;
}

$html = file_get_contents($url); // 1-4에서 공용 httpGet()으로 교체 예정

if ($html === false) {
    jsonError(500, "페이지를 가져오지 못했습니다.");
}

// 제목도 서버가 직접 추출 (클라이언트 입력 신뢰 제거)
$title = extractTitle($html);
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
    "cached" => false,
], JSON_UNESCAPED_UNICODE);
