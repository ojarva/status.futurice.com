function popover_placement(popover, container) {
    var $container = $(container),
        height = $(window).height(),
        width = $(window).width(),
        offsetleft = $container.offset().left,
        offsettop = $container.offset().top,
        placements = {};
    var spaceleft = offsetleft,
        spaceright = width - offsetleft,
        spacetop = offsettop,
        spacebottom = height - offsettop,
        max = 0,
        best = false;

    if (spacetop > 150) {
        placements["top"] = spacetop;
        if (spaceleft < 150 || spaceright < 150) {
            placements["top"] = Math.min(spaceleft, spaceright);
        }
    }
    if (spacebottom > 150) {
        placements["bottom"] = spacebottom;
        if (spaceleft < 150 || spaceright < 150) {
            placements["bottom"] = Math.min(spaceleft, spaceright);
        }
    }
    if (spaceleft > 250) {
        placements["left"] = spaceleft / 2;
    }
    if (spaceright > 250) {
        placements["right"] = spaceright / 2;
    }
    best = "bottom";
    for (var item in placements) {
        if (placements[item] > max) {
            max = placements[item];
            best = item;
        }
    }
    return best;
}

