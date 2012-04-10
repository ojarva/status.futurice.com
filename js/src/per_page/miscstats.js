
String.prototype.hashCode = function(){
	var hash = 0,
            achar;
	if (this.length == 0) return hash;
	for (var i = 0; i < this.length; i++) {
		achar = this.charCodeAt(i);
		hash = ((hash<<5)-hash)+achar;
		hash = hash & hash; // Convert to 32bit integer
	}
	return hash;
}

function fetch_data() {
    function fetch_initial() {
        var items = [[localStorage, "localstorage"], [EventSource, "eventsource"], [window.applicationCache, "appcache"], [window.webkitNotifications, "notifications"]];
        for (var item in items) {
             if (items[item][0]) {
                 $("#your_browser_"+items[item][1]).html("Supported");
             } else {
                 $("#your_browser_"+items[item][1]).html("Supported");
             }
        }
    }

    if (!$("body").data("miscstats-fetch-initial-done")) {
        $("body").data("miscstats-fetch-initial-done", true);
        fetch_initial();
    }

    var graphs = [
        "?p=disk&pi=xvda1&t=disk_ops",
        "?p=load&pi=&t=load",
        "?p=interface&pi=&t=if_octets&ti=eth0",
        "?p=interface&pi=&t=if_packets&ti=eth0",
        "?p=apache&pi=foo&t=apache_requests",
        "?p=memory&pi=&t=memory"
    ];
    var commonparameters = "&h=status.futurice.com&s=86400";
    $.each(graphs, function(index, value) {
        value = "/grapher/graph.php"+value+commonparameters;
        var hash = value.hashCode();
        if ($("#"+hash).length == 0) {
            $("#graphs").append("<li class='span6'><a class='thumbnail' href='/grapher/detail.php"+value+"'><img id='"+hash+"' src='"+value+"'></a></li>");
        } else {
            $("#"+hash).attr("src", value+"&newtimestamp="+(new Date()).getTime());
        }
    });

    $.get("/get_per_user_stats.php", function(data) {
        handle_autofill(data);
    });

}

$(document).ready(function () {
    $("#update_data").pagerefresh({"short_timeout": 1*60, "long_timeout": 15*60, "filewatch": "miscstats.json"});
});
