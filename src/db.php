<?php
require_once __DIR__ . "/env.php";

function getDbName(): string
{
    if (env("APP_ENV") === "testing") {
        return env("DB_NAME_TEST", env("DB_NAME") . "_test");
    }
    return env("DB_NAME");
}

function  getDb(): PDO
{
    return new PDO(
        "mysql:host=" . env("DB_HOST", "localhost") . ";dbname=" . getDbName() . ";charset=utf8mb4",
        env("DB_USER"),
        env("DB_PASS"),
        [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
        ]
    );
}