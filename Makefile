# Source files
PAGES=$(wildcard pages/*.php)
RAPHAEL_JS=$(wildcard js/src/raphael/*.js)
COMBINED_JS=$(wildcard js/src/main/*.js)
PER_PAGE_JS=$(wildcard js/src/pages/*.js)
COMBINED_CSS=$(wildcard css/src/*.css)

# Destination files
PER_PAGE_JS_DEST=$(PER_PAGE_JS:.js=.js.min2)
RAPHAEL_JS_DEST=$(RAPHAEL_JS:.js=.js.min)
COMBINED_JS_DEST=$(COMBINED_JS:.js=.js.min)

# Render source codes
SOURCE_RENDER=sources/index.php.html sources/backend/fetch_pingdom.py.html sources/backend/fetch_rt.py.html sources/backend/miscstats_json.py.html sources/backend/frontpage_json.py.html sources/backend/fetch_twitter.py.html sources/backend/printer_graphs.py.html sources/backend/printer_status.py.html sources/sauna.php.html sources/graph/sauna.php.html sources/json.php.html sources/upload.php.html sources/staticserve.php.html sources/carousel_images.php.html sources/get_per_user_stats.php.html

PNG_FILES=$(wildcard img/*.png)

# cat makes debugging easier
#JS_COMPILER=cat
# closure breaks javascript in android browser
#JS_COMPILER=java -jar /var/www/closure/compiler.jar
JS_COMPILER=yui-compressor 


ALL_FILES=index.php css/combined.min.css js/combined.min.js js/combined.raphael.min.js
ALL_FILES+=${PAGES}
ALL_FILES+=${PER_PAGE_JS_DEST}
ALL_FILES+=${SOURCE_RENDER}

all: ${ALL_FILES} cache.manifest

clean:
	find . -name \*.tmp -delete

fullclean: clean
	find sources/ -name \*.html -delete
	find . -name \*.js.min -delete
	find . -name \*.js.min2 -delete

imagepack: ${PNG_FILES}


img/%.png:
	advpng -z4 $@


# update cache manifest serial
cache.manifest: ${ALL_FILES}
	sed -i s/'\# version: .*'/"\# version: `date +%s`"/ $@
	redis-cli publish "pubsub:cache.manifest" "{\"mtime\": `date +%s`, \"hash\": \"`cat $@ | md5sum | awk {'print $1'}`\"}"


css/combined.min.css: css/combined.css
	yui-compressor $< > $@.tmp
	mv $@.tmp $@
	chmod 644 $@

css/combined.css: ${COMBINED_CSS}
	cat ${COMBINED_CSS} > $@.tmp
	mv $@.tmp $@
	chmod 644 $@

js/src/%.js.min: js/src/%.js
	${JS_COMPILER} $< > $@.tmp
	mv $@.tmp $@


js/src/pages/%.js.min2: js/src/pages/%.js
	${JS_COMPILER} $< > $@.tmp
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

# Older versions of highlight can't autodetect php/python.
sources/%.php.html: %.php
	cd sources; highlight --syntax php ../$< > ../$@; chmod 644 ../$@

sources/%.py.html: %.py
	cd sources; highlight --syntax py ../$< > ../$@; chmod 644 ../$@
