CREATE TABLE articles (
    topic_id        INT UNSIGNED NOT NULL,
    title           VARCHAR(500) NOT NULL DEFAULT '',
    content         MEDIUMTEXT NOT NULL,
    crawled_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (topic_id),
    FULLTEXT KEY ft_content (title, content) WITH PARSER ngram
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;