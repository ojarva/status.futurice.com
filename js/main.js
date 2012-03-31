var paused = false, refresh_interval = 1;
function update_next_reload() {
    var next_reload = $("#next-reload").data("reload-timestamp");
    if (!next_reload || moment(next_reload) < moment()) {
        $("#next-reload").html("Next reload right now");
        fetch_data();
    } else {
        $("#next-reload").html("Next reload " + moment(next_reload).fromNow());
    }
    setTimeout("update_next_reload();", 1000);
}

function fetch_data() {
    update_twitter();
    $("#next-reload").data("reload-timestamp", (new Date()).getTime() + refresh_interval * 60 * 1000);
    $.get("/frontpage_json.php", function (data) {
        for (key in data.autofill) {
            if ($("#" + key) !== null) {
                $("#" + key).html(data.autofill[key]);
            }
        }
    }, "json");
}

$(document).ready(function () {
    $("#next-reload").data("reload-timestamp", 0);
    update_next_reload();

    $(window).blur(function () {
        paused = true;
        refresh_interval = 30;
        $("#next-reload").data("reload-timestamp", (new Date()).getTime() + refresh_interval * 60 * 1000);
    });

    $(window).focus(function () {
        $("#next-reload").data("reload-timestamp", $("#next-reload").data("reload-timestamp") - ((refresh_interval - 1) * 60 * 1000));
        refresh_interval = 1;
        paused = false;
    });
});
