<?php
if (!isset($_GET["q"])) {
 Header("Location: http://status.futurice.com/");
 exit();
}

// similar_text is O(n^3) -> prevent (accidental) DoS with long query strings.
$q = substr($_GET["q"], 0, 30);

require_once("lib/search_terms.php");

$bestscore = 0;
$besturl = false;

foreach ($results as $v) {
    foreach ($v[1] as $keyword) {
        if ($q == $keyword) {
            $bestscore = 9999;
            $besturl = $v[0];
        } else {
            $score = similar_text($keyword, $q);
            if ($score > $bestscore) {
                $besturl = $v[0];
                $bestscore = $score;
                if (metaphone($q, 6) == metaphone($keyword, 6)) {
                    $bestscore += 4;
                }
            }
        }
    }
}

if ($bestscore > 2) {
    Header("Location: http://status.futurice.com$besturl");
    exit();
}


?>

<script type="text/javascript">
var typeahead_data = <?php echo json_encode($typeahead_keywords); ?>;

$(document).ready(function() {
    $("#searchbox").typeahead({source: typeahead_data});
});

</script>

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
			<input type="text" class="input-medium search-query" placeholder="Type search query" name="q" autocomplete="off" id="searchbox">
			<button type="submit" class="btn">Search</button>
		</form>
	</div>
</div>
