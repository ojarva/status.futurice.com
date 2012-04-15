<?php

require_once("../lib/redis.php");
require_once 'conf/common.inc.php';
require_once 'inc/functions.inc.php';

$get_cleaned = array();
$valid_params = array("p", "pi", "t", "h", "s", "x", "y");
foreach ($valid_params as $v) {
   $get_cleaned[$v] = $_GET[$v];
}

$plugin = validate_get(GET('p'), 'plugin');
$width = empty($_GET['x']) ? $CONFIG['width'] : $_GET['x'];
$heigth = empty($_GET['y']) ? $CONFIG['heigth'] : $_GET['y'];


$requesthash = sha1(serialize($get_cleaned));
$rediskey = "cache:grapher:graph:$plugin:${width}x${heigth}:$requesthash";
$cached = $redis->get($rediskey);
if ($cached) {
   Header("Content-Type: image/png");
   echo $cached;
   exit();
}

if (validate_get(GET('h'), 'host') === NULL) {
	error_log('CGP Error: plugin contains unknown characters');
	error_image();
}

if (!file_exists($CONFIG['webdir'].'/plugin/'.$plugin.'.php')) {
	error_log(sprintf('CGP Error: plugin "%s" is not available', $plugin));
	error_image();
}

ob_start();

# load plugin
include $CONFIG['webdir'].'/plugin/'.$plugin.'.php';

$content = ob_get_clean();
$redis->setex($rediskey, 60, $content);
echo $content;

?>
