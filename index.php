<?php
require_once("lib/redis.php");
require_once("lib/userstats.php");

Header("Content-Type: text/html; charset=utf-8");
$pagename = "main";
if (isset($_GET["page"])) {
    $temp = basename($_GET["page"]);
    if ($temp == "network-map") {
        $pagename = "netmap";
    }
    $temp = str_replace("-", "", $temp);
    if (file_exists("pages/$temp.php")) {
        $pagename = $temp;
        $redis->incr("stats:web:pageview");
        stat_update("web:pageview");
    } else {
        $redis->incr("stats:web:invalidpage");
        $redis->incr("stats:web:invalid");
        stat_update("web:invalid");
    }
}
$pages = array(array("/", "Home"),
	array("/page/services", "Services"),
	array("/page/network-map", "Network map"),
	array("/page/it-tickets", "IT tickets"),
	array("/page/printers", "Printers"),
	array("/page/misc-stats", "Server stats"),
	array("/page/what", "What?"));

$manifestenabled = false;
foreach ($pages as $k => $v) {
    if ($_SERVER["REQUEST_URI"] == $v[0]) {
        $manifestenabled = true;
    }
}
function callback($buffer) {
    return $buffer;
    $search = array(
        '/\>[^\S ]+/s', //strip whitespaces after tags, except space
        '/[^\S ]+\</s', //strip whitespaces before tags, except space
        '/(\s)+/s'  // shorten multiple whitespace sequences
        );
    $replace = array(
        '>',
        '<',
        '\\1'
        );
    $buffer = preg_replace($search, $replace, $buffer);
    return $buffer;
}
ob_start("callback");
?>

<!DOCTYPE html>
<html lang="en"<?php
if ($manifestenabled) {
    ?> manifest="/cache.manifest"<?php
}
?>>
  <head>
    <meta charset="utf-8">
    <title>status.futurice.com</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Futurice IT status - because transparency brings shitloads of good">
    <meta name="author" content="Olli Jarva">

    <meta name="apple-mobile-web-app-capable" content="yes" />
    <meta name="apple-mobile-web-app-status-bar-style" content="black" />
    <link rel="apple-touch-startup-image" href="/img/ios-splashscreen.png" />

    <link href="/css/combined.min.css" rel="stylesheet">
    <!--[if lt IE 9]>
      <script src="/js/html5.js"></script>
    <![endif]-->
    <script src="/js/combined.min.js"></script>
    <link rel="search" type="application/opensearchdescription+xml" title="Futurice Status" href="/opensearch.xml"/>

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
<?php
 foreach ($pages as $k => $v) {
  ?><li<?php if ($v[0] == $pagename) {?> class="active"<?php }?>><a href="<?=$v[0];?>"><?=$v[1];?></a></li><?php
 }
?>
            </ul>

            <ul class="nav pull-right" style="display:none">
             <li id="cache-status" style="display:; ">
              <form class="navbar-form"><button class="btn btn-small btn-inverse" id="reload-button">Current version</button></form>
             </li>
             <li id="cache-update-status" style="display:none">
                <div class="progress progress-striped active" style="margin-bottom:0px; margin:10px; width:100px">
                 <div class="bar" style="width: 0%;"></div>
                </div>
             </li>
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

<?php
ob_end_flush();

ob_start("callback");
require_once("pages/$pagename.php");
?>


      <hr style="padding-top: 5em">

      <footer id="twitter_footer">

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
<!-- Piwik --> 
<script type="text/javascript">
var pkBaseURL = (("https:" == document.location.protocol) ? "https://analytics.futurice.com/piwik/" : "http://analytics.futurice.com/piwik/");
document.write(unescape("%3Cscript src='" + pkBaseURL + "piwik.js' type='text/javascript'%3E%3C/script%3E"));
</script><script type="text/javascript">
try {
var piwikTracker = Piwik.getTracker(pkBaseURL + "piwik.php", 13);
piwikTracker.trackPageView();
piwikTracker.enableLinkTracking();
} catch( err ) {}
</script><noscript><p><img src="http://analytics.futurice.com/piwik/piwik.php?idsite=13" style="border:0" alt="" /></p></noscript>
<!-- End Piwik Tracking Code -->

  </body>
</html>
<?php
ob_end_flush();
?>
