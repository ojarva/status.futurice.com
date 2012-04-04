function fetch_data() {
    var data = $("body").data("pagerefresh-data").content;
    for (var key in data.autofill) {
        if ($("#" + key) !== null) {
            $("#" + key).html(data.autofill[key]);
        }
    }
}

$(document).ready(function () {
    $("#update_data").pagerefresh({"short_timeout": 1*60, "long_timeout": 15*60, "filewatch": "frontpage.json"});
});
