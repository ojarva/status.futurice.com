<?php
// width+height+range = 1900*1900*8999 = 3245390000 cache keys
// 3245390000 * 200kB = 604TB - saturates redis storage.
// However, redis should be configured with maxmemory directive and
// volatile-lru, which evicts least recently used key that's
// going to to expire anyway.

require_once("../lib/redis.php");
$filename = "../upload/sauna.rrd";
http_send_content_type("image/png");
$width = 500;
$height = 300;
$range = 6;
$mode = "normal";
$modes = array(
               "raw" => '"LINE1:temperature#C00000" ',
               "derivate" => '"CDEF:prev1=PREV(temperature)" '.
                           '"CDEF:time=temperature,POP,TIME" '.
                           '"CDEF:prevtime=PREV(time)" '.
                           '"CDEF:derivate=temperature,prev1,-,time,prevtime,-,/" '.
                           '"CDEF:smoothed=derivate,1800,TREND" '.
                           '"LINE1:smoothed#000077" ',
              "normal" => '"CDEF:trendtemp=temperature,900,TREND" '.
                          '"CDEF:trend=trendtemp,20,110,LIMIT" '.
                          '"CDEF:linehot=trend,64,110,LIMIT" '.
                          '"CDEF:linewarm=trend,39,65,LIMIT" '.
                          '"CDEF:linecold=trend,0,40,LIMIT" '.
                          '"CDEF:comp1=PREV(trend)" '.
                          '"CDEF:comp2=PREV(comp1)" '.
                          '"CDEF:comp3=PREV(comp2)" '.
                          '"CDEF:slope=comp3,trend,LT" '. // going up = 1
                          '"CDEF:down=slope,UNKN,trend,IF,40,110,LIMIT" '.
                          '"CDEF:up=slope,trend,UNKN,IF,40,110,LIMIT" '.
                          '"AREA:up#7700001D" '.
                          '"AREA:down#0000771D" '.
                          '"LINE1:linehot#7700008F" '.
                          '"LINE1:linewarm#0077008F" '.
                          '"LINE1:linecold#0000778F" '

);

$modestring = $modes[$mode];

if (isset($_GET["width"])) {
    $width = min(2000, max(100, intval($_GET["width"])));
}
if (isset($_GET["height"])) {
    $height = min(2000, max(100, intval($_GET["height"])));
}
if (isset($_GET["range"])) {
    $range = min(9000, max(1, intval($_GET["range"])));
}
$tz = "EEST";
if (isset($_GET["tz"])) {
    $tz = substr($_GET["tz"], 0, 4);
}
$tz = timezone_name_from_abbr($tz);
if ($tz === FALSE) {
    $tz = "Europe/Helsinki";
}

if (isset($_GET["mode"])) {
    $mode = $_GET["mode"];
    if (!isset($modes[$mode])) {
        $mode = "normal";
    }
    $modestring = $modes[$mode];
}

http_cache_etag();
$cachekey = "cache:sauna.png:$width:$height:$range:$mode:$tz";
$data = $redis->get($cachekey);

if ($data) {
    http_send_data($data);
} else {
    ob_start();
    passthru('TZ='.$tz.' rrdtool graph - --end now --start end-'.$range.'h --slope-mode -u 100 -l 0 '.
       '--font TITLE:16:Helvetica --font WATERMARK:3:Helvetica --font AXIS:9:Helvetica --font UNIT:10:Helvetica '.
       '-c "GRID#FFFFFF" -c "MGRID#FFFFFF" -c "ARROW#000000" -c "SHADEA#FFFFFF" -c "SHADEB#FFFFFF" -c "FRAME#FFFFFF" -c "BACK#FFFFFF" '.
       '--full-size-mode --width '.$width.' --height '.$height.' '.
       '"DEF:temperatureraw='.$filename.':temperature:AVERAGE" '.
       '"CDEF:temperature=temperatureraw,24,110,LIMIT" '.
       $modestring);
    $data = ob_get_clean();
    $redis->setex($cachekey, 60, $data);
    http_send_data($data);
}
?>
