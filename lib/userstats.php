<?
//session_start();

function stat_update($what) {
    global $redis;

    $value = $redis->incr("per_user:total:$what");
    $redis->expire("per_user:total:$what", 3600 * 24 * 90);

    $ip = $_SERVER['REMOTE_ADDR'];
    $value = $redis->incr("per_user:ip:$ip:$what");
    $redis->expire("per_user:ip:$ip:$what", 3600 * 24 * 90);

/*    $session = session_id();
    $value = $redis->incr("per_user:session:$session:$what");
    $redis->expire("per_user:session:$session:$what", 3600 * 24 * 90);*/
}
?>
