<?php

require_once("../lib/redis.php");
require_once 'conf/common.inc.php';
require_once 'inc/html.inc.php';
require_once 'inc/collectd.inc.php';

$host = validate_get(GET('h'), 'host');
$splugin = validate_get(GET('p'), 'plugin');

$content = ($redis->get("cache:grapher:host:$host:$splugin"));
if ($content) {
  http_cache_etag();
  http_send_data($content);
  exit(0);
}

ob_start();

html_start();

printf('<h2>%s</h2>'."\n", $host);

$plugins = unserialize($redis->get("cache:grapher:collectd_plugins:$host"));
if (!$plugins) {
    $plugins = collectd_plugins($host);
    $redis->setex("cache:grapher:collectd_plugins:$host", 300, serialize($plugins));
}

if(!$plugins) {
	echo "Unknown host\n";
	return false;
}

# first the ones defined in overview
foreach($CONFIG['overview'] as $plugin) {
	if (in_array($plugin, $plugins)) {
		printf('<div id="%s">'."\n", $plugin);
		plugin_header($host, $plugin, 0);
		graphs_from_plugin($host, $plugin);
		print "</div>\n";
	}
}

# other plugins
foreach($plugins as $plugin) {
	if (!in_array($plugin, $CONFIG['overview'])) {
		printf('<div id="%s">'."\n", $plugin);
		if ($splugin == $plugin) {
			plugin_header($host, $plugin, 0);
			graphs_from_plugin($host, $plugin);
		} else {
			plugin_header($host, $plugin, 1);
		}
		print "</div>\n";
	}
}

html_end();

$content = ob_get_clean();
$redis->setex("cache:grapher:host:$host:$splugin", 300, $content);
http_cache_etag();
http_send_data($content);
?>
