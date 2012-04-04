<?
// This file handles uploads from RT server and network monitoring server

// File contains $password = "secret password for upload authentication"; $what_allowed=array("allowed_files.json", "netmap.png", ...);
require_once("upload_settings.php");

// Do not cache
header('Cache-Control: no-cache, no-store, max-age=0, must-revalidate');
header('Expires: Mon, 26 Jul 1997 05:00:00 GMT');
header('Pragma: no-cache');
header("content-type: application/json");

function response($success, $status) {
    return json_encode(array("success" => $success, "status" => $status));
}

if (!isset($POST["password"]) || $_POST["password"] != $password) {
    Header('HTTP/1.1 403 Forbidden');
    echo response(false, "Wrong password");
    exit(0);
}

if (!in_array($_POST["what"], $what_allowed)) {
    echo response(false, "Invalid target name");
    exit(0);
}

$filename = "upload/".$_POST["what"]; // Already validated
if (move_uploaded_file($_FILES["data"]["tmp_name"], $filename)) {
    echo response(true, "Upload succeeded");
    $pinfo = pathinfo($filename);
    if ($pinfo["extension"] == "png") {
        exec("advpng -z1 \"$filename\"");
        file_put_contents("upload/".$pinfo["filename"].".json", json_encode(array("timestamp" => time() )) );
    }
} else {
    echo response(false, "File upload failed: $filename\n");
}

?>
