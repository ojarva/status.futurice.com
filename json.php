<?
Header("Content-Type: application/json");
$ret = array("message_timestamp" => time(), "status" => false, "status_message" => false, "data" => array("file_timestamp" => false, "content_timestamp" => false, "content" => false), "twitter" => array("file_timestamp" => false, "content_timestamp" => false, "content" => false));

if (isset($_GET["filename"])) {
    $filename = "data/".basename($_GET["filename"]);
}
if (!(isset($filename) && file_exists($filename))) {
    $ret["status"] = "error";
    $ret["status_message"] = "Invalid request / no such file";
    echo json_encode($ret);
    exit();
}
if (isset($_GET["last_data"])) {
   $last_data = intval($_GET["last_data"]);
} else {
   $last_data = 0;
}

function process_json($filename, $last_data) {
    $ret = array("file_timestamp" => filemtime($filename), "content_timestamp" => false, "content" => false);
    $ret["content"] = json_decode(file_get_contents($filename), true);
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

$ret["twitter"] = process_json("data/twitter.json", $last_data);
$ret["data"] = process_json($filename, $last_data);


$ret["status"] = "success";
echo json_encode($ret);
?>
