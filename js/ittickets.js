var ticketdata;

$(document).ready(function() {
    $("#update_data").pagerefresh({"short_timeout": 15 * 60, "long_timeout": 120 * 60, "filewatch": "ittickets.json"});
    if (localStorage) {
        var ticketdata_temp = localStorage.getItem("ittickets_json");
        if (ticketdata_temp != null) {
            try {
                ticketdata_temp = JSON.parse(ticketdata_temp);
                ticketdata = ticketdata_temp;
                fetch_data(true);
            } catch (e) {}
        }
    }
});

function fetch_data(from_storage) {
    var $workflowchart = $("#workflowchart"),
        $dotschart = $("#dotschart"),
        $placeholder = $("#placeholder");

    function initialize_page() {
        $("body").data("ittickets-initialized", true);
        $workflowchart.slideUp();
        $workflowchart.empty();
        $dotschart.empty();
        $("#emailpieholder").empty();

        var $ticketid = $("#total-tickets-popover");
        $ticketid.data('content', "This is the total number of tickets since March 2010 ("+moment("2010-03-15", "YYYY-MM-DD").fromNow()+"), including automatic messages");
        $ticketid.data("original-title", "What?");
        $ticketid.data("placement", "top");
        $ticketid.attr("rel", "popover");
        $ticketid.popover("hide");
        $ticketid.popover({"placement": popover_placement});

        $("#dots_all").addClass("active");
        $dotschart.dotsgraph({"data": ticketdata.dots.all});
        $dotschart.dotsgraph("update");

    }

    function update_data() {
        for (var key in ticketdata) {
            if ($("#" + key) != null) {
                $("#" + key).html(ticketdata[key]);
            }
        }

        $(".dots-btn").click(function() {
            if ($(this).hasClass("active")) {
                return;
            }
            $dotschart.slideDown();
            $workflowchart.slideUp();
            var dictname = $(this).data("name");
            $dotschart.dotsgraph({"data": ticketdata["dots"][dictname]});
            $dotschart.dotsgraph("update");
            $placeholder.html("mouse over the circles for more details");
            $placeholder.removeClass("hidden");
            $("#name2").addClass("hidden");
        });

        $("#change_graph").click(function() {
            $placeholder.html("mouse over the graph for more details");
            $dotschart.slideUp();
            $workflowchart.html("");
            process(ticketdata.workflow);
            $workflowchart.removeClass("hidden");
            $workflowchart.slideDown();
        });

        $("#emailpieholder").empty();
        var emailpie_values = [ticketdata.other_users, ticketdata.futurice_users],
            emailpie_labels = {legend: ["External %%.%%", "Internal %%.%%"], legendpos: "west"};
        var r = Raphael("emailpieholder", 400, 200),
            pie = r.piechart(190, 100, 69, emailpie_values, emailpie_labels);
        
        pie.hover(function () {
            this.sector.stop();
                this.sector.scale(1.1, 1.1, this.cx, this.cy);
                if (this.label) {
                    this.label[0].stop();
                    this.label[0].attr({ r: 7.5 });
                    this.label[1].attr({ "font-weight": 800 });
                }
            }, function () {
                this.sector.animate({ transform: 's1 1 ' + this.cx + ' ' + this.cy }, 500, "bounce");
                if (this.label) {
                    this.label[0].animate({ r: 5 }, 500, "bounce");
                    this.label[1].attr({ "font-weight": 400 });
                }
        });
    }
    if (from_storage) {
            if ($("body").data("ittickets-initialized") !== true) {
                initialize_page();
            }
            update_data();        
    } else {
        $.get("/ittickets.json", function(data) {
            ticketdata = data.data;
            if (localStorage) {
                localStorage.setItem("ittickets_json", JSON.stringify(ticketdata));
            }
            if ($("body").data("ittickets-initialized") !== true) {
                initialize_page();
            }
            update_data();
            $("#update_data").pagerefresh("fetch_done", (new Date()).getTime());
        });
    }
}
