<?
Header("Content-Type: application/json");
$autofill = array();
$tickets_json = json_decode(file_get_contents("ittickets.json"), true);
$autofill["unique_7d"] = $tickets_json["data"]["unique_manual_7d"];
$services_json = json_decode(file_get_contents("services.json"), true);
$autofill["services_up"] = $services_json["overall"]["services_up"];
$autofill["services_unknown"] = $services_json["overall"]["services_unknown"];
$autofill["services_down"] = $services_json["overall"]["services_down"];
echo json_encode(array("autofill" => $autofill));
?>
