$(document).ready(function() {
    $("#update_data").pagerefresh({"short_timeout": 6*60, "long_timeout": 30*60, "filewatch": "netmap.json"});
});

function fetch_data() {
    $("#netmap-img").attr("src", "/data/netmap.png?timestamp="+ (new Date()).getTime());
}
