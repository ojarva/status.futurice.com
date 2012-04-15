<?php
require 'Predis/Autoloader.php';

Predis\Autoloader::register();

function getRedis() {
    return new Predis\Client("unix:///home/redis/redis.sock");
}

if (!isset($redis)) {
    $redis = getRedis();
}

?>
