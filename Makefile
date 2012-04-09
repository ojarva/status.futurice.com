
RAPHAEL_JS=js/r-800-raphael.js js/r-801-raphaelg.js js/r-801-raphael-sparkline.js js/r-802-raphael-impact.js js/r-803-raphael-pie.js js/r-804-raphael-dots.js js/r-805-raphael-bar.js
COMBINED_JS=js/bootstrap/000-jquery.js js/bootstrap/001-custom.js js/bootstrap/110-bootstrap-transition.js js/bootstrap/110-bootstrap-alert.js js/bootstrap/110-bootstrap-dropdown.js js/bootstrap/110-bootstrap-tab.js js/bootstrap/109-bootstrap-tooltip.js js/bootstrap/110-bootstrap-popover.js js/bootstrap/110-bootstrap-button.js js/bootstrap/110-bootstrap-collapse.js js/bootstrap/110-bootstrap-carousel.js js/300-moment.js js/700-underscore.js js/999-custom.js js/990-pagerefresh.js js/400-jquery.color.js
COMBINED_CSS=css/bootstrap.min.css css/custom.css css/bootstrap-responsive.min.css
PER_PAGE_JS=js/services.js js/miscstats.js js/printers.js js/netmap.js js/ittickets.js js/servicedetails.js
PER_PAGE_JS_DEST=$(PER_PAGE_JS:.js=.min.js)

#JS_COMPILER=cat
JS_COMPILER=java -jar /var/www/closure/compiler.jar
#JS_COMPILER=yui-compressor 

ALL_FILES=sources/index.php.html sources/fetch_pingdom.py.html sources/fetch_rt.py.html css/combined.min.css js/combined.min.js js/combined.raphael.min.js pages/main.php pages/ittickets.php pages/services.php pages/miscstats.php pages/what.php pages/netmap.php
ALL_FILES+=${PER_PAGE_JS_DEST}

all: ${ALL_FILES} cache.manifest


cache.manifest: ${ALL_FILES} cache.manifest
	sed -i s/'\# version: .*'/"\# version: `date +%s`"/ $@
	redis-cli publish "pubsub:cache.manifest" "{\"mtime\": `date +%s`, \"hash\": \"`cat $@ | md5sum | awk {'print $1'}`\"}"



css/combined.min.css: css/combined.css Makefile
	yui-compressor $< > $@.tmp
	mv $@.tmp $@
	chmod 644 $@

css/combined.css: ${COMBINED_CSS} Makefile
	cat ${COMBINED_CSS} > $@
	chmod 644 $@

js/combined.raphael.min.js: js/combined.raphael.js Makefile
	${JS_COMPILER} $< > $@.tmp
	mv $@.tmp $@
	chmod 644 $@

js/combined.raphael.js: ${RAPHAEL_JS} Makefile
	cat ${RAPHAEL_JS} > $@
	chmod 644 $@

js/services.min.js: js/services.js Makefile
	${JS_COMPILER} $< > $@.tmp
	mv $@.tmp $@
	chmod 644 $@

js/miscstats.min.js: js/miscstats.js Makefile
	${JS_COMPILER} $< > $@.tmp
	mv $@.tmp $@
	chmod 644 $@

js/servicedetails.min.js: js/servicedetails.js Makefile
	${JS_COMPILER} $< > $@.tmp
	mv $@.tmp $@
	chmod 644 $@

js/printers.min.js: js/printers.js Makefile
	${JS_COMPILER} $< > $@.tmp
	mv $@.tmp $@
	chmod 644 $@

js/netmap.min.js: js/netmap.js Makefile
	${JS_COMPILER} $< > $@.tmp
	mv $@.tmp $@
	chmod 644 $@

js/ittickets.min.js: js/ittickets.js Makefile
	${JS_COMPILER} $< > $@.tmp
	mv $@.tmp $@
	chmod 644 $@

js/main.min.js: js/main.js Makefile
	${JS_COMPILER} $< > $@.tmp
	mv $@.tmp $@
	chmod 644 $@

js/combined.min.js: js/combined.js Makefile
	${JS_COMPILER} $< > $@.tmp
	mv $@.tmp $@
	chmod 644 $@

js/combined.js: ${COMBINED_JS} Makefile
	cat ${COMBINED_JS} > $@
	chmod 644 $@

sources/index.php.html: index.php Makefile
	cd sources; highlight --syntax php ../$< > ../$@; chmod 644 ../$@

sources/fetch_pingdom.py.html: backend/fetch_pingdom.py Makefile
	cd sources; highlight --syntax py ../$< > ../$@; chmod 644 ../$@

sources/fetch_rt.py.html: backend/fetch_rt.py Makefile
	cd sources; highlight --syntax py ../$< > ../$@; chmod 644 ../$@

