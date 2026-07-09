CREATE TABLE chat_session (
    id              INT UNSIGNED NOT NULL AUTO_INCREMENT,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE chat_message (
    id              INT UNSIGNED NOT NULL AUTO_INCREMENT,
    session_id      INT UNSIGNED NOT NULL,
    role            ENUM('user', 'model') NOT NULL,
    content         TEXT NOT NULL,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_session (session_id),
    CONSTRAINT fk_messages_session FOREIGN KEY (session_id)
        REFERENCES chat_session(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;