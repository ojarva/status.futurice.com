all: index.php.html fetch_pingdom.py.html fetch_rt.py.html css/combined.min.css js/combined.min.js js/services.min.js

css/combined.min.css: css/combined.css
	yui-compress css/combined.css > css/combined.min.css
	chmod 644 css/combined.min.css

css/combined.css:
	cat css/bootstrap.min.css css/bootstrap-responsive.min.css css/custom.css > css/combined.css
	chmod 644 css/combined.css

js/services.min.js: js/services.js
	yui-compress js/services.js > js/services.min.js
	chmod 644 js/services.min.js

js/combined.min.js: js/combined.js
	yui-compress js/combined.js > js/combined.min.js
	chmod 644 js/combined.min.js

js/combined.js:
	cat js/???-*.js > js/combined.js
	chmod 644 js/combined.js

index.php.html: index.php
	highlight --syntax php index.php > index.php.html
	chmod 644 index.php.html

fetch_pingdom.py.html: backend/fetch_pingdom.py
	highlight --syntax py backend/fetch_pingdom.py > fetch_pingdom.py.html
	chmod 644 fetch_pingdom.py.html

fetch_rt.py.html: backend/fetch_rt.py
	highlight --syntax py backend/fetch_rt.py > fetch_rt.py.html
	chmod 644 fetch_rt.py.html

