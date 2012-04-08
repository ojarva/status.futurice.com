
String.prototype.hashCode = function(){
	var hash = 0;
	if (this.length == 0) return hash;
	for (i = 0; i < this.length; i++) {
		achar = this.charCodeAt(i);
		hash = ((hash<<5)-hash)+achar;
		hash = hash & hash; // Convert to 32bit integer
	}
	return hash;
}

function fetch_data() {
    var graphs = [
        "?p=disk&pi=xvda1&t=disk_ops&h=status.futurice.com&s=86400",
        "?p=load&pi=&t=load&h=status.futurice.com&s=86400",
        "?p=interface&pi=&t=if_octets&ti=eth0&h=status.futurice.com&s=86400",
        "?p=interface&pi=&t=if_packets&ti=eth0&h=status.futurice.com&s=86400",
        "?p=apache&pi=foo&t=apache_requests&h=status.futurice.com&s=86400",
        "?p=memory&pi=&t=memory&h=status.futurice.com&s=86400"
    ];
    $.each(graphs, function(index, value) {
        var hash = value.hashCode();
        if ($("#"+hash).length == 0) {
            $("#graphs").append("<li class='span6'><a class='thumbnail' href='/grapher/detail.php"+value+"'><img id='"+hash+"' src='/grapher/graph.php"+value+"'></a></li>");
        } else {
            $("#"+hash).attr("src", "/grapher/graph.php"+value+"&newtimestamp="+(new Date()).getTime());
        }
    });

    $.get("/get_per_user_stats.php", function(data) {
        handle_autofill(data);
    });

}

$(document).ready(function () {
    $("#update_data").pagerefresh({"short_timeout": 1*60, "long_timeout": 15*60, "filewatch": "miscstats.json"});
});
