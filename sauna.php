<?
// This file handles data from sauna.

// Do not cache
header('Cache-Control: no-cache, no-store, max-age=0, must-revalidate');
header('Expires: Mon, 26 Jul 1997 05:00:00 GMT');
header('Pragma: no-cache');
header("content-type: application/json");

// Sample file is named as upload_settings.php.sample. Move it, and change password to something more complex.
require_once("upload_settings.php");
require_once("lib/redis.php");

function response($success, $status) {
    return json_encode(array("success" => $success, "status" => $status));
    exit(0);
}

if ($_POST["password"] != $password) {

    // Update statistics
    $redis->incr("stats:web:invalid");
    $redis->incr("stats:web:sauna:pwfail");
    Header('HTTP/1.1 403 Forbidden');
    echo response(false, "Wrong password");
}

$expiration_time = 3600 * 24 * 30; // One month

// If file doesn't exist, create it.
if (!file_exists("upload/sauna.rrd")) {
    exec("rrdtool create upload/sauna.rrd --start N --step 60 DS:temperature:GAUGE:240:10:110 ".
          " RRA:AVERAGE:0.5:1:1440 RRA:AVERAGE:0.5:5:4032 RRA:AVERAGE:0.5:10:8640 RRA:AVERAGE:0.5:30:35040".
          " RRA:MAX:0.5:1:1440 RRA:MAX:0.5:5:4032 RRA:MAX:0.5:10:8640 RRA:MAX:0.5:30:35040".
          " RRA:MIN:0.5:1:1440 RRA:MIN:0.5:5:4032 RRA:MIN:0.5:10:8640 RRA:MIN:0.5:30:35040".
          " RRA:LAST:0.5:1:1440 RRA:LAST:0.5:5:4032 RRA:LAST:0.5:10:8640 RRA:LAST:0.5:30:35040".
          " RRA:HWPREDICT:20160:0.5:0.5:1440");
}

// Sanitize input value - temperature is directly used in exec().
$data = floatval($_GET["temperature"]);

if ($data < 25 || $data > 110) {
    // Update statistics
    $redis->incr("stats:web:invalid");
    $redis->incr("stats:web:sauna:invalidvalue");

    echo response(false, "Invalid value");
}

exec("rrdtool update upload/sauna.rrd N:$data");

// Push new value to temperatures list (left)
$redis->lpush("cache:latest_sauna", $data);
$redis->ltrim("cache:latest_sauna", 0, 49);

// Update expire for list - it's always one month from last update.
$redis->expire("cache:latest_sauna", 3600*24*30);
echo response(true, "Success");
?>
