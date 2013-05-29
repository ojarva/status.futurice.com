<?php
/*
 * This file provides server-sent events interface for faster reloads when data changes
 * W3 EventSource draft: http://www.w3.org/TR/eventsource/
 * html5rocks.com tutorial: http://www.html5rocks.com/en/tutorials/eventsource/basics/
 * caniuse.com browser compatibility: http://caniuse.com/#feat=eventsource
 */

ini_set("default_socket_timeout", -1);
set_time_limit(0);
require_once("lib/redis.php");
require_once("lib/userstats.php");


// Don't cache
header('Cache-Control: no-cache, no-store, max-age=0, must-revalidate');
header('Expires: Mon, 26 Jul 1997 05:00:00 GMT');
header('Pragma: no-cache');

Header("Content-Type: text/event-stream");

// Send headers to browser immediately
flush();
ob_flush();

if (isset($_GET["file"])) {
    $filename = "data:".basename($_GET["file"]);
} else {
    echo "Event: error\n";
    echo "data: no filename set\n";
    $redis->incr("stats:web:invalid");
    $redis->incr("stats:web:sse:invalid");
    stat_update("web:invalid");
    stat_update("web:sse:invalid");
    flush();
    exit();
}
if ($redis->get($filename) === FALSE) {
    echo "Event: error\n";
    echo "data: invalid filename\n";
    $redis->incr("stats:web:invalid");
    $redis->incr("stats:web:sse:invalid");
    stat_update("web:invalid");
    stat_update("web:sse:invalid");
    flush();
    exit();
}

$redis->incr("stats:web:sse:started");
stat_update("web:sse:started");

//array("filename" => "data:twitter.json", "event" => "changeevent", "redis" => true),
$follow_files = array(
                      array("filename" => "cache.manifest", "event" => "manifestchange", "redis" => false),
                      array("filename" => $filename, "event" => "changeevent", "redis" => true));

// Get initial data and send single round of updates immediately.
foreach ($follow_files as $k => $v) {
    if ($v["redis"]) {
        $follow_files[$k]["mtime"] = $redis->get($v["filename"]."-mtime");
        $follow_files[$k]["hash"] = $redis->get($v["filename"]."-hash");
    } else {
        $follow_files[$k]["mtime"] = filemtime($v["filename"]);
        $follow_files[$k]["hash"] = sha1_file($v["filename"]);
    }
    send_event($redis, $v["event"], $follow_files[$k]["mtime"], 0, $v["filename"]);
}

// send single event
function send_event($redis, $event, $new_mtime, $old_mtime, $filename) {
    $redis->incr("stats:web:sse:event_sent");
    stat_update("web:sse:event_sent");
    echo "event: ".$event."\n";
    echo "data: {\"timestamp\": $new_mtime, \"old_timestamp\": ".$old_mtime.", \"filename\": \"".$filename."\"}\n\n";
    ob_flush();
    flush();
}

// Handle single pubsub message
function process_pubsub($redis, $chan, $msg) {
    global $follow_files;
    stat_update("web:sse:pubsub_received");
    $redis->incr("stats:web:sse:pubsub_received");
    $msg_decode = json_decode($msg, true);
    foreach ($follow_files as $k => $v) {
        if ($chan == "pubsub:".$v["filename"]) {
            $new_hash = $msg_decode["hash"];
            if ($new_hash != $v["hash"]) {
                $new_mtime = $msg_decode["mtime"];
                send_event($redis, $v["event"], $new_mtime, $v["mtime"], $v["filename"]);
                $follow_files[$k]["hash"] = $new_hash;
                $follow_files[$k]["mtime"] = $new_mtime;
            }
            break;
        }
    }
}

// Predis allows only pubsub in single connection -> get separate connection for listening.
// Another one is required for updating statistics etc.
$pubredis = getRedis();
$pubsub = $pubredis->pubSub();
//$pubsub->subscribe("pubsub:data:twitter.json", "pubsub:cache.manifest", "pubsub:".$filename);
$pubsub->subscribe("pubsub:cache.manifest", "pubsub:".$filename);

$counter = 1800;
while ($counter > 0) {
  foreach ($pubsub as $message) {
    switch($message->kind) {
        case 'subscribe':
            break;
        case 'message':
            process_pubsub($redis, $message->channel, $message->payload);
            break;
    }

    $counter--;
    if ($counter == 0) {
        error_log("pubsub unsubscribe");
        $pubsub->unsubscribe();
    }
  }
}
unset($pubsub);
?>
