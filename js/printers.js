function fetch_data(from_localstorage) {

    function process_data() {
        var data = $("body").data("printers_data");
        $("#printers").empty();
        $("#printers_accordion").empty();
        $("#printers_consumables").empty();
        $("#printers_papers").empty();

        var counter = 0;
        for (var printerid in data.printers) {
            counter++;
            var printer = data.printers[printerid];
            var status_label = "";
            if (printer.alert_level.readable == "warning") {
                status_label = '<span class="label label-warning">Warning</span>';
            } else if (printer.alert_level.readable == "unknown") {
                status_label = '<span class="label label-default">Unknown</span>';
            } else if (printer.alert_level.readable == "running") {
                status_label = '<span class="label label-success">Ok</span>';
            } else if (printer.alert_level.readable == "invalid") {
                status_label = '<span class="label label-default">Unknown</span>';
            } else if (printer.alert_level.readable == "down") {
                status_label = '<span class="label label-important">Down</span>';
            } else if (printer.alert_level.readable == "testing") {
                status_label = '<span class="label label-info">Testing</span>';
            }
            var status_texts = "<ul>";
            if (printer.alert_text.length > 0) {
                for (var item in printer.alert_text) {
                     status_texts += "<li>"+printer.alert_text[item]+"</li>";
                }
            } else {
                status_texts += "<li>Everything is fine.</li>";
            }
            status_texts += "</ul>";

            collapse_id = "printers_collapse_"+counter;
            var printer_activity = "<span class='badge'>"+printer.status.readable+"</span>";
//            $("#printers").append('<div class="row" style="padding-top: 2em"><div class="span8"><h2>'+printer.name+' '+status_label+' '+printer_activity+'</h2>'+status_texts+'</div></div>');

            //consumables
            var con_status_texts = '<table class="table-striped">';
            var con_status_texts_front = '<table class="table-striped">';
            for (var item in printer.consumables) {
                var consumable = printer.consumables[item],
                    progress_class = "progress-danger";
                if (consumable.percentage > 50) { progress_class = "progress-success"; }
                else if (consumable.percentage > 25) { progress_class = "progress-warning"; }
                con_status_texts += "<tr><td style='padding-right:15px'>"+consumable.name+"</td><td style='width:100px'><div style='margin-bottom: 3px' class='progress "+progress_class+"'><div class='bar' style='width: "+consumable.percentage+"%'></div></div></td><td style='padding-left: 15px'><small>"+consumable.percentage+"%</small></tr>";
                if (consumable.percentage < 60) { 
                    con_status_texts_front += "<tr><td style='padding-right:15px'>"+consumable.name+"</td><td style='width:100px'><div style='margin-bottom: 3px' class='progress "+progress_class+"'><div class='bar' style='width: "+consumable.percentage+"%'></div></div></td><td style='padding-left: 15px'><small>"+consumable.percentage+"%</small></tr>";
                }
            }
            con_status_texts += "</table>";
            con_status_texts_front += "</table>";
            $("#printers_consumables").append('<div class="row" style="padding-top: 2em"><div class="span8"><h2>'+printer.name+' '+status_label+' '+printer_activity+'</h2>'+con_status_texts+'</div></div>');


            // Papers
            var pap_status_texts = '<table class="table-striped">';
            var pap_status_texts_front = '<table class="table-striped">';
            for (var item in printer.papers) {
                var paper = printer.papers[item],
                    progress_class = "progress-danger";
                if (paper.percentage > 50) { progress_class = "progress-success"; }
                else if (paper.percentage > 25) { progress_class = "progress-warning"; }
                pap_status_texts += "<tr><td style='padding-right:15px'>"+paper.name+"</td><td style='width:100px'><div style='margin-bottom: 3px' class='progress "+progress_class+"'><div class='bar' style='width: "+paper.percentage+"%'></div></div></td><td style='padding-left: 15px'><small>"+paper.percentage+"%</small></td></tr>";
                if (paper.percentage < 50) {
                    pap_status_texts_front += "<tr><td style='padding-right:15px'>"+paper.name+"</td><td style='width:100px'><div style='margin-bottom: 3px' class='progress "+progress_class+"'><div class='bar' style='width: "+paper.percentage+"%'></div></div></td><td style='padding-left: 15px'><small>"+paper.percentage+"%</small></td></tr>";
                }
            }
            pap_status_texts += "</table>";
            pap_status_texts_front += "</table>";
            $("#printers_papers").append('<div class="row" style="padding-top: 2em"><div class="span8"><h2>'+printer.name+' '+status_label+' '+printer_activity+'</h2>'+pap_status_texts+'</div></div>');

            $("#printers_accordion").append('            <div class="accordion-group"> ' +
'              <div class="accordion-heading"> ' +
'<h2><a style="text-decoration:none" class="accordion-toggle" data-toggle="collapse" data-parent="#printers_accordion" href="#'+collapse_id+'">'+printer.name+' '+status_label+' '+printer_activity+'</a></h2> ' +
 status_texts +
'              </div> ' +
'              <div id="'+collapse_id+'" class="accordion-body collapse"> ' +
'                <div class="accordion-inner"> ' +
'                    <h3>Consumables</h3> ' +
                    con_status_texts_front +
'                    <h3>Paper</h3> ' +
                    pap_status_texts_front +
'                </div> ' +
'              </div> ' +
'            </div>');



        }
    } // End of process_data()


    if (from_localstorage) {
        var data = $("body").data("printers_json");
        $("#update_data").pagerefresh("fetch_done", data.timestamp.unix * 1000);
        process_data();
    } else {
      $.getJSON("/printers.json?timestamp="+Math.floor((new Date()).getTime() / 100), function(data) {
        try {
            var old_timestamp = $("body").data("printers_data").timestamp;
            if (old_timestamp == data.overall.timestamp.unix) {
                $("#update_data").pagerefresh("fetch_done", data.timestamp * 1000);
                return;
            }
        } catch (e) { }
        if (localStorage) {
            localStorage.setItem("printers_json", JSON.stringify(data));
        }
        $("body").data("printers_data", data);
        process_data();
        $("#update_data").pagerefresh("fetch_done", data.timestamp*1000);
      });
    }
}

$(document).ready(function() {
    $("#update_data").pagerefresh({"short_timeout": 1*60, "long_timeout": 15*60, "filewatch": "printers.json"});

    if (localStorage) {
        var printers_temp = localStorage.getItem("printers_json");
        if (printers_temp != null) {
            try {
                printers_temp = JSON.parse(printers_temp);
                $("body").data("printers_data", printers_temp);
                fetch_data(true);
            } catch (e) {}
        }
    }

});

