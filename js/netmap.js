var paused = false,
    refresh_interval = 5;


function update_next_reload() {
    var next_reload = $("#next-reload").data("reload-timestamp");
    if (!next_reload || moment(next_reload) < moment()) {
        $("#next-reload").html("Next reload right now");
        $("#next-reload").data("reload-timestamp", (new Date()).getTime() + refresh_interval * 60 * 1000);
        fetch_data();
    } else {
        $("#next-reload").html("Next reload " + moment(next_reload).fromNow());
    }
    setTimeout("update_next_reload();", 1000);
}

$(document).ready(function() {
    update_next_reload();
    $("#update_now_button").click(function() {
        fetch_data();
    });

    $(window).blur(function () {
        paused = true;
        $("#next-reload").data("reload-timestamp", (new Date()).getTime() + 30 * 60 * 1000);
    });

    $(window).focus(function () {
        $("#next-reload").data("reload-timestamp", (new Date()).getTime() + refresh_interval * 60 * 1000);
        paused = false;
        if ($("#next-reload").data("reloaded") > 0 && (((new Date()).getTime() * 1000) - $("#next-reload").data("reloaded")) > 1000 * 60 * 2) {
            fetch_data();
        }
    });
});

function fetch_data() {
    console.log("fetch_data");
    $("#progress-indicator").show();
    $("#update_now_button").addClass("disabled");

    $("#next-reload").data("reloaded", (new Date()).getTime()*1000);

    clearInterval($("body").data("status_timestamp_interval"));
    $("body").data("status_timestamp_interval", setInterval('$("#status-timestamp").html(moment('+(new Date()).getTime()+').fromNow()+".");', 1000));

    $("#netmap-img").attr("src", "/netmap.png?timestamp="+ (new Date()).getTime());

    setTimeout('$("#update_now_button").removeClass("disabled");$("#progress-indicator").hide();', 500);

}
