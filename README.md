status.futurice.com
===================

Earlier we took Pingdom into use and published Pingdom default status page ([blog 
post](http://blog.futurice.com/public-performance-and-uptime-information)). Very soon we realized it's 
not good enough and we want to share more information on the same place. Also, Pingdom wasn't willing to 
improve public status pages, so we decided to make our own.

Want to use this?
-----------------

Feel free to! All code provided by us is licensed with BSD license. See 
LICENSE.md for more information. Some parts have other licenses, MIT and
Apache license and CC (commercial usage allowed). 

Our setup
---------

Our public status information server runs in Amazon EC2 - there's no point on running it on our own 
network. It's in our domain, but domain servers are easy to replicate. Small python script posts 
network map from our internal statistics server to public one. Similarly RT runs on separate 
server. RT server sends statistics regularly with *backend/fetch_rt.py*. Both network map and RT 
statistics come in through *upload.php*. Public server fetches Pingdom statistics directly. That's 
the only time critical page - if everything something is broken on our end, network map and RT 
statistics are not working, but [services status page](http://status.futurice.com/page/services) 
shows up-to-date information.

Basic documentation:

* [Hosted at github](https://github.com/ojarva/status.futurice.com/tree/master/docs)
* [Redis prefixes](https://github.com/ojarva/status.futurice.com/blob/master/docs/redis_key_prefixes.md)

Installation instructions
=========================

See also *docs/* directory for more information.

External systems
----------------

Configure Pingdom. Get API key from Pingdom control panel.

On server running this site
---------------------------

Install following packages: python, highlight, collectd, redis, python-imaging, python-redis, python-dateutil, python-twitter, apache2, libapache2-mod-php5, trimage, yui-compressor, rrdtool, python-rrdtool and make. In Debian/Ubuntu:

```
sudo apt-get install python-imaging collectd python python-redis redis-server python-dateutil highlight python-twitter apache2 libapache2-mod-php5 yui-compressor make trimage rrdtool python-rrdtool
```

Configure redis to offer unix socket at */home/redis/redis.sock* (or change *lib/redis.php* and *backend/* to use TCP connection instead).

Configure apache2:

```
sudo a2enmod php5 rewrite headers deflate expires
```

Install pecl_http: http://pecl.php.net/package/pecl_http

```
sudo pecl install pecl_http
```

Change PHP session handler to redis (it'll not work with default settings). In Debian/Ubuntu, */etc/php5/apache2/php.ini*:

```
session.save_handler = redis
session.save_path = "tcp://localhost:6379?prefix=phpsession:&timeout=2"
```

To this code
------------

* Whenever you make changes, run *make* on top directory to generate minified versions and to update application cache manifest timestamp
* Modify *pages/main.php* (for example company name)
* Modify *pages/what.php* to match with your ideologies and technologies used.
* Feel free to change *favicon.ico* - by default it's Futurice company logo
* Move *upload_settings.php.sample* to *upload_settings.php*. Change *$password*, and add same password to backend settings.
* *404.html*, *500.html*, *index.php*, *grapher/inc/html.inc.php*: change google analytics tracking code to yours (or just remove it).
* Optional: add carousel (on ["What?"](http://status.futurice.com/page/what) page) images to *img/carousel/*. See *img/carousel/README.md* for more information.

On your RT server
-----------------

For security reasons, it might be good idea to run RT on separate server.

* Install and configure [RT](http://bestpractical.com/rt/) (if you want to use "IT tickets" page)
* Copy *backend/rt_settings.py.example* to your RT server. Rename it to *rt_settings.py* and configure relevant variables
* Copy *backend/fetch_rt.py* to your RT server. Add it to crontab.

Network weathermap
------------------

* Configure [network weathermap](http://www.network-weathermap.com/)
* For output image, something like 900x950px is good.
* *backend/monitor_and_upload_file.py* handles file upload, if network weathermap runs on separate server (recommended).

Printer statuses
----------------

It's recommended to run printer status update from separate server - server running public status pages shouldn't have access to printers at all.

* Enable SNMP on your printers. **Some printer drivers use SNMP too - changing community might break something**.
* Don't enable write access for this script.
* *printer_status.py* fetches printer status using SNMP. Configure *printer_settings.py.sample*. Requires net-snmp package.


Backend components (*backend/*)
-------------------------------

* **Don't run any of the scripts under root**
* Move *pingdom_settings.py.example* to *backend/pingdom_settings.py* and configure relevant variables.
* Add *fetch_pingdom.py* to crontab (suggestion: every minute - fetches only current statuses every minute, other details less often)
* Add *fetch_twitter.py* to crontab. First argument is your twitter username. (suggestion: once per few minutes)
* Add *frontpage_json.py* to crontab (suggestion: every minute)
* Add *miscstats_json.py* to crontab (suggestion: every minute)
* Add *printer_graphs.py* to crontab (suggestion: every minute)

This is what we have in crontab for regular user owning all files under */var/www*:

```
* * * * * cd /var/www/backend; python fetch_pingdom.py
* * * * * cd /var/www/backend; python frontpage_json.py; python miscstats_json.py; python printer_graphs.py; cd sauna; python gen.py
*/3 * * * * cd /var/www/backend; python fetch_twitter.py futurice
```

Relevant sites/documents
========================

This list is just some useful documents and links used while creating this services.

* [Application cache](http://www.html5rocks.com/en/tutorials/appcache/beginner/)
* [Server-sent events](http://www.html5rocks.com/en/tutorials/eventsource/basics/) and [W3 EventSource draft](http://www.w3.org/TR/eventsource/)
* [caniuse.com](http://caniuse.com/)
* [Web notifications](http://www.w3.org/TR/notifications/)
* [Local storage](http://dev.w3.org/html5/webstorage/)
* [Pingdom API](http://www.pingdom.com/services/api-documentation-rest/)
