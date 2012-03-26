all: index.php.html fetch_pingdom.py.html fetch_rt.py.html

index.php.html: index.php
	highlight --syntax php index.php > index.php.html
	chmod 644 index.php.html

fetch_pingdom.py.html: backend/fetch_pingdom.py
	highlight --syntax python backend/fetch_pingdom.py > fetch_pingdom.py.html
	chmod 644 fetch_pingdom.py.html

fetch_rt.py.html: backend/fetch_rt.py
	highlight --syntax python backend/fetch_rt.py > fetch_rt.py.html
	chmod 644 fetch_rt.py.html

