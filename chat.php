<?php
require_once __DIR__ . "/gemini.php";
require_once __DIR__ . "/article_repo.php";
require_once __DIR__ . "/chat_repo.php";
require_once __DIR__ . "/api.php";

jsonHeader();

$input = jsonInput();
$question = trim($input["question"] ?? "");
$sessionId = isset($input["session_id"]) ? (int)$input["session_id"] : null;

if ($question  === "") {
    jsonError(400, "question 필드가 필요합니다.");
}

// 세션 확보: 없거나 유효하지 않으면 새로 생성
if ($sessionId === null || !sessionExists($sessionId)) {
    $sessionId = createSession();
}

// 이전 대화 불러오기 (질문 저장 전에!)
$history = getRecentMessages($sessionId);

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

// 메시지 배열:; 이전 대화 + 이번 질문(컨텍스트 포함 프롬프트)
$messages = $history;
$messages[] = ["role" => "user", "content" => $prompt];

// 4) Gemini 호출
try {
    $answer = callGeminiChat($messages);
} catch (RuntimeException $e) {
    jsonError(500, $e->getMessage());
}

// 대화 저장: DB에는 원본 질문만 (컨텍스트 덩어리 말고)
addMessage($sessionId, "user", $question);
addMessage($sessionId, "model", $answer);

echo json_encode([
    "session_id" => $sessionId,
    "answer" => $answer,
    "sources" => $sources
], JSON_UNESCAPED_UNICODE);
