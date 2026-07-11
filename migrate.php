<?php
require_once __DIR__ . "/db.php";

$setup = new PDO(
    "mysql:host=" . env("DB_HOST", "localhost") . ";charset=utf8mb4",
    env("DB_USER"),
    env("DB_PASS"),
    [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]
);
$setup->exec("CREATE DATABASE IF NOT EXISTS `" . getDbName() . "` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci");

$pdo = getDb();

// 실행 이력 테이불 (없으면 생성)
$pdo->exec("CREATE TABLE IF NOT EXISTS `migrations` (
    filename VARCHAR(255) NOT NULL PRIMARY KEY,
    applied_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4");

// 이미 적용된 파일 목록
$applied = $pdo->query("SELECT filename FROM migrations")->fetchAll(PDO::FETCH_COLUMN);

// migrations 폴더의 .sql 파일을 이름순으로
$files = glob(__DIR__ . "/migrations/*.sql");
sort($files);

$ran = 0;
foreach ($files as $file) {
    $name = basename($file);
    if (in_array($name, $applied)) {
        continue;
    }
    echo "적용 중: {$name}\n";
    $pdo->exec(file_get_contents($file));
    $pdo->prepare("INSERT INTO migrations (filename) VALUES (?)")->execute([$name]);
    $ran++;
}

echo $ran === 0 ? "적용할 마이그레이션이 없습니다.\n" : "완료: {$ran}개 적용됨.\n";