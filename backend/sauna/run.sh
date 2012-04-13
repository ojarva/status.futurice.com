python sauna_eta.py 70 $(rrdtool fetch /var/www/data/sauna.rrd AVERAGE -e now -s end-1800s | grep ":" | awk {'print $2'} | xargs)
