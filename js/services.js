var services_data;
var services_data_ajax;
var update_next_reload_timeout, status_timestamp_interval, update_data_timeout;

function update_next_reload(next_reload) {
 clearTimeout(update_next_reload_timeout);
 if (moment(next_reload) < moment()) {
  $("#next-reload").html("Next reload right now");
 } else {
  $("#next-reload").html("Next reload "+moment(next_reload).fromNow());
  update_next_reload_timeout = setTimeout('update_next_reload('+next_reload+');', 1000);
 }
}

function refresh_popovers() {
 var counter = 0;
 popover_contents = new Array();
 for (service in services_data.per_service) {
  counter += 1;
  ts = services_data.per_service[service];
  if (ts.lasterrortime > 0) {
   last_error_time = moment(ts.lasterrortime*1000).fromNow();
  } else {
   last_error_time = "-";
  }
  if (ts.lasttesttime > 0) {
   last_check_time = moment(ts.lasttesttime*1000).fromNow();
  } else {
   last_check_time = "-";
  }
  popover_contents[service] = '<b>Status: '+ts.status+'</b><br>Test method: '+ts.type+'<br>Test interval: '+ts.resolution+' minutes<br>Last error '+last_error_time+'<br>Last check '+last_check_time;
 }
 $(".check-popover").each(function(index) {
  $(this).data("content", popover_contents[$(this).data("service-id")]);
  $(this).popover();
 });
}
function process_data() {
 for (key in services_data.overall) {
  if ($("#"+key) != null) {
    $("#"+key).html(services_data.overall[key]);
  }
 }
 $("#checks-overview-tbody").empty();
 $("#checks-summary-tbody").empty();
 $("#status-timestamp").html(moment(services_data.overall.timestamp.unix*1000).fromNow()+".");
 clearInterval(status_timestamp_interval);
 status_timestamp_interval = setInterval('$("#status-timestamp").html(moment(services_data.overall.timestamp.unix*1000).fromNow()+".");', 1000);
 update_next_reload((new Date()).getTime() + 15 * 60 * 1000);
 broken_services = 0;
 var counter = 0;
 for (service in services_data.per_service) {
  counter += 1;
  ts = services_data.per_service[service];
  daystatus = ""
  for (a in ts.dates) {
   da = ts.dates[a];
   if (da.u > 0.999) {
     color = "green";
   } else if (da.u > 0.98) {
     color = "yellow";
   } else {
     color = "red";
   }
   if (da.u == 1) {
    popover_content = "Uptime: 100% - perfect record.";
   } else {
      popover_content = 'Uptime: '+Math.floor(100000*da.u)/1000+'%<br> Downtime: '+da.down+' seconds<br>Total uptime: '+da.up+' seconds.';
   }
   if (da.totalup == 0) {
     color = "grey";
     popover_content = "No data available. Either test was paused or it was created after this date.";
   }
   daystatus += '<td class="check-day" rel="popover" data-original-title="More information" data-content="'+popover_content+'"><span class="icon '+color+'">'+color+'</span></td>';
  }
  if (ts.status == "down") {
   broken_services++;
  }
  popover_content = "";
  $("#checks-overview-tbody").append('<tr><td class="check-status check-popover" rel="popover" data-service-id="'+service+'" data-original-title="'+ts.name+'" data-content="'+popover_content+'" data-placement="right"><span class="status '+ts['status']+'"></span></td><td class="check-name"><a target="_parent" href="http://status.futurice.com/'+service+'">'+ts["name"]+'</a></td><td style="width:50px" class="response-sparkline" id="full_table_'+service+'_sparkline" data-check-id="'+service+'"></td>'+daystatus+'</tr>');
  $("#checks-summary-tbody").append('<tr><td class="check-name"><a target="_parent" href="http://status.futurice.com/'+service+'">'+ts["name"]+'</a></td><td class="check-status check-popover" data-service-id="'+service+'" rel="popover" data-original-title="'+ts.name+'" data-content="'+popover_content+'" data-placement="right"><span class="status '+ts['status']+'"></span></td><td style="width:50px" class="response-sparkline" id="summary_table_'+service+'_sparkline" data-check-id="'+service+'"></td><td style="width:50px" class="uptime-sparkline" id="summary_table_'+service+'_uptime_sparkline" data-check-id="'+service+'"></td></tr>');
 }
 if (broken_services == 0) {
  $("#status-text").html("Everything is running normally");
 } else if (broken_services == 1) {
  $("#status-text").html("Just one service is down right now");
 } else {
  $("#status-text").html(broken_services+" services are down right now");
 }

 $(".uptime-sparkline").each(function(index) {
   paper = Raphael.fromJquery($(this));
   var data = [];
   $.each(services_data.per_service[$(this).data('check-id')].dates, function (index, item) {
    data.push(item.u);
   });
   paper.sparkline(data);
    var min = Math.min.apply(Math, data),
        max = Math.max.apply(Math, data);
    popover_content = "Highest uptime: "+Math.floor(max*100*1000)/1000+"%<br>Lowest uptime: "+Math.floor(min*100*1000)/1000+"%";
    add_popover($(this), "Uptime", popover_content);
 });
 $(".response-sparkline").each(function(index) {
    paper = Raphael.fromJquery($(this));
    var data = services_data.per_service[$(this).data('check-id')].avgms;
    paper.sparkline(data);
    var min = Math.min.apply(Math, data),
        max = Math.max.apply(Math, data);
    popover_content = "Highest response time: "+max+"ms<br>Lowest response time: "+min+"ms";
    add_popover($(this), "Response times", popover_content);
 });
 $(".check-day-title").each(function(index) {
  popover_content = "Uptime: "+services_data.overall.uptime_per_day[index]+"%";
  if (services_data.overall.outages_per_day[index] > 0) {
   popover_content += "<br>Number of outages: "+services_data.overall.outages_per_day[index]+" (even short ones count)";
  }
  $(this).html(services_data.overall.day_titles[index][2]);
  add_popover($(this), services_data.overall.day_titles[index][2], popover_content);
 });

 refresh_popovers();
 // Reload popovers
 $("[rel=popover]").popover();
 $("#progress-indicator").hide();
}

function add_popover(element, title, content) {
  element.attr("rel", "popover");
  element.attr("data-original-title", title);
  element.attr("data-content", content);
  element.popover();
}

function update_data() {
 $("#progress-indicator").show();
 $("#update_now_button").addClass("disabled");
 clearTimeout(update_data_timeout);
 $.getJSON("services.json?timestamp="+((new Date()).getTime()), function(data) {
  services_data = data;
  process_data();
  update_data_timeout = setTimeout("update_data();", 1000*60*15); // fetch data every 15 minutes
  $("#update_now_button").removeClass("disabled");
 });
}


$(document).ready(function() {
 update_data();
 setInterval("refresh_popovers();", 1000*60); // refresh popovers every minute
 $("#update_now_button").click(function() {
  update_data();
 });
});
