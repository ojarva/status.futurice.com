<?
/*
 * This file provides server-sent events interface for faster reloads when data changes
 * W3 EventSource draft: http://www.w3.org/TR/eventsource/
 * html5rocks.com tutorial: http://www.html5rocks.com/en/tutorials/eventsource/basics/
 * caniuse.com browser compatibility: http://caniuse.com/#feat=eventsource
 */

set_time_limit(0);
$redis = new Redis();
$redis->connect('127.0.0.1', 6379, 0);

Header("Content-Type: text/event-stream");
flush();
if (isset($_GET["file"])) {
    $filename = "data:".basename($_GET["file"]);
} else {
    echo "Event: error\n";
    echo "data: no filename set\n";
    $redis->incr("stats:web:invalid");
    $redis->incr("stats:web:sse:invalid");
    $redis->close();
    flush();
    exit();
}
if ($redis->get($filename) === FALSE) {
    echo "Event: error\n";
    echo "data: invalid filename\n";
    $redis->incr("stats:web:sse:invalid");
    $redis->close();
    flush();
    exit();
}

$redis->incr("stats:web:sse:started");

$follow_files = array(array("filename" => "data:twitter.json", "event" => "changeevent", "redis" => true),
                      array("filename" => "cache.manifest", "event" => "manifestchange", "redis" => false),
                      array("filename" => $filename, "event" => "changeevent", "redis" => true));

foreach ($follow_files as $k => $v) {
    if ($v["redis"]) {
        $follow_files[$k]["mtime"] = $redis->get($v["filename"]."-mtime");
        $follow_files[$k]["hash"] = $redis->get($v["filename"]."-hash");
    } else {
        $follow_files[$k]["mtime"] = filemtime($v["filename"]);
        $follow_files[$k]["hash"] = sha1_file($v["filename"]);
    }
}


function listen_pubsub($redis, $chan, $msg) {
    global $follow_files;
    $redis->incr("stats:web:sse:pubsub_received");
    $msg_decode = json_decode($msg, true);
    foreach ($follow_files as $k => $v) {
        if ($chan == "pubsub:".$v["filename"]) {
            $new_hash = $msg_decode["hash"];
            if ($new_hash != $v["hash"]) {
                $redis->incr("stats:web:sse:event_sent");
                $new_mtime = $msg_decode["mtime"];
                echo "event: ".$v["event"]."\n";
                echo "data: {\"timestamp\": $new_mtime, \"old_timestamp\": ".$v["mtime"].", \"filename\": \"".$v["filename"]."\"}\n\n";
                ob_flush();
                flush();
                $follow_files[$k]["hash"] = $new_hash;
                $follow_files[$k]["mtime"] = $new_mtime;
            }
            break;
        }
    }
}

$redis_subscribe = array();
foreach ($follow_files as $k => $v) {
    $redis_subscribe[] = "pubsub:".$v["filename"];
}

$redis->subscribe($redis_subscribe, 'listen_pubsub');

$counter = 1800;
while ($counter > 0) {
    $redis->incr("stats:web:sse:loop");
    if ($counter % 60 == 0) {
        echo "event: nop\ndata: nop\n\n";
        ob_flush();
        flush();
    }
    $counter--;
    sleep(1);
}
$redis->close();
?>
