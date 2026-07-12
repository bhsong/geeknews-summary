<?php
require_once __DIR__ . "/db.php";

// READ: 있으면 배열, 없으면 null
function findSummary(int $topicId): ?array
{
    $stmt = getDb()->prepare("SELECT * FROM summaries WHERE topic_id = ?");
    $stmt->execute([$topicId]);
    $row = $stmt->fetch();
    return $row === false ? null : $row;
}

// CREATE or UPDATE (upsert)
function saveSummary(int $topicId, string $url, string $title, string $summary, string $model): void
{
    $sql = "INSERT INTO summaries (topic_id, url, title, summary, model) 
            VALUES (?, ?, ?, ?, ?)
            ON DUPLICATE KEY UPDATE
            url = VALUES(url), title = VALUES(title),
            summary = VALUES(summary), model = VALUES(model)";
    getDb()->prepare($sql)->execute([$topicId, $url, $title, $summary, $model]);
}

// DELETE
function deleteSummary(int $topicId): void
{
    getDb()->prepare("DELETE FROM summaries WHERE topic_id = ?")->execute([$topicId]);
}

// READ ALL (최신순)
function listSummary(int $limit = 50): array
{
    $stmt = getDb()->prepare("SELECT * FROM summaries ORDER BY updated_at DESC LIMIT ?");
    $stmt->bindValue(1, $limit, PDO::PARAM_INT);
    $stmt->execute();
    return $stmt->fetchAll();
}
