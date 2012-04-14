<?
if (!isset($_GET["filename"])) {
 echo "No filename provided.";
 exit();
}
$filename = basename($_GET["filename"]);
Header("Content-Type: image/png");

$extra = "";
if (isset($_GET["title"])) {
 $title = str_replace(array("'", "\\", ";", "`", "$"), array("", "", "", "", ""), $_GET["title"]);
 $title = escapeshellarg($title);
 $extra = '-t "'.$title.'"';
}

system('rrdtool graph - --end now --start end-3h -r -v "Pages" -c "SHADEA#FFFFFF" -c "SHADEB#FFFFFF" -c "FRAME#FFFFFF" -c "BACK#FFFFFF" '.$extra.' --width 400 "DEF:value1=/home/ubuntu/graphs/'.$filename.'.rrd:value2:AVERAGE" "LINE1:value1#00C000"');
?>
