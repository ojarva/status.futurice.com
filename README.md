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
network. Small python script posts network map from our internal statistics server to public one. 
Similarly RT runs on separate server. RT server sends statistics regularly with *backend/fetch_rt.py*. 
Both network map and RT statistics come in through *upload.php*. Public server fetches Pingdom statistics 
directly. That's the only time critical page - if everything something is broken on our end, network map 
and RT statistics are not working, but [services status page](http://status.futurice.com/page/services) 
shows up-to-date information.

How to install
--------------

External systems:

* Configure Pingdom
* Install and configure RT (if you want to use "IT tickets" page)
* Configure [network weathermap](http://www.network-weathermap.com/)

On server running this site:

* Install python, highlight, redis, python-redis, python-dateutil, python-twitter, apache2, libapache2-mod-php5, trimage, yui-compressor, rrdtool, python-rrdtool and make (*apt-get install python python-redis redis-server python-dateutil highlight python-twitter apache2 libapache2-mod-php5 yui-compressor make trimage rrdtool python-rrdtool*).
* Configure apache2 (*a2enmod php5 rewrite headers deflate expires*)

On your RT server:

* Move *backend/rt_settings.py.example* to *backend/rt_settings.py* and configure relevant variables
* Add *backend/fetch_rt.py* to crontab (preferrably on separate server running RT)

To this code:

* Whenever you make changes, run *make* on top directory to generate minified versions and to update application cache manifest timestamp
* Modify *pages/what.php* to match with your ideologies and technologies used.
* Add carousel (on what? page) images to *img/carousel/*. We recommend 1200x400, but you can use whatever resolution you want. UI doesn't scale images.
* Move *upload_settings.php.sample* to *upload_settings.php*. Change *$password*, and add same password to backend settings.

Backend components (*backend/*)

* Move *pingdom_settings.py.example* to *backend/pingdom_settings.py* and configure relevant variables.
* Add *fetch_pingdom.py* to crontab
* Add *fetch_twitter.py* to crontab. First argument is your twitter username.
* If your weathermap runs on separate server, run *monitor_and_upload_file.py* there.
* *printer_status.py* fetches printer status using SNMP. Configure *printer_settings.py.sample*. Requires net-snmp package.

Relevant sites/documents
------------------------

This list is just some useful documents and links used while creating this services.

* [Application cache](http://www.html5rocks.com/en/tutorials/appcache/beginner/)
* [Server-sent events](http://www.html5rocks.com/en/tutorials/eventsource/basics/) and [W3 EventSource draft](http://www.w3.org/TR/eventsource/)
* [caniuse.com](http://caniuse.com/)
* [Web notifications](http://www.w3.org/TR/notifications/)
* [Pingdom API](http://www.pingdom.com/services/api-documentation-rest/)
