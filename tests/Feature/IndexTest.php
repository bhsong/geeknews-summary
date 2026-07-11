<?php

test('index.php prints the hello message', function () {
    ob_start();
    include __DIR__ . '/../../index.php';
    $output = ob_get_clean();

    expect($output)->toBe("Hello, PHP!\n");
});
