<?php
require 'Predis/Autoloader.php';

Predis\Autoloader::register();

function getRedis() {
    return new Predis\Client();
}

if (!isset($redis)) {
    $redis = getRedis();
}

?>
