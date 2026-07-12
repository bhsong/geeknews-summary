<?php
require_once __DIR__ . "/env.php";

// 성공 시 답변 텍스트, 실패 시 예외
function sendGeminiRequest(array $contents): string
{
    $apiKey = env("GEMINI_API_KEY");
    if ($apiKey === null) {
        throw new RuntimeException("GEMINI_API_KEY가 설정되지 않았습니다.");
    }

    $model = env("GEMINI_MODEL", "gemini-2.5-flash");
    $url = "https://generativelanguage.googleapis.com/v1beta/models/{$model}:generateContent?key={$apiKey}";

    $ch = curl_init($url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_HTTPHEADER, ["Content-Type: application/json"]);
    curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode(["contents" => $contents]));

    $response = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);

    if ($httpCode != 200) {
        throw new RuntimeException("Gemini API Error (HTTP {$httpCode}): {$response}");
    }

    $data = json_decode($response, true);
    $answer = $data["candidates"][0]["content"]["parts"][0]["text"] ?? null;
    if ($answer === null) {
        throw new RuntimeException("Gemini Response Parsing Fail");
    }
    return $answer;
}

// 성공 시 답변 텍스트, 실패 시 예외
function callGemini(string $prompt): string
{
    return sendGeminiRequest([
        ["parts" => [["text" => $prompt]]]
    ]);
}

// $messages: [["role" => "user"|"model", "content" => "..."], ...]
function callGeminiChat(array $messages): string
{
    $contents = [];
    foreach ($messages as $m) {
        $contents[] = [
            "role" => $m["role"],
            "parts" => [["text" => $m["content"]]]
        ];
    }
    return sendGeminiRequest($contents);
}