<?php

require_once __DIR__ . '/../../chat_repo.php';

afterEach(function () {
    if (isset($this->sessionId)) {
        getDb()->prepare('DELETE FROM chat_session WHERE id = ?')->execute([$this->sessionId]);
    }
});

test('createSession creates a session and sessionExists finds it', function () {
    $this->sessionId = createSession();

    expect($this->sessionId)->toBeGreaterThan(0);
    expect(sessionExists($this->sessionId))->toBeTrue();
});

test('sessionExists returns false for an unknown session id', function () {
    expect(sessionExists(999999999))->toBeFalse();
});

test('addMessage stores a message and getRecentMessages returns it in chronological order', function () {
    $this->sessionId = createSession();

    addMessage($this->sessionId, 'user', '첫 번째 질문');
    addMessage($this->sessionId, 'model', '첫 번째 답변');
    addMessage($this->sessionId, 'user', '두 번째 질문');

    $messages = getRecentMessages($this->sessionId);

    expect($messages)->toHaveCount(3);
    expect($messages[0])->toBe(['role' => 'user', 'content' => '첫 번째 질문']);
    expect($messages[1])->toBe(['role' => 'model', 'content' => '첫 번째 답변']);
    expect($messages[2])->toBe(['role' => 'user', 'content' => '두 번째 질문']);
});

test('getRecentMessages respects the limit while keeping chronological order', function () {
    $this->sessionId = createSession();

    for ($i = 1; $i <= 5; $i++) {
        addMessage($this->sessionId, 'user', "메시지 {$i}");
    }

    $messages = getRecentMessages($this->sessionId, 2);

    expect($messages)->toHaveCount(2);
    expect($messages[0]['content'])->toBe('메시지 4');
    expect($messages[1]['content'])->toBe('메시지 5');
});
