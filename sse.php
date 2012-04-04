<?
/*
 * This file provides server-sent events interface for faster reloads when data changes
 * W3 EventSource draft: http://www.w3.org/TR/eventsource/
 * html5rocks.com tutorial: http://www.html5rocks.com/en/tutorials/eventsource/basics/
 * caniuse.com browser compatibility: http://caniuse.com/#feat=eventsource
 */

set_time_limit(0);

Header("Content-Type: text/event-stream");
flush();
if (isset($_GET["file"])) {
    $filename = "data/".basename($_GET["file"]);
}

if (!(isset($filename) && file_exists($filename))) {
    echo "Event: error\n";
    echo "data: invalid filename $filename\n";
    flush();
    exit();
}

$follow_files = array(array("filename" => "data/twitter.json", "event" => "changeevent"),
                      array("filename" => "cache.manifest", "event" => "manifestchange"),
                      array("filename" => $filename, "event" => "changeevent"));

foreach ($follow_files as $k => $v) {
    $follow_files[$k]["mtime"] = filemtime($v["filename"]);
    $follow_files[$k]["hash"] = sha1_file($v["filename"]);
}

while (true) {
    clearstatcache();
    foreach ($follow_files as $k => $v) {
        $new_mtime = filemtime($v["filename"]);
        if ($new_mtime != $v["mtime"]) {
            $hash = sha1_file($v["filename"]);
            if ($hash != $v["hash"]) {
                echo "event: ".$v["event"]."\n";
                echo "data: {'timestamp': $new_mtime, 'old_timestamp': ".$v["mtime"].", 'filename': ".$v["filename"]."}\n\n";
                ob_flush();
                flush();
                $follow_files[$k]["hash"] = $hash;
            }
            $follow_files[$k]["mtime"] = $new_mtime;
        }
    }
    usleep(1000000);
}
?>
