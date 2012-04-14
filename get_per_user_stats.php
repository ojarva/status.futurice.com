<?
//session_start();
Header("Content-Type: application/json");
require_once("lib/redis.php");

$ip = $_SERVER["REMOTE_ADDR"];
$session = session_id();

$get_values = array("total_web_pageview",
	"your_ip_web_pageview",
	"your_ip_web_json_processed",
	"your_ip_static_served",
	"your_session_web_pageview",
	"your_session_web_json_processed",
	"your_session_static_served");

$autofill = array();
$responses = $redis->pipeline(function($pipe) {
    $ip = $_SERVER["REMOTE_ADDR"];
    $session = session_id();
    $get_values = array("per_user:total:web:pageview",
	"per_user:ip:$ip:web:pageview",
	"per_user:ip:$ip:web:json:processed",
	"per_user:ip:$ip:web:static:served",
	"per_user:session:$session:web:pageview",
	"per_user:session:$session:web:json:processed",
	"per_user:session:$session:web:static:served");

    foreach ($get_values as $k => $v) {
        $pipe->get($v);
    }
});

$autofill = array_combine($get_values, $responses);

$content = json_encode(array("autofill" => $autofill));


http_cache_etag();
Header("Cache-Control: private");
http_send_content_type("application/json");
http_send_data($content);
?>
