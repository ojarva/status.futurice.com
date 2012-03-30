function update_frontpage() {
    $.get("/frontpage_json.php", function (data) {
        for (key in data.autofill) {
            if ($("#" + key) !== null) {
                $("#" + key).html(data.autofill[key]);
            }
        }
    }, "json");
    setTimeout("update_frontpage()", 1000*60);
}

$(document).ready(function () {
   update_frontpage();
});
