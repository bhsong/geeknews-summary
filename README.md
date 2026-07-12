# GeekNews 요약 + 챗봇

## 요구사항
- PHP 8.1+ (php-cli, php-curl, php-mysql, php-mbstring, php-xml)
- MySQL 8.0+ (ngram FULLTEXT 파서 필요 — MariaDB 불가)
- 브라우저

## 설치
1. 저장소 클론
2. MySQL에 DB/사용자 생성:
   CREATE DATABASE geeknews CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   CREATE USER 'appuser'@'localhost' IDENTIFIED BY '비밀번호';
   GRANT ALL PRIVILEGES ON geeknews.* TO 'appuser'@'localhost';
3. `.env.local` 생성:
   DB_PASS=비밀번호
   GEMINI_API_KEY=키
4. php migrate.php
5. php -S localhost:8000 → http://localhost:8000
