status.futurice.com
===================

Earlier we took Pingdom into use and published Pingdom default status page ([blog 
post](http://blog.futurice.com/public-performance-and-uptime-information)). Very soon we realized it's 
not good enough and we want to share more information on the same place. Also, Pingdom wasn't willing to 
improve public status pages, so we decided to make our own.

Want to use this?
-----------------

Feel free to! All code provided by us is licensed with BSD license. See LICENSE.md for more information.
Some parts are licensed with GPL, for example [icon set by Alexandra Wolska](http://handdrawing.olawolska.com/).


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

* Install python and php. Configure apache2.
* Install highlight (Debian/Ubuntu package "highlight")
* Install yui-compressor (after making changes to css/js, run make on top directory to create minified versions)

On your RT server:

* Move *backend/rt_settings.py.example* to *backend/rt_settings.py* and configure relevant variables
* Add *backend/fetch_rt.py* to crontab (preferrably on separate server running RT)

To this code:

* Modify *pages/what.php* to match with your ideologies and technologies used.
* Move *backend/pingdom_settings.py.example* to *backend/pingdom_settings.py* and configure relevant variables.
* Add *backend/fetch_pingdom.py* to crontab
* Add *upload_settings.php* with <?$password="some_randomly_generated_password";?>. Put this password to *rt_settings.py* too
