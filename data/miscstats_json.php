<?
$redis = new Redis();
$redis->connect("localhost");
$autofill = array();
$keys = array();
$uptime = trim(file_get_contents("/proc/uptime"));
$uptime = explode(" ", $uptime);
$uptime = intval($uptime[0]);

$redis->set("stats:server:uptime", $uptime);

if ($uptime > 86400) {
  $uptime = round($uptime / 86400, 1) . " days";
} elseif ($uptime > 3600) {
  $uptime = round($uptime / 3600, 1) . " hours";
} else {
   $uptime = round($uptime / 60)." minutes";
}
$redis->set("stats:server:uptime:readable", $uptime);

$redis_info = array();
$redis_final = array();
exec("redis-cli info", $redis_info);
foreach ($redis_info as $k => $v) {
  $v = explode(":", $v);
  if (is_numeric($v[1])) {
     $v[1] = floatval($v[1]);
  }
  $redis_final["stats:redis:".$v[0]] = $v[1];
}
$dbstats = $redis_final["stats:redis:db0"];
$dbstats = explode(",", $dbstats);
foreach ($dbstats as $k => $v) {
    $v = explode("=", $v);
    $redis_final["stats:redis:db0:".$v[0]] = intval($v[1]);
}

$redis->mset($redis_final);

$loadavg = trim(file_get_contents("/proc/loadavg"));
$loadavg = explode(" ", $loadavg);
$redis->mset(array("stats:server:load:1m" => $loadavg[0], "stats:server:load:5m" => $loadavg[1], "stats:server:load:15m" => $loadavg[2]));

$traffic = trim(exec("/sbin/ifconfig eth0 | grep 'RX bytes'"));
// RX bytes:1218147977 (1.2 GB)  TX bytes:952382226 (952.3 MB)
$traffic = explode("  ", $traffic);
$sum = 0;
foreach ($traffic as $k => $v) {
   $v = explode(":", $v);
   $v = explode(" ", $v[1]);
   $sum += intval($v[0]);
}

if ($sum < 1024) {
   $sumreadable = $sum."B";
} elseif ($sum < 1024*1024) {
   $sumreadable = round($sum/1024)."kB";
} elseif ($sum < 1024*1024*1024) {
   $sumreadable = round($sum/1024/1024, 1)."MB";
} elseif ($sum < 1024*1024*1024*1024) {
   $sumreadable = round($sum/1024/1024/1024, 2)."GB";
} elseif ($sum < 1024*1024*1024*1024*1024) {
   $sumreadable = round($sum/1024/1024/1024/1024, 3)."TB";
}
$redis->mset(array("stats:server:net:eth0:total" => $sum, "stats:server:net:eth0:total:readable" => $sumreadable));

exec("redis-cli keys 'stats:*'", $keys);
$autofill = array();
$values = $redis->mget($keys);
foreach ($keys as $k => $v) {
   $autofill[str_replace(":", "_", $v)] = $values[$k];
}


$content = json_encode(array("autofill" => $autofill));
$hash = sha1($content);
$exptime = 3600 * 24 * 30;

$redis->setex("data:miscstats.json", $exptime, $content);
$redis->setex("data:miscstats.json-mtime", $exptime, time());
$redis->setex("data:miscstats.json-hash", $exptime, $hash);

foreach ($autofill as $k => $v) {
    if (!is_numeric($v)) { continue; }
    $v = round(floatval($v) * 100);
    $filename = "miscstats_graphs/$k.rrd";
    if (!file_exists($filename)) {
        exec("rrdtool create $filename --step 60 -- DS:valueg:GAUGE:300:U:U DS:valuec:COUNTER:300:U:U RRA:AVERAGE:0.5:1:120 RRA:AVERAGE:0.5:5:8640 RRA:AVERAGE:0.5:60:12760 RRA:MAX:0.5:5:8640 RRA:MAX:0.5:60:12760 RRA:MIN:0.5:5:8640 RRA:MIN:0.5:60:12760");
    }
    exec("rrdtool update $filename N:$v:$v");
}

?>
