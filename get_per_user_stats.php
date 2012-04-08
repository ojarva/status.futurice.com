<?
session_start();
Header("Content-Type: application/json");
$redis = new Redis();
$redis->connect("localhost");

$ip = $_SERVER["REMOTE_ADDR"];
$session = session_id();

$autofill = array();

$autofill["total_web_pageview"] = $redis->get("per_user:total:web:pageview");
$autofill["your_ip_web_pageview"] = $redis->get("per_user:ip:$ip:web:pageview");
$autofill["your_ip_web_json_processed"] = $redis->get("per_user:ip:$ip:web:json:processed");
$autofill["your_ip_static_served"] = $redis->get("per_user:ip:$ip:web:static:served");
$autofill["your_session_web_pageview"] = $redis->get("per_user:session:$session:web:pageview");
$autofill["your_session_web_json_processed"] = $redis->get("per_user:session:$session:web:json:processed");
$autofill["your_session_static_served"] = $redis->get("per_user:session:$session:web:static:served");

$content = json_encode(array("autofill" => $autofill));


http_cache_etag();
Header("Cache-Control: private");
http_send_content_type("application/json");
http_send_data($content);
?>
