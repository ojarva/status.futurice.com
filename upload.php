<?
// File contains $password = "secret password for upload authentication";
require_once("upload_settings.php");
if ($_POST["password"] != $password) {
 echo "Wrong password.";
 exit(0);
}
$what_allowed = array("ittickets.json", "netmap.png");
if (!in_array($_POST["what"], $what_allowed)) {
 echo "Invalid target.";
 exit(0);
}

$filename = "upload/".$_POST["what"]; // Already validated
if (move_uploaded_file($_FILES["data"]["tmp_name"], $filename)) {
 echo "Upload succeeded";
 $ext = pathinfo($filename, PATHINFO_EXTENSION);
 if ($ext == "png") {
  exec("advpng -z1 \"$filename\"");
 }
} else {
 echo "File upload failed: $filename\n";
 var_dump($_FILES);
}

?>
