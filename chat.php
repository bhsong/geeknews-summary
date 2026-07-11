<?php
require_once __DIR__ . "/gemini.php";
require_once __DIR__ . "/article_repo.php";

header("Content-Type: application/json; charset=utf-8");

$input = json_decode(file_get_contents("php://input"), true);
$question = trim($input["question"] ?? "");

if ($question  === "") {
    http_response_code(400);
    echo json_encode(["error" => "question 필드가 필요합니다."], JSON_UNESCAPED_UNICODE);
    exit;
}

// 1) 질문과 관련된 기사 검색
$articles = searchArticles($question, 3);

// 2) 검색 결과를 컨텍스트 텍스트로 조립
$context = "";
$sources = [];
foreach ($articles as $a) {
    $context .= "### 기사 #{$a['topic_id']}: {$a['title']}\n";
    $context .= "요약: " . ($a["summary"] ?? "(요약 없음)") . "\n";
    $context .= "본문: " . mb_substr($a["content"], 0, 1500) . "\n\n";
    $sources[] = [
        "topic_id" => (int)$a["topic_id"],
        "title" => $a["title"],
        "url" => "https://news.hada.io/topic?id=" . $a["topic_id"]
    ];
}

// 3) 프롬프트 조립
if ($context == "") {
    $prompt = "너는 GeekNews 기사 기반 챗봇이야. 관련 기사를 찾지 못했음을 밝히고, "
        . "일반 지식으로 간단히 답하되 기사 기반 답변이 아님을 알려줘.\n\n질문: {$question}";
} else {
    $prompt = "너는 GeekNews 기사 기반 챗봇이야. 아래 기사들을 참고해서 질문에 답변해줘. "
        . "기사에 없는 내용은 추측하지 말고 없다고 말해. 답변에서 참고한 기사 번호(#id)를 언급해줘.\n\n"
        . $context . "질문: {$question}";
}

// 4) Gemini 호출
try {
    $answer = callGemini($prompt);
} catch (RuntimeException $e) {
    http_response_code(500);
    echo json_encode(["error" => $e->getMessage()], JSON_UNESCAPED_UNICODE);
    exit;
}

echo json_encode([
    "answer" => $answer,
    "sources" => $sources
], JSON_UNESCAPED_UNICODE);
