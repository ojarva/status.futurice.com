<?php
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
 }
}
$pages = array(array("/", "Home"),
	array("/page/services", "Services"),
	array("/page/network-map", "Network map"),
	array("/page/it-tickets", "IT tickets"),
	array("/page/what", "What?"),
	array("/page/todo", "TODO"));

function callback($buffer) {
 $buffer = str_replace("\r\n", " ", $buffer);
 $buffer = str_replace("\n", " ", $buffer);
 $buffer = str_replace("\t", " ", $buffer);
 $buffer = preg_replace( '/\s+/', ' ', $buffer);
 return $buffer;
}
ob_start("callback");
?>

<!DOCTYPE html>
<html lang="en" manifest="/cache.appcache">
  <head>
    <meta charset="utf-8">
    <title>status.futurice.com</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Futurice IT status">
    <meta name="author" content="Olli Jarva">

    <link href="/css/combined.min.css" rel="stylesheet">
    <!--[if lt IE 9]>
      <script src="http://html5shim.googlecode.com/svn/trunk/html5.js"></script>
    <![endif]-->
    <script src="/js/combined.min.js"></script>
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
<?
 foreach ($pages as $k => $v) {
  ?><li<?if ($v[0] == $pagename) {?> class="active"<?}?>><a href="<?=$v[0];?>"><?=$v[1];?></a></li><?
 }
?>
            </ul>

            <ul class="nav pull-right">
             <li id="cache-status" style="display:; ">
              <form class="navbar-form"><button class="btn btn-small btn-inverse" id="reload-button">Current version</button></form>
             </li>
             <li id="cache-update-status" style="display:none">
                <div class="progress progress-striped active" style="margin-bottom:0px; margin:10px; width:100px">
                 <div class="bar" style="width: 30%;"></div>
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

<?
ob_end_flush();

ob_start("callback");
require_once("pages/$pagename.php");
?>


      <hr style="padding-top: 5em">

      <footer id="twitter_footer">

      </footer>

    </div> <!-- /container -->

  </body>
</html>
<?
ob_end_flush();
?>
