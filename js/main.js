function fetch_data() {
}

$(document).ready(function () {
    $("#update_data").pagerefresh({"short_timeout": 1*60, "long_timeout": 15*60, "filewatch": "frontpage.json"});
});
