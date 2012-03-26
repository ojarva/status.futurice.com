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

How to install
--------------

* Start using Pingdom
* Install and configure RT (if you want to use "IT tickets" page)
* Install python and php. Configure apache2.
* Move backend/pingdom_settings.py.example to backend/pingdom_settings.py and configure relevant variables.
* Move backend/rt_settings.py.example to backend/rt_settings.py and configure relevant variables
* Add backend/fetch_pingdom.py to crontab
* Add backend/rt_settings.py to crontab (preferrably on separate server running RT)
* Modify pages/what.php to match with your ideologies and technologies used.
* Configure [network weathermap](http://www.network-weathermap.com/)
