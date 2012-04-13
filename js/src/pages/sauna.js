/*global jQuery */
/*!	
* FitText.js 1.0
*
* Copyright 2011, Dave Rupert http://daverupert.com
* Released under the WTFPL license 
* http://sam.zoy.org/wtfpl/
*
* Date: Thu May 05 14:23:00 2011 -0600
*/

(function( $ ){
	
$.fn.fitText = function( kompressor, options ) {
    var settings = {
        'minFontSize' : Number.NEGATIVE_INFINITY,
        'maxFontSize' : Number.POSITIVE_INFINITY
    };
    return this.each(function(){
        var $this = $(this); // store the object
        var compressor = kompressor || 1; // set the compressor
        if ( options ) { 
            $.extend( settings, options );
        }
        // Resizer() resizes items based on the object width divided by the compressor * 10
        var resizer = function () {
            var fontsize = Math.max(Math.min($this.width() / (compressor*10), parseFloat(settings.maxFontSize)), parseFloat(settings.minFontSize));

            $this.css('font-size', fontsize);
            $this.css("line-height", fontsize+"px");
        };
        // Call once to set.
        resizer();
        // Call on resize. Opera debounces their resize by default. 
        $(window).resize(resizer);
    });
};
})( jQuery );

function fetch_data() {
    var data = $("body").data("pagerefresh-data").content;
    $("#bigtext").fitText(0.5, {"minFontSize": 30, "maxFontSize": 300});
    $("#etacalc").html("");
    if (data.autofill.sauna_trend == "warming") {
        for (key in data.sauna_eta_temperatures) {
             var sauna_value = data.sauna_eta_temperatures[key];
             if (sauna_value[1] > 0 && sauna_value[1] < 7200) {
                 $("#etacalc").html(Math.floor(sauna_value[1] / 60) + " minutes to "+ sauna_value[0] + "&deg;C");
             }
        }
    }
    $("#temperature_graph").attr("src", "/graph_sauna.php?newtimestamp="+(new Date()).getTime());
}

$(document).ready(function () {
    $("#bigtext").fitText(0.5, {"minFontSize": 30, "maxFontSize": 300});
    $("#update_data").pagerefresh({"short_timeout": 1*60, "long_timeout": 15*60, "filewatch": "sauna.json"});
});
