<?php

require_once __DIR__ . '/../../article_repo.php';

beforeEach(function () {
    $this->topicId = 999000001;
    saveArticle(
        $this->topicId,
        'Pest 테스트용 기사 제목',
        '이것은 Pest 테스트를 위해 삽입된 임시 기사 본문입니다. 검색전용키워드프레스토파랑고양이가 포함되어 있습니다.'
    );
});

afterEach(function () {
    getDb()->prepare('DELETE FROM articles WHERE topic_id = ?')->execute([$this->topicId]);
});

test('searchArticles finds an article whose content matches the query', function () {
    $results = searchArticles('검색전용키워드프레스토파랑고양이');

    $topicIds = array_column($results, 'topic_id');

    expect($results)->not->toBeEmpty();
    expect($topicIds)->toContain($this->topicId);
});
