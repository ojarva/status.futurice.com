PAGES=$(wildcard pages/*.php)
RAPHAEL_JS=$(wildcard js/src/raphael/*.js)
COMBINED_JS=$(wildcard js/src/main/*.js)
PER_PAGE_JS=$(wildcard js/src/pages/*.js)
COMBINED_CSS=$(wildcard css/src/*.css)

PER_PAGE_JS_DEST=$(PER_PAGE_JS:.js=.js.min2)
RAPHAEL_JS_DEST=$(RAPHAEL_JS:.js=.js.min)
COMBINED_JS_DEST=$(COMBINED_JS:.js=.js.min)

SOURCE_RENDER=sources/index.php.html sources/backend/fetch_pingdom.py.html sources/backend/fetch_rt.py.html

#JS_COMPILER=cat
JS_COMPILER=java -jar /var/www/closure/compiler.jar
#JS_COMPILER=yui-compressor 

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

sources/%.php.html: %.php
	cd sources; highlight --syntax php ../$< > ../$@; chmod 644 ../$@

sources/%.py.html: %.py
	cd sources; highlight --syntax py ../$< > ../$@; chmod 644 ../$@
