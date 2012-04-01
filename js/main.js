function fetch_data() {
    $.get("/frontpage_json.php", function (data) {
        for (key in data.autofill) {
            if ($("#" + key) !== null) {
                $("#" + key).html(data.autofill[key]);
            }
        }
    }, "json");
}

$(document).ready(function () {
    $("#update_data").pagerefresh({"short_timeout": 1*60, "long_timeout": 15*60});
});
