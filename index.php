<?
$pagename = "main";
if (isset($_GET["page"])) {
 $temp = $_GET["page"];
 if (file_exists("pages/$temp.php")) {
  $pagename = $temp;
 }
}
?>

<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>status.futurice.com</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Futurice IT status">
    <meta name="author" content="Olli Jarva">

    <link href="css/combined.css" rel="stylesheet">
    <style type="text/css">
      body {
        padding-top: 60px;
        padding-bottom: 40px;
      }
    </style>

    <!--[if lt IE 9]>
      <script src="http://html5shim.googlecode.com/svn/trunk/html5.js"></script>
    <![endif]-->
<?/*
    <script src="js/jquery.js"></script>
    <script src="js/bootstrap-transition.js"></script>
    <script src="js/bootstrap-alert.js"></script>
    <script src="js/bootstrap-modal.js"></script>
    <script src="js/bootstrap-dropdown.js"></script>
    <script src="js/bootstrap-scrollspy.js"></script>
    <script src="js/bootstrap-tab.js"></script>
    <script src="js/bootstrap-tooltip.js"></script>
    <script src="js/bootstrap-popover.js"></script>
    <script src="js/bootstrap-button.js"></script>
    <script src="js/bootstrap-collapse.js"></script>
    <script src="js/bootstrap-carousel.js"></script>
<!--    <script src="js/bootstrap-typeahead.js"></script> -->
    <script src="js/underscore.js"></script>
    <script src="js/raphael.js"></script>
    <script src="js/raphael-sparkline.js"></script>
*/?>
    <script src="js/combined.min.js"></script>
<script type="text/javascript">

$(document).ready(function() {
$("[rel=popover]")
      .popover()
/*      .click(function(e) {
        e.preventDefault()
      })*/
});
</script>

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
          <a class="brand" href="?page=main">status</a>
          <div class="nav-collapse">
            <ul class="nav">
              <li class="active"><a href="?page=main">Home</a></li>
              <li><a href="?page=services">Services</a></li>
              <li><a href="?page=netmap">Network map</a></li>
              <li><a href="?page=ittickets">IT tickets</a></li>
              <li><a href="?page=todo">todo</a></li>
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

