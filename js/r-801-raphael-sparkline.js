Raphael.fromJquery = function ($obj) {
   var obj = $obj.get(0),
       width = 50, //obj.scrollWidth,
       height = 30; //obj.scrollHeight;
   return Raphael($obj.attr('id'), width, height);
};

Raphael.fn.sparkline = function (data) {
    var paper = this,
        min = Math.min.apply(Math, data),
        max = Math.max.apply(Math, data),
        graph_opts = {
            padding: {
                top: 5,
                left: 5,
                bottom: 5,
                right: 5
            },
        },
        graph_width = paper.width - graph_opts.padding.left - graph_opts.padding.right,
        graph_height = paper.height - graph_opts.padding.top - graph_opts.padding.bottom,
        padding = graph_opts.padding.left;

    var to_coords = function(value, idx) {
        var step = (graph_width / (data.length-1));
        return {
            y:  -((value-min)/(max-min) * graph_height) + graph_height + graph_opts.padding.top,
            x: padding + idx*step
        };
    };

    var prev_pt;

    _.each(data, function(item, idx) {
        var pt = to_coords(item, idx);

        if (item===max || item===min) {
            paper.circle(pt.x, pt.y, 1).attr({stroke: '#F00' }).toFront();
        }
        if (idx===0 || idx===data.length-1) {
            paper.circle(pt.x, pt.y, 1).attr({stroke: '#00F' }).toFront();
        }

        if (prev_pt) {
            var path = Raphael.format("M{0},{1}L{2},{3}z", prev_pt.x, prev_pt.y, pt.x, pt.y);
            paper.path(path).attr({stroke: '#666', 'stroke-width': 0.5});
        }
        prev_pt = pt;
    });
};
