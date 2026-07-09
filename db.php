<?php
require_once __DIR__ . "/env.php";

function  getDb(): PDO
{
    return new PDO(
        "mysql:host=" . env("DB_HOST", "localhost") . ";dbname=" . env("DB_NAME") . ";charset=utf8mb4", 
        env("DB_USER"),
        env("DB_PASS"),
        [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
        ]
    );
}