<?php

afterEach(function () {
    foreach (['PEST_ENV_TEST_A', 'PEST_ENV_TEST_B', 'PEST_ENV_TEST_C'] as $key) {
        unset($_ENV[$key]);
        putenv($key);
    }
});

test('env() returns the value from $_ENV when set', function () {
    $_ENV['PEST_ENV_TEST_A'] = 'from-env-array';

    expect(env('PEST_ENV_TEST_A'))->toBe('from-env-array');
});

test('env() falls back to getenv() when $_ENV is not set', function () {
    putenv('PEST_ENV_TEST_B=from-getenv');

    expect(env('PEST_ENV_TEST_B'))->toBe('from-getenv');
});

test('$_ENV takes priority over getenv()', function () {
    $_ENV['PEST_ENV_TEST_C'] = 'from-env-array';
    putenv('PEST_ENV_TEST_C=from-getenv');

    expect(env('PEST_ENV_TEST_C'))->toBe('from-env-array');
});

test('env() returns the given default when the key is missing everywhere', function () {
    expect(env('PEST_ENV_TEST_MISSING', 'fallback'))->toBe('fallback');
});

test('env() returns null when the key is missing and no default is given', function () {
    expect(env('PEST_ENV_TEST_MISSING_NULL'))->toBeNull();
});
