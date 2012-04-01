$(document).ready(function() {
    $("#update_data").pagerefresh({"short_timeout": 5*60, "long_timeout": 30*60});
});

function fetch_data() {
    $("#netmap-img").attr("src", "/netmap.png?timestamp="+ (new Date()).getTime());
    $("#update_data").pagerefresh("fetch_done", (new Date()).getTime());
}
