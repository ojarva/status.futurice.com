// Sequence diagram for client polling: docs/clientpolling.png

function set_last_data(filename, data) {
    data = JSON.stringify(data);
    if (localStorage) {
        localStorage.setItem(filename+"-data", data);
    } else {
        $("body").data(filename+"-data", data);
    }
}

function set_last_data_timestamp(filename, data) {
    if (localStorage) {
        localStorage.setItem(filename+"-timestamp", data);
    } else {
        $("body").data(filename+"-timestamp", data);
    }
}

function get_last_data(filename) {
    var data;
    if (localStorage) {
        data = localStorage.getItem(filename+"-data");
    } else {
        data = $("body").data(filename+"-data");
    }
    if (!data) {
       return;
    }
    return JSON.parse(data);
}

function get_last_data_timestamp(filename) {
    var data;
    if (localStorage) {
        data = localStorage.getItem(filename+"-timestamp");
    } else {
        data = $("body").data(filename+"-timestamp");
    }
    if (!data) {
       data = 0;
    }
    return parseInt(data);
}


function handle_autofill(data) {
    if (!(data && data.autofill)) {
        return;
    }
    for (var key in data.autofill) {
        var $elem = $("#" + key);
        if ($elem) {
            if (data.autofill[key] != $elem.html()) {
                animate_change($elem, data.autofill[key]);
            }
        }
    }
}

function animate_change($elem, data, continueold) {
    if (!continueold && $elem.data("animate-init")) {
      return;
    }
    if (!$elem.data("animate-original-color")) {
        $elem.data("animate-original-color", $elem.css("color"));
        $elem.data("animate-original-bgcolor", $elem.css("background-color"));
    }

    if (isNaN(data)) {
        $elem.html(data);
        $elem.css("color", "#FFFDF9").css("background-color", "#FCF8E3");
        $elem.animate({color: $elem.data("animate-original-color"), "background-color": $elem.data("animate-original-bgcolor")}, 2000);
        return;
    }

    var tdata = parseFloat(data);
    if (!$elem.data("animate-init")) {
        $elem.data("animate-init", true);
        $elem.css("color", "#CCCCCC").css("background-color", "#FCF8E3");
        $elem.data("animate-target", data);
        new_data = parseFloat($elem.html());
        if (isNaN(new_data)) { new_data = 0; }
        $elem.data("animate-step", Math.max(1, (tdata - new_data) / 20));
        tdata = new_data;
    }
    tdata = Math.min($elem.data("animate-target"), Math.floor(tdata + $elem.data("animate-step")));


    if (tdata >= $elem.data("animate-target")) {
        $elem.html($elem.data("animate-target"));
        $elem.animate({color: $elem.data("animate-original-color"), "background-color": $elem.data("animate-original-bgcolor")}, 2000);
        $elem.removeData("animate-init");
        return;
    }

    $elem.html(tdata);

    setTimeout(function() { animate_change($elem, tdata, true)}, 100);
}


(function ( $) {
    var methods = {
        init : function (options) {
            var settings = $.extend( {
                'short_timeout': 5*60,
                'long_timeout': 30*60,
                'current_timeout': 5*60,
                'update_button_id': $(this).selector + '> .update_now_button',
                'spinner_id': $(this).selector + '> .update_now_button > .update_progress_indicator',
                'next_reload_id': $(this).selector + '> small > .update_next_reload',
                'refresh_callback': "fetch_data();",
                'refresh_twitter_callback': "update_twitter();",
                'ago_id': $(this).selector + '> small > .update_ago',
                'thiselem': $(this),
                'filewatch': false
            }, options);
            settings.current_timeout = settings.short_timeout;

            $(this).html('<small><span class="update_ago"></span> <span class="update_next_reload"></span></small> <button class="btn btn-small update_now_button">Update now <span class="update_progress_indicator"><img src="/img/loading-mini.gif"></span></button>');

            $(this).data("pagerefresh_settings", settings);

            $(settings.update_button_id).click(function() {
                 settings.thiselem.pagerefresh("fetch");
            });


            if (!$("body").data(settings.filewatch+"-localstorage-loaded")) {
                $("body").data(settings.filewatch+"-localstorage-loaded", true);
                data = get_last_data(settings.filewatch);
                if (data && data.content) {
                    $("body").data("pagerefresh-data", data);
                    eval(settings.refresh_callback);
                    settings.thiselem.pagerefresh("autofill");
                    settings.thiselem.pagerefresh("fetch_done", $("body").data("pagerefresh-data").content_timestamp*1000);
                }
                twitter = get_last_data("twitter.json");
                if (twitter && twitter.content) {
                    $("body").data("pagerefresh-twitter", twitter);
                    eval(settings.refresh_twitter_callback);
                }
            }


            if (EventSource && settings.filewatch) {
                $(this).pagerefresh("savesetting", "sse", true);
                settings.sse = true;

                $(this).pagerefresh("enableSSE", settings.thiselem);
            }

            if (settings.sse) {
                $(settings.next_reload_id).data("reload-timestamp", (new Date()).getTime() + settings.long_timeout * 1000);
            } else {
                $(settings.next_reload_id).data("reload-timestamp", 0);
            }

            $(window).blur(function () {
                var asettings = settings.thiselem.data("pagerefresh_settings");
                if (asettings.sse && asettings.thiselem.data("sserunning")) {
                    $(this).pagerefresh("disableSSE", settings.thiselem);
                } 
                var next_reload = $(settings.next_reload_id).data("reload-timestamp");
                if (next_reload) {
                    var max_timeout = (new Date()).getTime() + settings.long_timeout * 1000 + settings.short_timeout * 1000;
                    var proposed_timeout = next_reload + (settings.long_timeout * 1000);
                    $(settings.next_reload_id).data("reload-timestamp", Math.min(max_timeout, proposed_timeout));
                } else {
                    $(settings.next_reload_id).data("reload-timestamp", (new Date()).getTime() + settings.long_timeout * 1000);
                }
                settings.thiselem.pagerefresh("savesetting", "current_timeout", settings.long_timeout);
            });

            $(window).focus(function () {
                var asettings = settings.thiselem.data("pagerefresh_settings");
                if (asettings.sse && !settings.thiselem.data("sserunning")) {
                    $(this).pagerefresh("enableSSE", settings.thiselem);
                } else {
                    var next_reload = $(settings.next_reload_id).data("reload-timestamp");
                    if (next_reload) {
                        $(settings.next_reload_id).data("reload-timestamp", next_reload - settings.long_timeout * 1000);
                    } else {
                        $(settings.next_reload_id).data("reload-timestamp", (new Date()).getTime() + settings.short_timeout * 1000);
                    }
                    settings.thiselem.pagerefresh("savesetting", "current_timeout", settings.short_timeout);
                }
            });

            $(this).pagerefresh("update");
        },

        disableSSE : function (element) {
            var ssesource = element.data("ssesource");
            if (ssesource) {
                ssesource.close();
                element.data("sserunning", false);
            }
        }, 

        enableSSE : function (element) {
            var settings = element.data("pagerefresh_settings");
            var source = new EventSource("/sse.php?file="+settings.filewatch);
            settings.thiselem.data("sserunning", true);

            source.addEventListener('message', function(e) {
            }, false);

            source.addEventListener('changeevent', function(e) {
                var data = JSON.parse(e.data);
                settings.thiselem.data("sserunning", true);
                if (get_last_data_timestamp(settings.filewatch) < data.timestamp - 20) {
                    $(settings.next_reload_id).data("reload-timestamp", 0);
                } else {
                }
            }, false);

            source.addEventListener('manifestchange', function(e) {
                settings.thiselem.data("sserunning", true);
                try { window.window.applicationCache.update(); } catch (e) {}
            }, false);

            source.addEventListener('open', function(e) {
                settings.thiselem.data("sserunning", true);
                settings.thiselem.pagerefresh("savesetting", "sse", true);
            }, false);

            source.addEventListener('error', function(e) {
                settings.thiselem.data("sserunning", false);
                settings.thiselem.pagerefresh("savesetting", "sse", false);
            }, false);
            settings.thiselem.data("ssesource", source);
        },

        savesetting : function (key, value) {
            var settings = $(this).data("pagerefresh_settings");
            if (!settings) {
                console.log("Failed to save setting", key, " with value ", value, " using element ", $(this));
                return;
            }
            settings[key] = value;
            $(this).data("pagerefresh_settings", settings);
        },
        update : function ( ) {
            var settings = $(this).data("pagerefresh_settings");
            if (!settings) {
                return;
            }
            if (settings.timestamp) {
                $(settings.ago_id).html(moment(settings.timestamp).fromNow()+".");
            } else {
                $(settings.ago_id).html("");
            }

            var next_reload = $(settings.next_reload_id).data("reload-timestamp");
            if (settings.thiselem.data("sserunning")) {
                if (moment(next_reload) < moment()) {
                    $(settings.next_reload_id).html("Next reload right now");
                    $(this).pagerefresh("fetch");
                } else {
                    $(settings.next_reload_id).html("Next reload when new data is available");
                    $(settings.next_reload_id).data("reload-timestamp", (new Date()).getTime() + settings.current_timeout * 60 * 1000);
                }
            } else {
                if (!next_reload || moment(next_reload) < moment()) {
                    $(settings.next_reload_id).html("Next reload right now");
                    $(this).pagerefresh("fetch");
                } else {
                    $(settings.next_reload_id).html("Next reload " + moment(next_reload).fromNow());
                }
            }
            setTimeout("$('"+String(settings.thiselem.selector)+"').pagerefresh('update');", 1000);
        },
        destroy : function ( ) {
            return this.each(function () {
                var $this = $(this);
                var settings = $this.data("pagerefresh_settings");
                if (!settings) {
                    return;
                }
                $this.empty();
                $this.removeData("pagerefresh_settings");
            });
        },
        autofill : function ( ) {
            return this.each(function () {
                var $this = $(this);
                var settings = $this.data("pagerefresh_settings");
                if (!settings) {
                    return;
                }
                var data = get_last_data(settings.filewatch);
                if (data) { data = data.content; }
                handle_autofill(data);
            });
        },
        fetch: function ( ) {
            var settings = $(this).data("pagerefresh_settings");
            if (!settings) {
                console.log("No settings available (fetch)");
                return;
            }

            $(settings.next_reload_id).data("reload-timestamp", (new Date()).getTime() + settings.current_timeout * 1000);
            $(settings.spinner_id).show();
            $(settings.update_button_id).addClass("disabled");

            var url = "/json.php?filename="+settings.filewatch+"&last_data="+get_last_data_timestamp(settings.filewatch);
            $.get(url, function(data) {
                if (data.status == "success") {
                    if (data.twitter) {
                        $("body").data("pagerefresh-twitter", data.twitter);
                        set_last_data("twitter.json", data.twitter);
                        eval(settings.refresh_twitter_callback);
                    }
                    if (data.data) {
                        $("body").data("pagerefresh-data", data.data);
                        set_last_data(settings.filewatch, data.data);
                        eval(settings.refresh_callback);
                        set_last_data_timestamp(settings.filewatch, data.data.content_timestamp);
                    }
                    settings.thiselem.pagerefresh("fetch_done", $("body").data("pagerefresh-data").content_timestamp*1000);
                    settings.thiselem.pagerefresh("autofill");
                }
            }, "json");

        },
        fetch_done: function ( timestamp ) {
            $(this).pagerefresh("savesetting", "timestamp", timestamp);
            var settings = $(this).data("pagerefresh_settings");
            if (!settings) {
                console.log("No settings available (fetch_done)");
                return;
            }
            setTimeout('$("'+settings.update_button_id+'").removeClass("disabled");$("'+settings.spinner_id+'").hide();', 1000);
        }
    }

    $.fn.pagerefresh = function( method ) {
        // Method calling logic
        if ( methods[method] ) {
            return methods[ method ].apply( this, Array.prototype.slice.call( arguments, 1 ));
        } else if ( typeof method === 'object' || ! method ) {
            return methods.init.apply( this, arguments );
        } else {
            $.error( 'Method ' +  method + ' does not exist on jQuery.pagrefresh' );
        }
    };
}) ( jQuery );
