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
                'refresh_callback': "update_twitter(); fetch_data();",
                'ago_id': $(this).selector + '> small > .update_ago',
                'thiselem': $(this),
                'filewatch': false
            }, options);
            settings.current_timeout = settings.short_timeout;

            $(this).html('<small><span class="update_ago"></span> <span class="update_next_reload"></span></small> <button class="btn btn-small update_now_button">Update now <span class="update_progress_indicator"><img src="/img/loading-mini.gif"></span></button>');

            $(this).data("pagerefresh_settings", settings);

            $(settings.next_reload_id).data("reload-timestamp", 0);

            $(settings.update_button_id).click(function() {
                 settings.thiselem.pagerefresh("fetch");
            });

            if (EventSource && settings.filewatch) {
                var source = new EventSource("/sse.php?file="+settings.filewatch);
                source.addEventListener('message', function(e) {
                }, false);

                source.addEventListener('changeevent', function(e) {
                    $(settings.next_reload_id).data("reload-timestamp", 0);
                }, false);

                source.addEventListener('manifestchange', function(e) {
                    try { window.window.applicationCache.update(); } catch (e) {}
                }, false);

                source.addEventListener('open', function(e) {
                }, false);

                source.addEventListener('error', function(e) {
                    if (e.eventPhase == EventSource.CLOSED) {
                        // Connection was closed.
                    }
                }, false);
                $(this).pagerefresh("savesetting", "sse", true);
                settings.sse = true;
            }

            if (!settings.sse) {
            $(window).blur(function () {
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
                var next_reload = $(settings.next_reload_id).data("reload-timestamp");
                if (next_reload) {
                    $(settings.next_reload_id).data("reload-timestamp", next_reload - settings.long_timeout * 1000);
                } else {
                    $(settings.next_reload_id).data("reload-timestamp", (new Date()).getTime() + settings.short_timeout * 1000);
                }
                settings.thiselem.pagerefresh("savesetting", "current_timeout", settings.short_timeout);
            });
            } // !sse

            $(this).pagerefresh("update");
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
            if (settings.sse) {
                if (moment(next_reload) < moment()) {
                    $(settings.next_reload_id).html("Next reload right now");
                    $(this).pagerefresh("fetch");
                } else {
                    $(settings.next_reload_id).html("Next reload when new data is available");
                    $(settings.next_reload_id).data("reload-timestamp", (new Date()).getTime() + settings.current_timeout * 1000);
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
        fetch: function ( ) {
            var settings = $(this).data("pagerefresh_settings");
            if (!settings) {
                console.log("No settings available (fetch)");
                return;
            }
            $(settings.next_reload_id).data("reload-timestamp", (new Date()).getTime() + settings.current_timeout * 1000);
            $(settings.spinner_id).show();
            $(settings.update_button_id).addClass("disabled");
            try {
                eval(settings.refresh_callback);
            } catch (e) { console.log("Executing callback ("+settings.refresh_callback+") failed", e); }
        },
        fetch_done: function ( timestamp ) {
            $(this).pagerefresh("savesetting", "timestamp", timestamp);
            var settings = $(this).data("pagerefresh_settings");
            if (!settings) {
                console.log("No settings available (fetch_done)");
                return;
            }
            setTimeout('$("'+settings.update_button_id+'").removeClass("disabled");$("'+settings.spinner_id+'").hide();', 1000);
        },
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
