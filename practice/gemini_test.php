<?php

$apiKey = getenv("GEMINI_API_KEY");
if ($apiKey === false) {
    echo "GEMINI_API_KEY 환경변수가 없습니다.\n";
    exit(1);
}

$model = "gemini-2.5-flash";
$url = "https://generativelanguage.googleapis.com/v1beta/models/{$model}:generateContent?key={$apiKey}";

// 보낼 데이터 (Gemini API 형식)
$payload = [
    "contents" => [
        [
            "parts" => [
                ["text" => "WSL이 뭔지 초등학생에게 설명해줘"]
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

echo $answer . "\n";
