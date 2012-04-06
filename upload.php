<?
// This file handles uploads from RT server and network monitoring server

// Do not cache
header('Cache-Control: no-cache, no-store, max-age=0, must-revalidate');
header('Expires: Mon, 26 Jul 1997 05:00:00 GMT');
header('Pragma: no-cache');
header("content-type: application/json");

// File contains $password = "secret password for upload authentication"; $what_allowed=array("allowed_files.json", "netmap.png", ...);
require_once("upload_settings.php");

function response($success, $status) {
    return json_encode(array("success" => $success, "status" => $status));
}


if ($_POST["password"] != $password) {
    Header('HTTP/1.1 403 Forbidden');
    echo response(false, "Wrong password");
    exit(0);
}
$what = $_POST["what"];

if (!in_array($what, $what_allowed)) {
    echo response(false, "Invalid target name");
    exit(0);
}

$redis = new Redis();
$redis->connect("localhost");

$pinfo = pathinfo($what);
$expiration_time = 3600 * 24 * 30; // One month

if ($pinfo["extension"] == "json") {
    $filename = "data:".$what; // Already validated
    $contents = file_get_contents($_FILES["data"]["tmp_name"]);
    $redis->setex($filename, $expiration_time, $contents);
    $redis->setex($filename."-hash", $expiration_time, sha1($contents));
    $redis->setex($filename."-mtime", $expiration_time, time());
    echo response(true, "Upload succeeded");
} else {
    $filename = "upload/".$what;
    if (move_uploaded_file($_FILES["data"]["tmp_name"], $filename)) {
        echo response(true, "Upload succeeded");
        $pinfo = pathinfo($filename);
        if ($pinfo["extension"] == "png") {
            exec("advpng -z1 \"$filename\"");
            $contents = json_encode( array("timestamp" => time()) );
            $rediskey = "data:".$pinfo["filename"].".json";
            $redis->setex($rediskey, $expiration_time, $contents);
            $redis->setex("$rediskey-hash", $expiration_time, sha1($contents));
            $redis->setex("$rediskey-mtime", $expiration_time, time());
        }
    } else {
        echo response(false, "File upload failed: $filename\n");
    }
}
$redis->close();
?>
