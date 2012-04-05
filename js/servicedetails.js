// from http://stackoverflow.com/a/901144/592174
function getParameterByName(name) {
    name = name.replace(/[\[]/, "\\\[").replace(/[\]]/, "\\\]");
    var regexS = "[\\?&]" + name + "=([^&#]*)";
    var regex = new RegExp(regexS);
    var results = regex.exec(window.location.search);
    if (results == null) {
        return "";
    } else {
        return decodeURIComponent(results[1].replace(/\+/g, " "));
    }
}

function automatic_moment_update() {
    $(".automatic-moment").each(function () {
        var data = $(this).data("moment-timeout");
        if (data) {
            $(this).html(moment(data).fromNow());
        }  
    });

    setTimeout("automatic_moment_update()", 1000);
}



function fetch_data() {
    var data = $("body").data("pagerefresh-data").content;
    $("#last_error").data("moment-timeout", data.autofill.lasterrortime*1000);
    $("#last_check").data("moment-timeout", data.autofill.lasttesttime*1000);

    var per_day_up = [],
        per_day_unmonitored = [],
        per_day_downtime = [],
        per_day_response = [];
    $.each(data.per_day, function (index, value) {
        per_day_up.push(Math.floor(100*(value["uptime"]/864))/100);
        per_day_unmonitored.push(Math.floor(100*(value["unmonitored"]/864))/100);
        per_day_downtime.push(Math.floor(100*(value["downtime"]/864))/100);
        per_day_response.push(value["avgresponse"]);
    });
    $("#response_graph").empty();
    $("#response_graph").css("height", 400).css("width", 1000);
    $("#uptime_graph").empty();
    $("#uptime_graph").css("height", 400).css("width", 1000);
    var r = Raphael("response_graph"),
                    fin = function () {
                        this.flag = r.popup(this.bar.x, this.bar.y, this.bar.value+"%" || "?%").insertBefore(this);
                    },
                    fin_uptime = function () {
                        this.flag = r.popup(this.bar.x, this.bar.y, this.bar.value+"ms" || "?ms").insertBefore(this);
                    },
                    fout = function () {
                        this.flag.remove();
                    };
    r.barchart(0,10,900,400, [per_day_up, per_day_unmonitored, per_day_downtime], {stacked: true}).hover(fin, fout);

    var r = Raphael("uptime_graph");
    r.barchart(0,10,900,400, [per_day_response]).hover(fin_uptime, fout);
}

$(document).ready(function () {
    var filename = "per-check-"+getParameterByName("id")+".json";
    $("#update_data").pagerefresh({"short_timeout": 1*60, "long_timeout": 15*60, "filewatch": filename});
    automatic_moment_update();
});
