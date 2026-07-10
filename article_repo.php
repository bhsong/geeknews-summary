<?php
require_once __DIR__ . "/db.php";

    function saveArticle(int $topicId, string $title, string $content): void
    {
        $sql = "INSERT INTO articles (topic_id, title, content)
                VALUES (?, ?, ?)
                ON DUPLICATE KEY UPDATE
                    title = VALUES(title), content = VALUES(content)";
        getDb()->prepare($sql)->execute([$topicId, $title, $content]);
    }

    function findArticle(int $topicId): ?array
    {
        $stmt = getDb()->prepare("SELECT * FROM articles WHERE topic_id = ?");
        $stmt->execute([$topicId]);
        $row = $stmt->fetch();
        return $row == false ? null : $row;
    }
