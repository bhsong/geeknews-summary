<?php
require_once __DIR__ . "/gemini.php";
require_once __DIR__ . "/summary_repo.php";
require_once __DIR__ . "/article_repo.php";

header("Content-Type: application/json; charset=utf-8");

// POST 본문의 JSON 읽기 (CLI의 $argv[1] 대신)
$input = json_decode(file_get_contents("php://input"), true);
$url = $input["url"] ?? null;

if ($url === null) {
    http_response_code(400);
    echo json_encode(["error" => "url 필드가 필요합니다."], JSON_UNESCAPED_UNICODE);
    exit;
}

// $url = $argv[1];
// URL에서 topic_id 추출
if (!preg_match('/topic\?id=(\d+)/', $url, $m)) {
    http_response_code(400);
    echo json_encode(["error" => "topic id를 찾을 수 없습니다."], JSON_UNESCAPED_UNICODE);
    exit;
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
    http_response_code(500);
    echo json_encode(["error" => "페이지를 가져오지 못했습니다."], JSON_UNESCAPED_UNICODE);
    exit;
}

$text = extractBody($html);

saveArticle($topicId, $title, $text);
$prompt = "다음 글을 한국어 3문장으로 요약해줘:\n\n" . mb_substr($text, 0, 8000);

try {
    $answer = callGemini($prompt);
} catch (RuntimeException $e) {
    http_response_code(500);
    echo json_encode(["error" => $e->getMessage()], JSON_UNESCAPED_UNICODE);
    exit;
}

saveSummary($topicId, $url, $title, $answer, env("GEMINI_MODEL", "gemini-2.5-flash"));

echo json_encode([
    "url" => $url,
    "summary" => $answer,
    "cached" => false
], JSON_UNESCAPED_UNICODE);

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

