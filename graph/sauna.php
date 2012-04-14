<?
require_once("../lib/redis.php");
$filename = "../upload/sauna.rrd";
http_send_content_type("image/png");
$width = 500;
$height = 300;
$range = 6;
if (isset($_GET["width"])) {
   $width = min(2000, max(100, intval($_GET["width"])));
}
if (isset($_GET["height"])) {
   $height = min(2000, max(100, intval($_GET["height"])));
}
if (isset($_GET["range"])) {
   $range = min(192, max(1, intval($_GET["range"])));
}
http_cache_etag();
$cachekey = "cache:sauna.png:$width:$height:$range";
$data = $redis->get($cachekey);
if ($data) {
 http_send_data($data);
} else {
 ob_start();
 system('rrdtool graph - --end now --start end-'.$range.'h -r --font TITLE:16:Helvetica --font WATERMARK:3:Helvetica --font AXIS:9:Helvetica --font UNIT:10:Helvetica -c "GRID#FFFFFF" -c "MGRID#FFFFFF" -c "ARROW#000000" -c "SHADEA#FFFFFF" -c "SHADEB#FFFFFF" -c "FRAME#FFFFFF" -c "BACK#FFFFFF" --full-size-mode --width '.$width.' --height '.$height.' "DEF:temperature='.$filename.':temperature:AVERAGE" "LINE1:temperature#00C000"');
 $data = ob_get_contents();
 ob_end_clean();
 $redis->setex($cachekey, 60, $data);
 http_send_data($data);
}
?>
