$(document).ready(function () {
    var onlinestatus = window.navigator.onLine,
        key;
    if (onlinestatus !== false) {
        onlinestatus = true;
    }
    if (!onlinestatus) {
        $("#notify-box").append("<div class='alert alert-block'><a class='close' data-dismiss='alert'>×</a><h4 class='alert-heading'>Running in offline mode</h4>Your browser is in offline mode, and this page comes from application cache. Data shown in these pages is not up-to-date or it might not ever load.</div>");
    }
    $("#reload-button").data("action", "update");
    try {
        $("#reload-button").click(function() {
            if ($(this).data("action") == "update") {
                $("#reload-button").data("pressed", true);
                check_appcache_update();
            } else {
                window.location.reload();
            }
            return false;
        });
     } catch (e) {}
});

function check_appcache_update() {
    try {
        window.applicationCache.update();
    } catch (e) {}
}


// Check if a new cache is available on page load.
window.addEventListener('load', function(e) {

    window.applicationCache.addEventListener('updateready', function(e) {
        if (window.applicationCache.status == window.applicationCache.UPDATEREADY) {
            // Browser downloaded a new app cache.
            // Swap it in and reload the page
            try {
                window.applicationCache.swapCache(); // Bug with firefox.
            } catch (e) {}
            $("#cache-status").show();
            $("#reload-button").html("New version available");
            $("#reload-button").data("action", "reload");
            $("#reload-button").removeClass("disabled");
            if (confirm('A new version of this site is available. Load it?')) {
                window.location.reload();
            }
        } else {
            // Manifest didn't changed. Nothing new to server.
        }
    }, false);
}, false);


try {
    window.applicationCache.addEventListener("progress", function(e) {
        $("#reload-button").html("Downloading...");
        $("#cache-update-status").show();
        $("#cache-update-status > .progress > .bar").css("width", (e.loaded / e.total*100)+"%");
        if (e.loaded == e.total) {
            $("#cache-update-status").hide();
        }
    }, false);

    window.applicationCache.addEventListener("cached", function(e) {
        $("#reload-button").html("Page cached");
        $("#reload-button").removeClass("disabled");
    }, false);
    window.applicationCache.addEventListener("obsolete", function(e) {
        if (confirm("You're running old version. Do you want to reload now?")) {
            window.location.reload();
        }
        $("#reload-button").html("Obsolete version");
        $("#reload-button").removeClass("disabled");
        $("#reload-button").data("action", "reload");
    }, false);
    window.applicationCache.addEventListener("noupdate", function(e) {
        $("#reload-button").html("No update available");
        setTimeout('$("#reload-button").html("Check for updates")', 1000);
        if ($("#reload-button").data("pressed")) {
            $("#next-reload").data("reload-timestamp", 0);
            $("#reload-button").data("pressed", false);
        }
        $("#reload-button").removeClass("disabled");
    }, false);

    window.applicationCache.addEventListener("checking", function(e) {
        $("#reload-button").addClass("disabled");
        $("#reload-button").html("Checking...");
    }, false);

    window.applicationCache.addEventListener("error", function(e) {
        console.log(e);
    }, false);

} catch(e) {
    $("#cache-update-status").hide();
    $("#cache-status").hide();
}

jQuery.fn.urlize = function() {
    if (this.length > 0) {
        this.each(function(i, obj){
            // making links active
            var x = $(obj).html();
            var list = x.match( /\b(http:\/\/|www\.|http:\/\/www\.)[^ <]{2,200}\b/g );
            if (list) {
                for (var i = 0; i < list.length; i++ ) {
                    var prot = list[i].indexOf('http://') === 0 || list[i].indexOf('https://') === 0 ? '' : 'http://';
                    x = x.replace( list[i], "<a target='_blank' href='" + prot + list[i] + "'>"+ list[i] + "</a>" );
                }

            }
            $(obj).html(x);
        });
    }
};

function update_twitter() {
    $.get("/twitter.json", function(data) {
        $("#twitter_footer").html("<blockquote><p id='twitter_status'>"+data["status"]+"</p><small><a href='http://twitter.com/futurice'><i class='icon-retweet'></i> @futurice "+data.status_ago+"</a></small></blockquote>");
        $("#twitter_status").urlize();
    }, "json");

}

$(document).ready(function() {
    $("[rel=popover]").popover("hide");
    $("[rel=popover]").popover();
    update_twitter();
    setInterval("check_appcache_update();", 1000 * 60 * 30); // Check for new application cache twice per hour.
});
