$(document).ready(function () {
    $.get("/frontpage_json.php", function (data) {
        for (key in data.autofill) {
            if ($("#" + key) !== null) {
                $("#" + key).html(data.autofill[key]);
            }
        }
    }, "json");
});
