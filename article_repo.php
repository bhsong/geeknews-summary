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

    function searchArticles(string $query, int $limit=3): array
    {
        $sql = "SELECT a.topic_id, a.title, a.content,
                        s.summary,
                        MATCH(a.title, a.content) AGAINST(? IN NATURAL LANGUAGE MODE) AS score
                FROM articles a
                LEFT JOIN summaries s ON s.topic_id = a.topic_id
                WHERE MATCH(a.title, a.content) AGAINST(? IN NATURAL LANGUAGE MODE)
                ORDER BY score DESC
                LIMIT ?";
        $stmt = getDb()->prepare($sql);
        $stmt->bindValue(1, $query);
        $stmt->bindValue(2, $query);
        $stmt->bindValue(3, $limit, PDO::PARAM_INT);
        $stmt->execute();
        return $stmt->fetchAll();
    }