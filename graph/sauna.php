<?
require_once("../lib/redis.php");
$filename = "../upload/sauna.rrd";
http_send_content_type("image/png");
$data = $redis->get("cache:sauna.png");
http_cache_etag();
if ($data) {
 http_send_data($data);
} else {
 ob_start();
 system('rrdtool graph - --end now --start end-6h -m 1.5 -r --font TITLE:13:Helvetica --font WATERMARK:3:Helvetica --font AXIS:7:Helvetica --font UNIT:8:Helvetica -v "Temperature" -c "GRID#FFFFFF" -c "MGRID#FFFFFF" -c "ARROW#000000" -c "SHADEA#FFFFFF" -c "SHADEB#FFFFFF" -c "FRAME#FFFFFF" -c "BACK#FFFFFF" -t "Sauna" --width 400 --height 200 "DEF:temperature='.$filename.':temperature:AVERAGE" "LINE1:temperature#00C000"');
 $data = ob_get_contents();
 ob_end_clean();
 $redis->setex("cache:sauna.png", 60, $data);
 http_send_data($data);
}
?>
