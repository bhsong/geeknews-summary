<?php

/**
* 클라이언트 입력에서 topic id만 추출한다.
* 양의 정수 (또는 그 형태의 문자열)만 통과하고 나머지는 전부 null
* URL 문자열은 여기서 절대 통과할 수 없으므로 SSRF 진입점이 사라진다.
*/
function parseTopicId(mixed $input): ?int
{
    if (is_string($input)) {
        if (preg_match('/^\d+$/', $input) !== 1) {
            return null;
        }
        $input = (int) $input;
    }

    if (!is_int($input) || $input <= 0) {
        return null;
    }

    return $input;
}

/** 대상 URL을 만드는 유일한 경로. 호스트는 서버가 고정 */
function topicUrl(int $topicId): string
{
    return "https://news.hada.io/topic?id=" . $topicId;
}
