CREATE TABLE summaries (
    topic_id        INT UNSIGNED    NOT NULL,
    url             VARCHAR(500)    NOT NULL,
    title           VARCHAR(500)    NOT NULL DEFAULT '',
    summary         TEXT            NOT NULL,
    model           VARCHAR(50)     NOT NULL DEFAULT '',
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (topic_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;