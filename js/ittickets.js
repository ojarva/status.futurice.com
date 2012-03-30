function update_next_reload() {
    var next_reload = $("#next-reload").data("reload-timestamp");
    if (moment(next_reload) < moment()) {
        $("#next-reload").html("Next reload right now");
    } else {
        $("#next-reload").html("Next reload " + moment(next_reload).fromNow());
    }
    setTimeout("update_next_reload();", 1000);
}



var ticketdata;

$(document).ready(function() {
    $("#next-reload").data("reload-timestamp", (new Date()).getTime() + 15 * 60 * 1000);
    update_next_reload();
    $("#update_now_button").click(function() {
        fetch_data();
    });
    fetch_data();
});

function fetch_data() {
    $("#progress-indicator").show();
    $("#update_now_button").addClass("disabled");
    clearTimeout($("body").data("update_data_timeout"));
    $.get("/ittickets.json", function(data) {
        ticketdata = data.data;
        if ($("body").data("ittickets-initialized") !== true) {
            initialize_page();
        }
        update_data();
        $("body").data("update_data_timeout", setTimeout("fetch_data();", 1000*60*15)); // fetch data every 15 minutes
        $("#update_now_button").removeClass("disabled");
        $("#progress-indicator").hide();
    });
}

function initialize_page() {
    $("body").data("ittickets-initialized", true);
    $("#workflowchart").slideUp();
    $("#workflowchart").empty();
    $("#dotschart").empty();
    $("#emailpieholder").empty();

    $("#total-tickets-popover").data('content', "This is the total number of tickets since March 2010 ("+moment("2010-03-15", "YYYY-MM-DD").fromNow()+"), including automatic messages");
    $("#total-tickets-popover").data("original-title", "What?");
    $("#total-tickets-popover").data("placement", "top");
    $("#total-tickets-popover").attr("rel", "popover");
    $("#total-tickets-popover").popover();

    $("#dots_all").addClass("btn-info");
    $("#dotschart").dotsgraph({"data": ticketdata.dots.all});
    $("#dotschart").dotsgraph("update");

}

function update_data() {


    $("#next-reload").data("reload-timestamp", (new Date()).getTime() + 15 * 60 * 1000);
    clearInterval($("body").data("status_timestamp_interval"));
    $("body").data("status_timestamp_interval", setInterval('$("#status-timestamp").html(moment('+(new Date()).getTime()+').fromNow()+".");', 1000));

    for (var key in ticketdata) {
        if ($("#" + key) != null) {
            $("#" + key).html(ticketdata[key]);
        }
    }

    $(".dots-btn").click(function() {
        if ($(this).hasClass("btn-info")) {
            return;
        }
        $("#dotschart").slideDown();
        $("#workflowchart").slideUp();
        var dictname = $(this).data("name");
        $("#dotschart").dotsgraph({"data": ticketdata["dots"][dictname]});
        $("#dotschart").dotsgraph("update");
        $(".dots-btn").removeClass("btn-info");
        $("#change_graph").removeClass("btn-info");
        $(this).addClass("btn-info");
        $("#placeholder").html("mouse over the circles for more details");
        $("#placeholder").removeClass("hidden");
        $("#name2").addClass("hidden");
    });

    $("#change_graph").click(function() {
        $("#placeholder").html("mouse over the graph for more details");
        $("#dotschart").slideUp();
        $("#workflowchart").html("");
        process(ticketdata.workflow);
        $("#workflowchart").removeClass("hidden");
        $("#workflowchart").slideDown();
        $(".dots-btn").removeClass("btn-info");
        $(this).addClass("btn-info");
    });

    var emailpie_values = [ticketdata.other_users, ticketdata.futurice_users],
        emailpie_labels = ["External", "Internal"];
    Raphael("emailpieholder", 400, 200).pieChart(180, 100, 69, emailpie_values, emailpie_labels, "#fff");
}
