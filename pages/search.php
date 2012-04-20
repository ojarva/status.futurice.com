<?php
if (!isset($_GET["q"])) {
 Header("Location: http://status.futurice.com/");
 exit();
}


// similar_text is O(n^3) -> prevent (accidental) DoS with long query strings.
$q = substr($_GET["q"], 0, 30);

$services = json_decode($redis->get("data:services.json"), true);


$results = array();
$results[] = array("/page/printers", array("printers", "printing", "scanner", "paper", "papers", "consumables"));
$results[] = array("/page/it-tickets", array("tickets", "requests"));
$results[] = array("/page/services", array("status", "services"));
$results[] = array("/page/sauna", array("sauna", "temperature", "helsinki sauna", "helsinki office sauna", "sauna at helsinki office"));
$results[] = array("/page/what", array("what", "info", "information", "howto", "source", "code"));
$results[] = array("/page/network-map", array("netmap", "map", "traffic", "network", "internet"));


foreach ($services["per_service"] as $k => $v) {
   $results[] = array("/page/servicedetails/?id=$k", array($v["name"]));
}

$bestscore = 0;
$besturl = false;
foreach ($results as $v) {
    foreach ($v[1] as $keyword) {
        $score = similar_text($keyword, $q);
        if ($score > $bestscore) {
            $besturl = $v[0];
            $bestscore = $score;
        }
    }
}
if ($bestscore > 2) {
    Header("Location: http://status.futurice.com$besturl");
    exit();
}?>

<div class="row">
	<div class="span12">
		<h1>Sorry, no results</h1>
	</div>
</div>

<div class="row">
	<div class="span12">
		<p>We didn't have anything relevant for your query. Feel free to try again or navigate using top bar. Also, this basically supports only single keywords, nothing more complex.</p>
	</div>

</div>

<div class="row">
	<div class="span12">
		<form class="well form-search" action="?" method="get">
			<input type="text" class="input-medium search-query" placeholder="Type search query" name="q">
			<button type="submit" class="btn">Search</button>
		</form>
	</div>
</div>
