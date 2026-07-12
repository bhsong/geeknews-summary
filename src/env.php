<?php

function loadEnv(): void
{
    static $loaded = false;
    if ($loaded) {
        return;
    }
    $loaded = true;

    foreach ([__DIR__ . "/../.env", __DIR__ . "/../.env.local"] as $file) {
        if (!file_exists($file)) continue;
        foreach (file($file, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES) as $line) {
            $line = trim($line);
            if ($line === "" || str_starts_with($line, "#")) continue;
            [$key, $value] = array_pad(explode("=", $line, 2), 2, "");
            $_ENV[trim($key)] = trim($value);
        }
    }
}

function env(string $key, ?string $default = null): ?string
{
    loadEnv();
    return $_ENV[$key] ?? getenv($key) ?: $default;
}