RAPHAEL_JS=js/src/raphael/r-800-raphael.js js/src/raphael/r-801-raphaelg.js js/src/raphael/r-805-raphael-bar.js js/src/raphael/r-805-raphael-dots.js js/src/raphael/r-805-raphael-impact.js js/src/raphael/r-805-raphael-pie.js js/src/raphael/r-805-raphael-sparkline.js
COMBINED_JS=js/src/main/005-jquery.js js/src/main/010-custom.js js/src/main/100-bootstrap.js js/src/main/110-bootstrap-transition.js js/src/main/111-bootstrap-alert.js js/src/main/112-bootstrap-dropdown.js js/src/main/113-bootstrap-tab.js js/src/main/114-bootstrap-tooltip.js js/src/main/115-bootstrap-popover.js js/src/main/116-bootstrap-button.js js/src/main/117-bootstrap-collapse.js js/src/main/118-bootstrap-carousel.js js/src/main/300-moment.js js/src/main/400-jquery.color.js js/src/main/700-underscore.js js/src/main/990-pagerefresh.js js/src/main/999-custom.js
COMBINED_CSS=css/src/bootstrap.min.css css/src/custom.css css/src/bootstrap-responsive.min.css

PER_PAGE_JS=js/src/per_page/ittickets.js  js/src/per_page/main.js  js/src/per_page/miscstats.js  js/src/per_page/netmap.js  js/src/per_page/printers.js  js/src/per_page/servicedetails.js  js/src/per_page/services.js
PER_PAGE_JS_DEST=$(PER_PAGE_JS:.js=.min2.js)

RAPHAEL_JS_DEST=$(RAPHAEL_JS:.js=.min.js)
COMBINED_JS_DEST=$(COMBINED_JS:.js=.min.js)

#JS_COMPILER=cat
JS_COMPILER=java -jar /var/www/closure/compiler.jar
#JS_COMPILER=yui-compressor 

ALL_FILES=sources/index.php.html sources/fetch_pingdom.py.html sources/fetch_rt.py.html css/combined.min.css js/combined.min.js js/combined.raphael.min.js pages/main.php pages/ittickets.php pages/services.php pages/miscstats.php pages/what.php pages/netmap.php
ALL_FILES+=${PER_PAGE_JS_DEST}

all: ${ALL_FILES} cache.manifest


cache.manifest: ${ALL_FILES}
	sed -i s/'\# version: .*'/"\# version: `date +%s`"/ $@
	redis-cli publish "pubsub:cache.manifest" "{\"mtime\": `date +%s`, \"hash\": \"`cat $@ | md5sum | awk {'print $1'}`\"}"


css/combined.min.css: css/combined.css Makefile
	yui-compressor $< > $@.tmp
	mv $@.tmp $@
	chmod 644 $@

css/combined.css: ${COMBINED_CSS} Makefile
	cat ${COMBINED_CSS} > $@
	chmod 644 $@

js/src/%.min.js: js/src/%.js
	${JS_COMPILER} js/src/$*.js > $@.tmp
	mv $@.tmp $@

js/src/per_page/%.min2.js: js/src/per_page/%.js
	${JS_COMPILER} js/src/per_page/$*.js > $@.tmp
	mv $@.tmp $@
	cp $@ js/$*.min.js
	chmod 644 js/$*.min.js

js/combined.raphael.min.js: ${RAPHAEL_JS_DEST}
	cat ${RAPHAEL_JS_DEST} > $@.tmp
	mv $@.tmp $@
	chmod 644 $@

js/combined.min.js: ${COMBINED_JS_DEST}
	cat ${COMBINED_JS_DEST} > $@.tmp
	mv $@.tmp $@
	chmod 644 $@

sources/index.php.html: index.php Makefile
	cd sources; highlight --syntax php ../$< > ../$@; chmod 644 ../$@

sources/fetch_pingdom.py.html: backend/fetch_pingdom.py Makefile
	cd sources; highlight --syntax py ../$< > ../$@; chmod 644 ../$@

sources/fetch_rt.py.html: backend/fetch_rt.py Makefile
	cd sources; highlight --syntax py ../$< > ../$@; chmod 644 ../$@
