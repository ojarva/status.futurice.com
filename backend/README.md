Backend components
==================

This folder includes backend components for updating relevant data. These are not available through web server.
*.htaccess* file is denying access, if it's enabled in apache (or any other web server).

What to do with these?
----------------------

* *fetch_rt.py* - this script fetches ["IT tickets" page](http://status.futurice.com/page/it-tickets) data directly from RT database. RT API wasn't good enough, and using database directly seemed like a good idea.
* *fetch_pingdom.py* - fetches Pingdom data through rather good Pingdom API.
* *fetch_twitter.py* - fetches information from Twitter. Give twitter username as first argument (*python fetch_twitter.py futurice*). Add this to crontab.
* *monitor_and_upload_file.py* - if your weathermap generation runs on separate server, this script can be used to post image to status page. *upload_settings.py.example* is example configuration file for this.
* *cache/* - cached JSON files from *fetch_pingdom.py*
* *../upload.php* receiver script for network map images and *fetch_rt.py* script.

