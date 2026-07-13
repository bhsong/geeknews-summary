<?php

require_once __DIR__ . '/../../src/topic.php';

test('parseTopicId accepts an integer', function () {
    expect(parseTopicId(123))->toBe(123);
});

test('parseTopicId accepts a numeric string', function () {
    expect(parseTopicId('123'))->toBe(123);
});

test('parseTopicId rejects zero and negative numbers', function () {
    expect(parseTopicId(0))->toBeNull();
    expect(parseTopicId(-1))->toBeNull();
    expect(parseTopicId('-5'))->toBeNull();
});

test('parseTopicId rejects missing or empty input', function () {
    expect(parseTopicId(null))->toBeNull();
    expect(parseTopicId(''))->toBeNull();
});

test('parseTopicId rejects non-numeric input', function () {
    expect(parseTopicId('abc'))->toBeNull();
    expect(parseTopicId('12abc'))->toBeNull();
    expect(parseTopicId('1 OR 1=1'))->toBeNull();
    expect(parseTopicId(['id' => 1]))->toBeNull();
    expect(parseTopicId(1.5))->toBeNull();
});

test('parseTopicId rejects a URL even when it contains a topic id', function () {
    expect(parseTopicId('https://news.hada.io/topic?id=123'))->toBeNull();
    expect(parseTopicId('https://evil.example.com/topic?id=123'))->toBeNull();
    expect(parseTopicId('http://169.254.169.254/topic?id=1'))->toBeNull();
    expect(parseTopicId('file:///etc/passwd'))->toBeNull();
});

test('topicUrl builds the url from the geeknews host only', function () {
    expect(topicUrl(123))->toBe('https://news.hada.io/topic?id=123');
});

test('topicUrl never reflects attacker-controlled hosts', function () {
    // parseTopicId를 통과한 값(정수)만 들어오므로 호스트 주입 경로가 없다
    $id = parseTopicId('456');

    expect($id)->not->toBeNull();
    expect(topicUrl($id))->toStartWith('https://news.hada.io/topic?id=');
    expect(topicUrl($id))->toBe('https://news.hada.io/topic?id=456');
});
