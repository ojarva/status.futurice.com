all: index.php.html fetch_pingdom.py.html fetch_rt.py.html css/combined.min.css js/combined.min.js js/services.min.js js/main.min.js js/combined.raphael.min.js js/ittickets.min.js js/netmap.min.js cache.manifest


cache.manifest: css/combined.min.css js/combined.min.js js/netmap.min.js js/ittickets.min.js js/services.min.js index.php pages/ittickets.php pages/main.php pages/netmap.php pages/services.php pages/todo.php pages/what.php js/main.min.js
	sed -i s/'\# version: .*'/"\# version: `date +%s`"/ cache.manifest

css/combined.min.css: css/combined.css
	yui-compressor css/combined.css > css/combined.min.css
	chmod 644 css/combined.min.css

css/combined.css: css/bootstrap.min.css css/bootstrap-responsive.min.css css/custom.css
	cat css/bootstrap.min.css css/custom.css css/bootstrap-responsive.min.css  > css/combined.css
	chmod 644 css/combined.css

js/combined.raphael.min.js: js/combined.raphael.js
	yui-compressor js/combined.raphael.js > js/combined.raphael.min.js
	chmod 644 js/combined.raphael.min.js

js/combined.raphael.js: js/r-800-raphael.js js/r-801-raphael-sparkline.js js/r-802-raphael-impact.js js/r-803-raphael-pie.js js/r-804-raphael-dots.js 
	cat js/r-*.js > js/combined.raphael.js
	chmod 644 js/combined.raphael.js
	

js/services.min.js: js/services.js
	yui-compressor js/services.js > js/services.min.js
	chmod 644 js/services.min.js

js/netmap.min.js: js/netmap.js
	yui-compressor js/netmap.js > js/netmap.min.js
	chmod 644 js/netmap.min.js

js/ittickets.min.js: js/ittickets.js
	yui-compressor js/ittickets.js > js/ittickets.min.js
	chmod 644 js/ittickets.min.js



js/main.min.js: js/main.js
	yui-compressor js/main.js > js/main.min.js
	chmod 644 js/main.min.js

js/combined.min.js: js/combined.js
	yui-compressor js/combined.js > js/combined.min.js
	chmod 644 js/combined.min.js

js/combined.js: js/bootstrap/000-jquery.js js/bootstrap/100-bootstrap.js js/bootstrap/110-bootstrap-alert.js js/bootstrap/110-bootstrap-button.js js/bootstrap/110-bootstrap-carousel.js js/bootstrap/110-bootstrap-collapse.js js/bootstrap/110-bootstrap-dropdown.js js/bootstrap/110-bootstrap-popover.js js/bootstrap/109-bootstrap-tooltip.js js/bootstrap/110-bootstrap-transition.js js/300-moment.js js/700-underscore.js js/999-custom.js js/990-pagerefresh.js
	cat js/bootstrap/000-jquery.js  js/bootstrap/110-bootstrap-transition.js js/bootstrap/110-bootstrap-alert.js js/bootstrap/110-bootstrap-modal.js js/bootstrap/110-bootstrap-dropdown.js js/bootstrap/110-bootstrap-scrollspy.js js/bootstrap/110-bootstrap-tab.js js/bootstrap/109-bootstrap-tooltip.js js/bootstrap/110-bootstrap-popover.js js/bootstrap/110-bootstrap-button.js js/bootstrap/110-bootstrap-collapse.js js/bootstrap/110-bootstrap-carousel.js js/bootstrap/110-bootstrap-typeahead.js > js/combined.js
	cat js/???-*.js >> js/combined.js
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

