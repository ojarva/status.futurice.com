<?php
require_once("../lib/redis.php");
require_once 'conf/common.inc.php';
require_once 'inc/functions.inc.php';
require_once 'inc/html.inc.php';
require_once 'inc/collectd.inc.php';

# use width/height from config if nothing is given
if (empty($_GET['x']))
	$_GET['x'] = $CONFIG['detail-width'];
if (empty($_GET['y']))
	$_GET['y'] = $CONFIG['detail-heigth'];

$host = validate_get(GET('h'), 'host');
$plugin = validate_get(GET('p'), 'plugin');
$pinstance = validate_get(GET('pi'), 'pinstance');
$type = validate_get(GET('t'), 'type');
$tinstance = validate_get(GET('ti'), 'tinstance');
$width = GET('x');
$heigth = GET('y');
$seconds = GET('s');

$requesthash = sha1(serialize($_GET));
$rediskey = "cache:grapher:detail:$host:$plugin:$type:$tinstance:$seconds";

$content = $redis->get($rediskey);
if ($content) {
    http_cache_etag();
    http_send_data($content);
    exit();
}


ob_start();

html_start();

if (isset($_GET["tz"])) {
	$tz = $_GET["tz"];
} else {
	$tz = "EEST";
}

printf('<h2><a href="%s">%s</a></h2>'."\n",
	$CONFIG['weburl'].'host?h='.htmlentities($host).'&tz='.$tz, $host
);

$term = array(
	'2 hours'	=> 3600*2,
	'8 hours'	=> 3600*8,
	'day'	=> 86400,
	'week'	=> 86400*7,
	'month'	=> 86400*31,
	'quarter'=> 86400*31*3,
	'year'	=> 86400*365,
);

$args = $_GET;
print "<ul>\n";
foreach($term as $key => $s) {
	$args['s'] = $s;
	printf('<li><a href="%s%s">%s</a></li>'."\n",
		$CONFIG['weburl'], build_url('detail', $args), $key);
}
print "</ul>\n";

$plugins = collectd_plugins($host);

if(!$plugins) {
	echo "Unknown host\n";
	return false;
}

# show graph
printf('<img src="%s%s">'."\n", $CONFIG['weburl'], build_url('graph', $_GET));

html_end();

$content = ob_get_clean();
http_cache_etag();
http_send_data($content);
$redis->setex($rediskey, 300, $content);
?>
