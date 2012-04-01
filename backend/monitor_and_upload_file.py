"""
This script monitors upload_settings.UPLOAD_FILE and uploads it after modifications
"""

from poster.encode import multipart_encode
from poster.streaminghttp import register_openers
import time
import sys
import pyinotify
import urllib2

import upload_settings

register_openers()


wm = pyinotify.WatchManager()  # Watch Manager
mask = pyinotify.IN_CLOSE_WRITE

def upload():
    try:
        datagen, headers = multipart_encode({"data": open(upload_settings.UPLOAD_FILE, "rb"), "password": upload_settings.UPLOAD_PASSWORD, "what": upload_settings.UPLOAD_DESTINATION})
        request = urllib2.Request(upload_settings.UPLOAD_URL, datagen, headers)
        urllib2.urlopen(request).read()
    except:
        pass

class EventHandler(pyinotify.ProcessEvent):
    def process_default(self, event):
        if event.maskname == pyinotify.IN_CLOSE_WRITE or event.maskname == "IN_CLOSE_WRITE":
            if event.pathname == upload_settings.UPLOAD_FILE:
                time.sleep(1)
                upload()

handler = EventHandler()
notifier = pyinotify.Notifier(wm, handler)
wdd = wm.add_watch('/var/www/weathermap', mask, rec=True)

try:
    notifier.loop(daemonize=True, pid_file='/var/run/status_uploader.pid')
except pyinotify.NotifierError, err:
    print >> sys.stderr, err
