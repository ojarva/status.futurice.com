<?
$autofill = array();
$tickets_json = json_decode(file_get_contents("ittickets.json"), true);
$autofill["unique_7d"] = $tickets_json["data"]["unique_manual_7d"];
$services_json = json_decode(file_get_contents("services.json"), true);
$autofill["services_up"] = $services_json["overall"]["services_up"];
$autofill["services_unknown"] = $services_json["overall"]["services_unknown"];
$autofill["services_down"] = $services_json["overall"]["services_down"];

$lastmodified=max(filemtime(__FILE__), filemtime("services.json"), filemtime("ittickets.json"));

$etag = md5(serialize($autofill));
Header("Content-Type: application/json");
Header("Cache-Control: public; max-age=60");
Header("Etag: ".$etag);
Header("Last-Modified: ".gmdate("D, d M Y H:i:s", $lastmodified)." GMT");
Header("Expires: ".gmdate("D, d M Y H:i:s", $lastmodified+60)." GMT");
Header("Date: ".gmdate("D, d M Y H:i:s", $lastmodified)." GMT");


$etagHeader = (isset($_SERVER['HTTP_IF_NONE_MATCH']) ? trim($_SERVER['HTTP_IF_NONE_MATCH']) : false);
if ($etagHeader == $etag) {
       header("HTTP/1.1 304 Not Modified");
       exit;
}

echo json_encode(array("autofill" => $autofill));

?>
