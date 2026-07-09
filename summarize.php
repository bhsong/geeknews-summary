<?php
require_once __DIR__ . "/env.php";
require_once __DIR__ . "/summary_repo.php";
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

// 1) script, style 태그는 내용까지 통째로 제거
$html = preg_replace('/<script\b[^>]*>.*?<\/script>/is', '', $html);
$html = preg_replace('/<style\b[^>]*>.*?<\/style/is', '', $html);

// 2) 나머지 태그 제거 -> 텍스트만 남음
$text = strip_tags($html);

// 3) 공백 정리: 연속된 공백/줄바꿈을 하나로
$text = preg_replace('/\s+/', ' ', $text);
$text = trim($text);

$apiKey = env("GEMINI_API_KEY");
if ($apiKey === null) {
    echo "GEMINI_API_KEY 환경변수가 없습니다.\n";
    exit(1);
}

$model = env("GEMINI_MODEL", "gemini-2.5-flash");
$url = "https://generativelanguage.googleapis.com/v1beta/models/{$model}:generateContent?key={$apiKey}";
$prompt = "다음 글을 한국어 3문장으로 요약해줘:\n\n" . mb_substr($text, 0, 8000);

// 보낼 데이터 (Gemini API 형식)
$payload = [
    "contents" => [
        [
            "parts" => [
                ["text" => $prompt]
            ]
        ]
    ]
];

// curl로 POST 요청
$ch = curl_init($url);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_POST, true);
curl_setopt($ch, CURLOPT_HTTPHEADER, ["Content-Type: application/json"]);
curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($payload));

$response = curl_exec($ch);
$httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
curl_close($ch);

if ($httpCode !== 200) {
    echo "API 오류 (HTTP {$httpCode}:\n{$response}\n";
    exit(1);
}

// JSON 응답에서 답변 텍스트만 꺼내기
$data = json_decode($response, true);
$answer = $data["candidates"][0]["content"]["parts"][0]["text"] ?? "(응답 파싱 실패)";

saveSummary($topicId, $url, $title, $answer, "gemini-2.5-flash");

echo json_encode([
    "url" => $url,
    "summary" => $answer,
    "cached" => false
], JSON_UNESCAPED_UNICODE);



