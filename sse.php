<?
/*
 * This file provides server-sent events interface for faster reloads when data changes
 * W3 EventSource draft: http://www.w3.org/TR/eventsource/
 * html5rocks.com tutorial: http://www.html5rocks.com/en/tutorials/eventsource/basics/
 * caniuse.com browser compatibility: http://caniuse.com/#feat=eventsource
 */

set_time_limit(0);
$redis = new Redis();
$redis->connect("localhost");

Header("Content-Type: text/event-stream");
flush();
if (isset($_GET["file"])) {
    $filename = "data:".basename($_GET["file"]);
}

if (!isset($filename)) {
    echo "Event: error\n";
    echo "data: no filename set\n";
    $redis->close();
    flush();
    exit();
}
if ($redis->get($filename) === FALSE) {
    echo "Event: error\n";
    echo "data: invalid filename\n";
    $redis->close();
    flush();
    exit();
}

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

$counter = 1800;
while ($counter > 0) {
    clearstatcache();
    foreach ($follow_files as $k => $v) {
        if ($v["redis"]) {
            $new_hash = $redis->get($v["filename"]."-hash");
            if ($new_hash != $v["hash"]) {
                $new_mtime = $redis->get($v["filename"]."-mtime");
                echo "event: ".$v["event"]."\n";
                echo "data: {'timestamp': $new_mtime, 'old_timestamp': ".$v["mtime"].", 'filename': ".$v["filename"]."}\n\n";
                $counter = $counter - 3;
                ob_flush();
                flush();
                $follow_files[$k]["hash"] = $new_hash;
                $follow_files[$k]["mtime"] = $new_mtime;
            }
        } else {
            $new_mtime = filemtime($v["filename"]);
            if ($new_mtime != $v["mtime"]) {
                $hash = sha1_file($v["filename"]);
                if ($hash != $v["hash"]) {
                    echo "event: ".$v["event"]."\n";
                    echo "data: {'timestamp': $new_mtime, 'old_timestamp': ".$v["mtime"].", 'filename': ".$v["filename"]."}\n\n";
                    ob_flush();
                    flush();
                    $follow_files[$k]["hash"] = $hash;
                    if ($v["event"] == "manifestchange") {
                        $counter = 5;
                    }
                }
                $follow_files[$k]["mtime"] = $new_mtime;
            }
        }
    }
    usleep(1000000);
    $counter--;
}
$redis->close();
?>
