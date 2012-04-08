<?
$redis = new Redis();
$redis->connect("localhost");
require_once("lib/userstats.php");

if (!isset($_GET["filename"])) {
    $redis->incr("stats:web:static:invalid");
    $redis->incr("stats:web:invalid");
    stat_update("web:static:invalid");
    stat_update("web:invalid");

    header("HTTP/1.1 500 Internal Server Error");
    exit();
}
$filename = $_GET["filename"];
$pathinfo = pathinfo($filename);
$dir = $pathinfo["dirname"];
if (!in_array($dir, array("css", "js", "img")) || !file_exists($filename)) {
    $redis->incr("stats:web:static:invalid");
    $redis->incr("stats:web:invalid");
    stat_update("web:static:invalid");
    stat_update("web:invalid");
    header("HTTP/1.1 500 Internal Server Error");
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

#http_cache_last_modified();
http_cache_etag();
http_send_content_type($ct);
http_send_file($filename);
?>
