function bytesToSize(bytes) {
    var sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    if (bytes == 0) return 'n/a';
    var i = parseInt(Math.floor(Math.log(bytes) / Math.log(1024)));
    return Math.round(bytes / Math.pow(1024, i), 2) + ' ' + sizes[i];
};

function fetch_data() {

    var data = $("body").data("pagerefresh-data").content;
    var today = data["gapps"]["today"];


    $("#users").html(today["num_accounts"]);
    $("#usage").html(bytesToSize(parseInt(today["usage_in_bytes"])));
    $("#average").html(bytesToSize(parseInt(today["avg_usage_in_mb"])*1024*1024));
    $("#active14d").html(today["count_14_day_actives"]);
    /*
    for (var row in data){
        var date = data[row]["date"];
        date = date.substring(6)+"."+date.substring(4,6)+"."+date.substring(0,4);
        avg_dates.push(date);
        var users = data[row]["num_accounts"];
        var usage = bytesToSize(data[row]["usage_in_bytes"]);
        var avg = bytesToSize(parseInt(data[row]["avg_usage_in_mb"])*1024*1024);
        avg_values.push(parseInt(data[row]["avg_usage_in_mb"]));

        $("#gapptable tbody").append("<tr></tr><td>"+date+"</td><td>"+users+"</td><td>"+usage+"</td><td>"+avg+"</td></tr>");
    } */

    //TODO: Draw graphs

    var actives = parseInt(today["count_14_day_actives"]);
    var inactives = parseInt(today["num_accounts"]) - actives;
    $.jqplot('holder', [[['Active',actives], ['Inactive',inactives]]], {
                                                seriesDefaults: {renderer: jQuery.jqplot.PieRenderer,
                                                    rendererOptions: {showDataLabels: true},
                                                    shadow: false,
                                                },
                                                legend: { show:true, location: 'e' },
                                                grid: {shadow: false,
                                                    background: '#ffffff',
                                                    borderWidth: 0.0},
                                                title: 'Accounts'
    });
};

$(document).ready(function () {
    $("#update_data").pagerefresh({"short_timeout": 1*60*60, "long_timeout": 1*60*60, "filewatch": "gapps.json"});

});
