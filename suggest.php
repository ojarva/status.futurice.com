<?php
Header("Content-Type: application/x-suggestions+json");

require_once("lib/redis.php");
require_once("lib/search_terms.php");

if (!isset($_GET["q"])) {
    echo json_encode(array());
}

$q = substr($_GET["q"], 0, 30);

$terms = array();
$nums = array();
$urls = array();

$c = 0;

foreach ($results as $k => $v) {
    foreach ($v[1] as $term) {
        if (stripos($term, $q) !== FALSE) {
            $terms[] = $term;
            $nums[] = "1 result";
            $urls[] = $v[0];
            $c++;
            break;
        }
    }
    if ($c > 8) {
        break;
    }
}

echo json_encode(array($q, $terms, $nums, $urls));
?>
