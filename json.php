<?
Header("Content-Type: application/json");

require_once("lib/redis.php");
require_once("lib/userstats.php");

// Basic data structure - this is always returned.
$ret = array("message_timestamp" => time(),
             "status" => false,
             "status_message" => false,
             "data" => array("file_timestamp" => false,
                             "content_timestamp" => false,
                             "content" => false),
             "twitter" => array("file_timestamp" => false,
                                "content_timestamp" => false,
                                "content" => false)
);

if (isset($_GET["filename"])) {
    $filename = "data:".basename($_GET["filename"]);
} else {
    // No filename provided -> abort

    // Update statistics
    $redis->incr("stats:web:invalid");
    $redis->incr("stats:web:json:invalid");
    stat_update("web:invalid");

    // Set error message
    $ret["status"] = "error";
    $ret["status_message"] = "Invalid request";
    echo json_encode($ret);
    exit();
}

// Try to get data from redis.
$data = $redis->get($filename);

if ($data === FALSE) {
    // No data available -> abort

    // Update statistics
    $redis->incr("stats:web:invalid");
    $redis->incr("stats:web:json:invalid");
    stat_update("web:invalid");

    // Set error message
    $ret["status"] = "error";
    $ret["status_message"] = "Invalid filename";
    echo json_encode($ret);
    exit();
}

// If last_data is set, don't return older than that.
if (isset($_GET["last_data"])) {
   $last_data = intval($_GET["last_data"]);
} else {
   $last_data = 0;
}

function process_json($filename, $last_data) {
    // Return data array or false if not available.
    global $redis;
    $timestamp = $redis->get($filename."-mtime");
    if ($timestamp === FALSE) {
        $timestamp = 0;
    }
    $ret = array("file_timestamp" => $timestamp, "content_timestamp" => false, "content" => false);
    $ret["content"] = json_decode($redis->get($filename), true);
    if (isset($ret["content"]["timestamp"])) {
        $ret["content_timestamp"] = $ret["content"]["timestamp"];
    } else {
        $ret["content_timestamp"] = $ret["file_timestamp"];
    }
    if ($ret["content_timestamp"] < $last_data || $ret["file_timestamp"] < $last_data) {
       return false;
    }
    return $ret;
}

// Populate data
$ret["twitter"] = process_json("data:twitter.json", $last_data);
$ret["data"] = process_json($filename, $last_data);
$ret["status"] = "success";

echo json_encode($ret);

// Update statistics
$redis->incr("stats:web:json:processed");
stat_update("web:json:processed");
?>
