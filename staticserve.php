<?
// This file serves static files and handles updating statistics.
// Static files are cached using html5 application cache (whenever it's supported).
// Many browsers don't update application cache correctly, if http cache headers
// are set.

require_once("lib/redis.php");
require_once("lib/userstats.php");

if (!isset($_GET["filename"])) {
    // No filename set

    // Update statistics
    $redis->incr("stats:web:static:invalid");
    $redis->incr("stats:web:invalid");
    stat_update("web:static:invalid");
    stat_update("web:invalid");

    header("HTTP/1.1 404 Not Found");
    exit();
}

$filename = $_GET["filename"];
$pathinfo = pathinfo($filename);
$dir = $pathinfo["dirname"];

if (!in_array($dir, array("css", "js", "img")) || !file_exists($filename)) {
    error_log("staticserve.php: Invalid directory or file ($filename) doesn't exist");
    $redis->incr("stats:web:static:invalid");
    $redis->incr("stats:web:invalid");
    stat_update("web:static:invalid");
    stat_update("web:invalid");
    header("HTTP/1.1 404 Not Found");
    exit();
}

if ($dir == "css") { $ct = "text/css"; }
elseif ($dir == "js") { $ct = "application/javascript"; }
elseif ($dir == "img") {
    $finfo = finfo_open(FILEINFO_MIME_TYPE);
    $ct = finfo_file($finfo, $filename);
} else {
    $ct = "text/plain";
}

$redis->incr("stats:web:static:served");
stat_update("web:static:served");

http_cache_etag();
http_send_content_type($ct);
http_send_file($filename);
?>
