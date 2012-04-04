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
        draw_dots_chart(ticketdata.dots.all);

        var $ticketid = $("#total-tickets-popover");
        $ticketid.data('content', "This is the total number of tickets since March 2010 ("+moment("2010-03-15", "YYYY-MM-DD").fromNow()+"), including automatic messages");
        $ticketid.data("original-title", "What?");
        $ticketid.data("placement", "top");
        $ticketid.attr("rel", "popover");
        $ticketid.popover("hide");
        $ticketid.popover({"placement": popover_placement});

        $("#dots_all").addClass("active");

    }

    function draw_dots_chart(datain) {
        $dotschart.empty();
        var r = Raphael("dotschart");
        var xs = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23],
            ys = [];
            data = datain.date_stats,
            axisy = datain.ytitles;
            axisx = datain.xtitles;
        for (var y = 0; y < 7; y++) {
            for (var i = 0; i < 24; i++) {
                ys.push(y);
            }
        }

        r.dotchart(10,10,900,300, xs, ys.reverse(), data, {symbol: "o", max: 10, heat: true, axis: "0 0 1 1", axisxstep: 23, axisystep: 6, axisxlabels: axisx, axisxtype: " ", axisytype: " ", axisylabels: axisy.reverse()}).hover(function () {
            this.marker = this.marker || r.tag(this.x, this.y, this.value, 0, this.r + 2).insertBefore(this);
            this.marker.show();
        }, function () {
            this.marker && this.marker.hide();
        });
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
            $dotschart.show(); // Show instantly, because otherwise svg chart height is 1
            $workflowchart.slideUp();

            var dictname = $(this).data("name");
            draw_dots_chart(ticketdata.dots[dictname]);

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
        $.get("/data/ittickets.json", function(data) {
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
