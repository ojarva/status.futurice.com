<?
$redis = new Redis();
$redis->connect("localhost");
$autofill = array();
$tickets_json = json_decode($redis->get("data:ittickets.json"), true);
$autofill["unique_7d"] = $tickets_json["data"]["unique_manual_7d"];
$services_json = json_decode($redis->get("data:services.json"), true);
$autofill["services_up"] = $services_json["overall"]["services_up"];
$autofill["services_unknown"] = $services_json["overall"]["services_unknown"];
$autofill["services_down"] = $services_json["overall"]["services_down"];

$lastmodified = max(filemtime(__FILE__), $redis->get("data:services.json-mtime"), $redis->get("data:ittickets.json-mtime"));
$content = json_encode(array("autofill" => $autofill));
$hash = sha1($content);

$exptime = 3600 * 24 * 30;

$redis->setex("data:frontpage.json", $exptime, $content);
$redis->setex("data:frontpage.json-mtime", $exptime, $lastmodified);
$redis->setex("data:frontpage.json-hash", $exptime, $hash);

?>
