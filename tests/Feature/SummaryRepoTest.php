<?php

require_once __DIR__ . '/../../summary_repo.php';

beforeEach(function () {
    $this->topicId = 999000002;
});

afterEach(function () {
    deleteSummary($this->topicId);
});

test('findSummary returns null when no summary exists', function () {
    expect(findSummary($this->topicId))->toBeNull();
});

test('saveSummary inserts a new summary that findSummary can read back', function () {
    saveSummary($this->topicId, 'https://news.hada.io/topic?id=999000002', '테스트 제목', '테스트 요약', 'gemini-2.5-flash');

    $summary = findSummary($this->topicId);

    expect($summary)->not->toBeNull();
    expect($summary['topic_id'])->toBe($this->topicId);
    expect($summary['title'])->toBe('테스트 제목');
    expect($summary['summary'])->toBe('테스트 요약');
    expect($summary['model'])->toBe('gemini-2.5-flash');
});

test('saveSummary upserts on a second call with the same topic id', function () {
    saveSummary($this->topicId, 'https://news.hada.io/topic?id=999000002', '첫 제목', '첫 요약', 'gemini-2.5-flash');
    saveSummary($this->topicId, 'https://news.hada.io/topic?id=999000002', '수정된 제목', '수정된 요약', 'gemini-2.5-flash');

    $summary = findSummary($this->topicId);

    expect($summary['title'])->toBe('수정된 제목');
    expect($summary['summary'])->toBe('수정된 요약');
});

test('deleteSummary removes the summary', function () {
    saveSummary($this->topicId, 'https://news.hada.io/topic?id=999000002', '제목', '요약', 'gemini-2.5-flash');

    deleteSummary($this->topicId);

    expect(findSummary($this->topicId))->toBeNull();
});

test('listSummary includes a saved summary ordered by most recently updated', function () {
    saveSummary($this->topicId, 'https://news.hada.io/topic?id=999000002', '제목', '요약', 'gemini-2.5-flash');

    $list = listSummary();

    expect($list[0]['topic_id'])->toBe($this->topicId);
});
