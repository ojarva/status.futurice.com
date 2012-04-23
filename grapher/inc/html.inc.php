<?php

# html related functions

require_once 'conf/common.inc.php';
require_once 'inc/rrdtool.class.php';
require_once 'inc/functions.inc.php';
require_once 'inc/collectd.inc.php';

function html_start() {
	global $CONFIG;

	$path = htmlentities(breadcrumbs());

	echo <<<EOT
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>status.futurice.com {$path}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Futurice IT status">
    <meta name="author" content="Olli Jarva">

    <meta name="apple-mobile-web-app-capable" content="yes" />
    <meta name="apple-mobile-web-app-status-bar-style" content="black" />
    <link rel="apple-touch-startup-image" href="/img/ios-splashscreen.png" />

    <link href="/css/combined.min.css" rel="stylesheet">
    <!--[if lt IE 9]>
      <script src="http://html5shim.googlecode.com/svn/trunk/html5.js"></script>
    <![endif]-->
    <script src="/js/combined.min.js"></script>
	<link rel="stylesheet" href="{$CONFIG['weburl']}layout/style.css" type="text/css">
	<script type="text/javascript" src="{$CONFIG['weburl']}ajax.js"></script>
  </head>

  <body>

    <div class="navbar navbar-fixed-top">
      <div class="navbar-inner">
        <div class="container">
          <a class="btn btn-navbar" data-toggle="collapse" data-target=".nav-collapse">
            <span class="icon-bar"></span>
            <span class="icon-bar"></span>
            <span class="icon-bar"></span>
          </a>
          <a class="brand" href="/">Status</a>
          <div class="nav-collapse">
            <ul class="nav">
		<li><a href="/">Home</a></li>
		<li><a href="/grapher/host.php?h=status.futurice.com">Graphs frontpage</a></li>
           </ul>

          </div><!--/.nav-collapse -->
        </div>
      </div>
    </div>

    <div class="container">
<div class="row">
        <div class="span12">
                <div id="notify-box"></div>
        </div>
</div>

EOT;
}

function html_end() {
	global $CONFIG;

	echo <<<EOT


      <hr style="padding-top: 5em">

      <footer>
<span class="small"><a href="http://pommi.nethuis.nl/category/cgp/" rel="external">Collectd Graph Panel</a> is distributed under the <a href="{$CONFIG['weburl']}doc/LICENSE" rel="licence">GNU General Public License (GPLv3)</a></span>
      </footer>

    </div> <!-- /container -->
<script type="text/javascript">

  var _gaq = _gaq || [];
  _gaq.push(['_setAccount', 'UA-31018904-1']);
  _gaq.push(['_trackPageview']);

  (function() {
    var ga = document.createElement('script'); ga.type = 'text/javascript'; ga.async = true;
    ga.src = ('https:' == document.location.protocol ? 'https://ssl' : 'http://www') + '.google-analytics.com/ga.js';
    var s = document.getElementsByTagName('script')[0]; s.parentNode.insertBefore(ga, s);
  })();

</script>
  </body>
</html>

EOT;
}

function plugin_header($host, $plugin, $status) {
	global $CONFIG;

	if ($status == 1) {
		$f = 'get';
		$i = 'plus';
		$a = '+';
	} else {
		$f = 'rm';
		$i = 'minus';
		$a = '-';
	}

	return printf("<h3><span class=\"point\" onclick=\"javascript:%sP('%s','%s')\"><img src=\"%slayout/%s.gif\" alt=\"[%s]\"> %s</span></h3>\n", $f, $host, $plugin, $CONFIG['weburl'], $i, $a, $plugin);
}

function host_summary($hosts) {
	global $CONFIG;

	$rrd = new RRDTool($CONFIG['rrdtool']);

	echo "<table class=\"summary\">\n";

	$row_style = array(0 => "even", 1 => "odd");
	$host_counter = 0;

	foreach($hosts as $host) {
		$host_counter++;

		printf('<tr class="%s">', $row_style[$host_counter % 2]);
		printf('<th><a href="%shost.php?h=%s">%s</a></th>',
			$CONFIG['weburl'],$host, $host);

		if ($CONFIG['showload']) {
			collectd_flush(sprintf('%s/load/load', $host));
			$rrd_info = $rrd->rrd_info($CONFIG['datadir'].'/'.$host.'/load/load.rrd');

			# ignore if file does not exist
			if (!$rrd_info)
				continue;

			if (isset($rrd_info['ds[shortterm].last_ds']) &&
				isset($rrd_info['ds[midterm].last_ds']) &&
				isset($rrd_info['ds[longterm].last_ds'])) {

				printf('<td>%.2f</td><td>%.2f</td><td>%.2f</td>',
					$rrd_info['ds[shortterm].last_ds'],
					$rrd_info['ds[midterm].last_ds'],
					$rrd_info['ds[longterm].last_ds']);
			}
		}

		print "</tr>\n";
	}

	echo "</table>\n";
}


function breadcrumbs() {
	$path = '';
	if (validate_get(GET('h'), 'host'))
		$path .= ' - '.ucfirst(GET('h'));
	if (validate_get(GET('p'), 'plugin'))
		$path .= ' - '.ucfirst(GET('p'));
	if (validate_get(GET('pi'), 'pinstance'))
		$path .= ' - '.GET('pi');
	if (validate_get(GET('t'), 'type') && validate_get(GET('p'), 'plugin') && GET('t') != GET('p'))
		$path .= ' - '.GET('t');
	if (validate_get(GET('ti'), 'tinstance'))
		$path .= ' - '.GET('ti');

	return $path;
}

?>
