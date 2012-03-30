(function( $ ) {
    var data = [],
        axisx = [],
        axisy = [];

    var methods = {
        init : function (options) {
            return $(this).each(function() {
                $(this).data("dotsgraph_data", options["data"]);
                var axisx = options.data.xtitles,
                    axisy = options.data.ytitles;
                if (! $(this).data("dotsgraph_settings")) {
                    // Draw
                    var width = 800,
                        height = 300,
                        leftgutter = 30,
                        bottomgutter = 20,
                        r = Raphael("dotschart", width, height),
                        txt = {"font": '10px Fontin-Sans, Arial', stroke: "none", fill: "#000"},
                        X = (width - leftgutter) / axisx.length,
                        Y = (height - bottomgutter) / axisy.length,
                        color = $("#chart").css("color"),
                        max = Math.round(X / 2) - 1;
                    var dotsgraph_settings = {"width": width, "height": height, "leftgutter": leftgutter, "bottomgutter": bottomgutter, "r": r, "txt": txt, "X": X, "Y": Y, "color": color, "max": max};
                    $(this).data("dotsgraph_settings", dotsgraph_settings);
                    // Draw axis
                    for (var i = 0, ii = axisx.length; i < ii; i++) {
                        var tmptext = r.text(0, 294, axisx[i]).attr(txt);
                        tmptext.animate({x: leftgutter + X * (i + .5), y: 294}, 2180, "bounce");
                    }
                    for (var i = 0, ii = axisy.length; i < ii; i++) {
                        var tmptext = r.text(10, 0, axisy[i]).attr(txt);
                        tmptext.animate({x: 10, y: Y * (i + .5)}, 2050, "bounce");
                    }
                }
            });
        },
        destroy: function () {

        },
        update: function() {
            return $(this).each(function() {
                var dgs = $(this).data("dotsgraph_settings"),
                    width = dgs.width,
                    height = dgs.height,
                    leftgutter = dgs.leftgutter,
                    bottomgutter = dgs.bottomgutter,
                    r = dgs.r,
                    txt = dgs.txt,
                    X = dgs.X,
                    Y = dgs.Y,
                    color = dgs.color,
                    max = dgs.max,
                    dgd = $(this).data("dotsgraph_data"),
                    xaxis = dgd.xtitles,
                    yaxis = dgd.ytitles,
                    data = dgd.date_stats,
                    o = 0,
                    circleinAnimation = Raphael.animation({opacity: 1}, 750, "easeIn"),
                    circleoutAnimation = Raphael.animation({opacity: 1}, 1500, "easeOut");
                // i == y axis index
                // j == x axis index
                // o == data array index
                // R == circle diameter

                for (var i = 0, ii = dgd.ytitles.length; i < ii; i++) {
                    for (var j = 0, jj = dgd.xtitles.length; j < jj; j++) {
                        var Rtmp = max,
                            R = data[o] && Math.min(Math.round(Math.sqrt(data[o] / Math.PI / 13) * 4), max),
                            dttmp = r.circle(leftgutter + X * (j + .5) - 60 - R + 60 + R, Y * (i + .5) - 10 + 10, max+2).attr({stroke:"none", fill: "#fff", opacity: 0});
                        dttmp.animate(circleoutAnimation.delay(dgd.ytitles.length*dgd.xtitles.length - o * 10)); //{"opacity": 1}, 1500, "easeOut");
                        if (R) {
                            (function (dx, dy, R, value) {
                                var color = "hsb(" + [(1 - R / max) * .5, 1, .75] + ")",
                                    dt = r.circle(dx + 60 + R, dy + 10, R).attr({stroke: "none", fill: color, opacity: 0});
                                dt.animate(circleinAnimation.delay((o % 24)*70 + (o % 24) * 20));
                                if (R < 6) {
                                    var bg = r.circle(dx + 60 + R, dy + 10, 6).attr({stroke: "none", fill: "#00f", opacity: .4}).hide();
                                }
                                var lbl = r.text(dx + 60 + R, dy + 10, data[o])
                                        .attr({"font": '18px Fontin-Sans, Arial', stroke: "none", fill: "#000"}).hide(),
                                    dot = r.circle(dx + 60 + R, dy + 10, max).attr({stroke: "none", fill: "#00f", opacity: 0});
                                dot[0].onmouseover = function () {
                                    if (bg) {
                                        bg.show();
                                    } else {
                                        var clr = Raphael.rgb2hsb(color);
                                        clr.b = .5;
                                        dt.attr("fill", Raphael.hsb2rgb(clr).hex);
                                    }
                                    lbl.show();
                                };
                                dot[0].onmouseout = function () {
                                    if (bg) {
                                        bg.hide();
                                    } else {
                                        dt.attr("fill", color);
                                    }
                                    lbl.hide();
                                };
                            })(leftgutter + X * (j + .5) - 60 - R, Y * (i + .5) - 10, R, data[o]);
                        }
                        o++;
                    }
                }
            });
        }
    }


    $.fn.dotsgraph = function( method ) {
    
        if ( methods[method] ) {
            return methods[method].apply( this, Array.prototype.slice.call( arguments, 1 ));
        } else if ( typeof method === 'object' || ! method ) {
            return methods.init.apply( this, arguments );
        } else {
            $.error( 'Method ' +  method + ' does not exist on jQuery.tooltip' );
        }    
    };
})( jQuery );
