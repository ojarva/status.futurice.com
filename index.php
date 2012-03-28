<?php
Header("Content-Type: text/html; charset=utf-8");
$pagename = "main";
if (isset($_GET["page"])) {
 $temp = basename($_GET["page"]);
 if (file_exists("pages/$temp.php")) {
  $pagename = $temp;
 }
}
$pages = array(array("main", "Home"),
	array("services", "Services"),
	array("netmap", "Network map"),
	array("ittickets", "IT tickets"),
	array("what", "What?"),
	array("todo", "TODO"));
?>

<!DOCTYPE html>
<html lang="en">
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
          <a class="brand" href="/page/main">status</a>
          <div class="nav-collapse">
            <ul class="nav">
<?
 foreach ($pages as $k => $v) {
  ?><li<?if ($v[0] == $pagename) {?> class="active"<?}?>><a href="/page/<?=$v[0];?>"><?=$v[1];?></a></li><?
 }
?>
            </ul>
          </div><!--/.nav-collapse -->
        </div>
      </div>
    </div>

    <div class="container">

<?
require_once("pages/$pagename.php");
?>


      <hr>

      <footer>
        <p>&copy; Futurice 2012</p>
      </footer>

    </div> <!-- /container -->

  </body>
</html>

