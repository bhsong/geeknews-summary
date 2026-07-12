<?php

function jsonHeader(): void
{
    header("Content-Type: application/json; charset=utf-8");
}

function jsonInput(): ?array
{
    return json_decode(file_get_contents("php://input"), true);
}

function jsonError(int $httpCode, string $message): never
{
    http_response_code($httpCode);
    echo json_encode(["error" => $message], JSON_UNESCAPED_UNICODE);
    exit;
}