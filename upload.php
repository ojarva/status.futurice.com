<?php
// This file handles uploads from RT server and network monitoring server
// Only files listed in upload_settings.php are allowed.

// Do not cache
header('Cache-Control: no-cache, no-store, max-age=0, must-revalidate');
header('Expires: Mon, 26 Jul 1997 05:00:00 GMT');
header('Pragma: no-cache');
header("content-type: application/json");

// Sample file is named as upload_settings.php.sample. Move it, and change password to something more complex.
require_once("upload_settings.php");
require_once("lib/redis.php");

function response($success, $status) {
    if (!$status) {
        error_log("upload.php: ".$status);
    }
    return json_encode(array("success" => $success, "status" => $status));
}

if (!isset($what_allowed)) {
    echo response(false, "Improperly configured: missing what_allowed from upload_settings.php");
    exit(0);
}
if (!isset($password)) {
    echo response(false, "Improperly configured: missing password from upload_settings.php");
    exit(0);
}
if ($password == "your_randomly_generated_password") {
    echo response(false, "Improperly configured: using default password.");
    exit(0);
}



if (!isset($_POST["password"]) || $_POST["password"] != $password) {
    Header('HTTP/1.1 403 Forbidden');
    echo response(false, "Wrong password");
    $redis->pipeline(function($pipe) {
     $pipe->incr("stats:web:invalid");
     $pipe->incr("stats:web:upload:pwfail");
    });
    exit(0);
}
$what = $_POST["what"];

if (!in_array($what, $what_allowed)) {
    echo response(false, "Invalid target name");
    $redis->pipeline(function($pipe) {
     $pipe->incr("stats:web:invalid");
     $pipe->incr("stats:web:upload:targetnamefail");
    });
    exit(0);
}


$pinfo = pathinfo($what);
$expiration_time = 3600 * 24 * 30; // One month

if ($pinfo["extension"] == "json") {
    $filename = "data:".$what; // Already validated
    $contents = file_get_contents($_FILES["data"]["tmp_name"]);
    $hash = sha1($contents);
    $timestamp = time();
    $redis->setex($filename, $expiration_time, $contents);
    $redis->setex($filename."-hash", $expiration_time, $hash);
    $redis->setex($filename."-mtime", $expiration_time, $timestamp);
    $redis->incr("stats:web:upload:success");
    $redis->publish("pubsub:$what", json_encode(array("hash" => $hash, "mtime" => $timestamp)));
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
            $hash = sha1($contents);
            $mtime = time();
            $redis->setex($rediskey, $expiration_time, $contents);
            $redis->setex("$rediskey-hash", $expiration_time, $hash);
            $redis->setex("$rediskey-mtime", $expiration_time, $mtime);
            $redis->publish("pubsub:$rediskey", json_encode(array("hash" => $hash, "mtime" => $mtime)));
            $redis->incr("stats:web:upload:pngsuccess");
        }
        $redis->incr("stats:web:upload:success");
    } else {
        echo response(false, "File upload failed: $filename\n");
        $redis->incr("stats:web:upload:filefailed");
        $redis->incr("stats:web:invalid");
    }
}
?>
