import redis
import hashlib
import json
from poster.encode import multipart_encode
from poster.streaminghttp import register_openers
import gapps_settings
#Import the Google Apps Manager
from gam import *

'''
This class need the Google Apps Manager to function.
https://code.google.com/p/google-apps-manager/

Run this script once a day to update the usage statistics.
'''

class Gappstats:
      
    def get_report_data(self, report):
        '''
        Function for getting csv reports from google.
        Modified from the original function in GAM.
        '''
        rep = getRepObject()
        try_count = 0
        wait_on_fail = .5
        while try_count < 10:
          try:
            report_data = rep.retrieve_report(report=report)
            break
          except gdata.apps.service.AppsForYourDomainException, e:
            terminating_error = checkErrorCode(e)
            if not terminating_error:
              try_count = try_count + 1
              if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
              time.sleep(wait_on_fail)
              wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
              continue
            elif e.error_code == 600 and e[0]['reason'] == 'Bad Request':
              sys.stderr.write('Error: Bad request - No report by that name\n')
              sys.exit(e.error_code)
            else:
              sys.stderr.write('Error: %s\n' % terminating_error)
              sys.exit(e.error_code)
        if try_count == 10:
          sys.stderr.write('Giving up\n')
          return
        return report_data
       
    def getDiskSpace(self):
        '''
        Get disk usage stats and return them as a list.
        '''
        data = self.get_report_data('disk_space')
        if data is not None:
            data =  data.split()
            fields = data[0].split(',')[:6]
            i=0
            space = []
            for row in data:
                if i>0:
                    newrow = {}
                    row=row.split(',')
                    j=0
                    for field in fields:
                        newrow[field]=row[j]
                        j+=1
                    space.append(newrow)
                i+=1
            return space
            
            
    def getActivity(self):
        '''
        Get activity stats and return as list.
        '''
        data = self.get_report_data('activity')
        if data is not None:
            data =  data.split()
            fields = data[0].split(',')
            i=0
            activity = []
            for row in data:
                if i>0:
                    newrow = {}
                    row=row.split(',')
                    j=0
                    for field in fields:
                        newrow[field]=row[j]
                        j+=1
                    activity.append(newrow)
                i+=1
            return activity

    
            
    def run(self):
        disk = self.getDiskSpace()
        activity = self.getActivity()
        
        items = {}
        
        for disk_item in disk:
            for activity_item in activity:
                if disk_item["date"] == activity_item["date"]:
                    item = dict(disk_item.items() + activity_item.items())
                    items[disk_item["date"]] = item
        
        items["today"] = items[max(items, key=int)]
        register_openers()
        
        data = {"gapps": items, "timestamp": time.time()}
        jsonfile="gapps.json"
        json.dump(data, open(jsonfile, "w"))
        send(gapps_settings.UPLOAD_DESTINATION, jsonfile)
        
def send(what, filename):
    datagen, headers = multipart_encode({"data": open(filename, "rb"), "password": gapps_settings.UPLOAD_PASSWORD, "what": what})
    request = urllib2.Request(gapps_settings.UPLOAD_URL, datagen, headers)
    urllib2.urlopen(request).read()
    
def main():
    miscstats = Gappstats()
    miscstats.run()

if __name__ == '__main__':
    main()