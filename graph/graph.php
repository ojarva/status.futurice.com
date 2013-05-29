<?php
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

system('rrdtool graph - --end now --start end-7d --upper-limit 100 -l 0  -v "Percentage" -c "SHADEA#FFFFFF" -c "SHADEB#FFFFFF" -c "FRAME#FFFFFF" -c "BACK#FFFFFF" '.$extra.' --width 400'.
       ' "DEF:value1=/home/ubuntu/graphs/'.$filename.'.rrd:value:AVERAGE" '.
       ' "CDEF:value1green=value1,50,100,LIMIT" '.
       ' "CDEF:value1yellow=value1,20,50,LIMIT" '.
       ' "CDEF:value1red=value1,0,20,LIMIT" '.
       ' "AREA:value1red#FF1300"' .
       ' "AREA:value1yellow#DED00F"' .
       ' "AREA:value1green#29FF00"');
?>
