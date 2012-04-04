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

system('rrdtool graph - --end now --start end-7d -u 100 -l 0 -r -v "Percentage" -c "SHADEA#FFFFFF" -c "SHADEB#FFFFFF" -c "FRAME#FFFFFF" -c "BACK#FFFFFF" '.$extra.' --width 400 "DEF:value1=/home/ubuntu/graphs/'.$filename.'.rrd:value:AVERAGE" "AREA:value1#00C000"');
?>
