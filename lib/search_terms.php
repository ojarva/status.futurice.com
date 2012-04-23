<?php
$results = array();
$results[] = array("/page/printers", array("printers", "printing", "scanner", "paper", "papers", "consumables"));
$results[] = array("/page/it-tickets", array("tickets", "requests"));
$results[] = array("/page/services", array("status", "services"));
$results[] = array("/page/sauna", array("sauna", "temperature", "helsinki sauna", "helsinki office sauna", "sauna at helsinki office"));
$results[] = array("/page/what", array("what", "info", "information", "howto", "source", "code"));
$results[] = array("/page/network-map", array("netmap", "map", "traffic", "network", "internet"));

$services = json_decode($redis->get("data:services.json"), true);
$keywords = array();
$excluded_keywords = array();
foreach ($services["per_service"] as $k => $v) {
    $clear_name = str_replace(array("(", ")"), array("", ""), $v["name"]);
    $terms = explode(" ", $clear_name);
    foreach ($terms as $v) {
        if (in_array($v, $keywords) === TRUE) {
            $excluded_keywords[] = $v;
        }
        if (in_array($v, $keywords) === FALSE) {
            $keywords[] = $v;
        }
    }
}

foreach ($services["per_service"] as $k => $v) {
    $clear_name = str_replace(array("(", ")"), array("", ""), $v["name"]);
    $all_terms = explode(" ", $clear_name);
    $allowed_terms = array($v["name"]);
    foreach ($all_terms as $v) {
        if (!in_array($v, $excluded_keywords)) {
            $allowed_terms[] = $v;
        }
    }

    $results[] = array("/page/servicedetails?id=$k", $allowed_terms);
}

$typeahead_keywords = array();

foreach ($results as $v) {
    foreach ($v[1] as $keyword) {
        $typeahead_keywords[] = $keyword;
    }
}
?>
