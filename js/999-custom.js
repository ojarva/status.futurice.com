$(document).ready(function () {
    var onlinestatus = window.navigator.onLine,
        key;
    if (onlinestatus !== false) {
        onlinestatus = true;
    }
    if (!onlinestatus) {
        $("#notify-box").append("<div class='alert alert-block'><a class='close' data-dismiss='alert'>×</a><h4 class='alert-heading'>Running in offline mode</h4>Your browser is in offline mode, and this page comes from application cache. Data shown in these pages is not up-to-date or it might not ever load.</div>");
    }
});


// Check if a new cache is available on page load.
window.addEventListener('load', function(e) {

  window.applicationCache.addEventListener('updateready', function(e) {
    if (window.applicationCache.status == window.applicationCache.UPDATEREADY) {
      // Browser downloaded a new app cache.
      // Swap it in and reload the page to get the new hotness.
      window.applicationCache.swapCache();
      if (confirm('A new version of this site is available. Load it?')) {
        window.location.reload();
      }
    } else {
      // Manifest didn't changed. Nothing new to server.
    }
  }, false);

}, false);

try {
 applicationCache;
 setInterval("applicationCache.update();", 1000*60*60);
} catch(e) {

}

jQuery.fn.urlize = function() {
    if (this.length > 0) {
        this.each(function(i, obj){
            // making links active
            var x = $(obj).html();
            var list = x.match( /\b(http:\/\/|www\.|http:\/\/www\.)[^ <]{2,200}\b/g );
            if (list) {
                for ( i = 0; i < list.length; i++ ) {
                    var prot = list[i].indexOf('http://') === 0 || list[i].indexOf('https://') === 0 ? '' : 'http://';
                    x = x.replace( list[i], "<a target='_blank' href='" + prot + list[i] + "'>"+ list[i] + "</a>" );
                }

            }
            $(obj).html(x);
        });
    }
};

$(document).ready(function() {
$("[rel=popover]").popover();

$.get("/twitter.json", function(data) {
$("#twitter_footer").html("<blockquote><p id='twitter_status'>"+data["status"]+"</p><small><a href='http://twitter.com/futurice'><i class='icon-retweet'></i> @futurice "+data.status_ago+"</a></small></blockquote>");
$("#twitter_status").urlize();
}, "json");

});
