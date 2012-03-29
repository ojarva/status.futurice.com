<?
// This file handles uploads from RT server and network monitoring server

// File contains $password = "secret password for upload authentication";
require_once("upload_settings.php");

/* Only files in this array are allowed. Make sure web server user
(typically apache, httpd or www-data) is allowed to write to these files */
$what_allowed = array("ittickets.json", "netmap.png");

function response($success, $status) {
 return json_encode(array("success" => $success, "status" => $status));
}

if ($_POST["password"] != $password) {
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
 $ext = pathinfo($filename, PATHINFO_EXTENSION);
 if ($ext == "png") {
  exec("advpng -z1 \"$filename\"");
 }
} else {
 echo response(false, "File upload failed: $filename\n");
}

?>
