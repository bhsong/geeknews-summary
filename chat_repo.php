<?php
require_once __DIR__ . "/db.php";

function createSession(): int
{
    $db = getDb();
    $db->exec("INSERT INTO chat_session () VALUES ()");
    return (int)$db->lastInsertId();
}

function sessionExists(int $sessionId): bool
{
    $stmt = getDb()->prepare("SELECT 1 FROM chat_session WHERE id=?");
    $stmt->execute([$sessionId]);
    return $stmt->fetch() !== false;
}

function addmessage(int $sessionId, string $role, string $content): void
{
    $stmt = getDb()->prepare(
        "INSERT INTO chat_message (session_id, role, content) VALUES (?,?,?)"
    );
    $stmt->execute([$sessionId, $role, $content]);
}

// 최근 N개를 시간순으로 (토근 절략 위해 오래된 건 잘라냄)
function getRecentMessages(int $sessionId, int $limit = 20): array
{
    $stmt = getDb()->prepare(
        "SELECT role, content FROM (
            SELECT role, content, id FROM chat_message
            WHERE session_id = ? ORDER BY id DESC LIMIT ?
        ) t ORDER BY id ASC"
    );
    $stmt->bindValue(1, $sessionId, PDO::PARAM_INT);
    $stmt->bindValue(2, $limit, PDO::PARAM_INT);
    $stmt->execute();
    return $stmt->fetchAll();
}