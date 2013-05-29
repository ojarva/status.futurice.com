# Author: Mike Babineau <mikeb@ea2d.com>
# Copyright 2011 Electronic Arts Inc.
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import base64
import gzip
import logging
import StringIO
import sys
import urllib
import urllib2
import time

try:
    import json
except:
    import simplejson as json

from pingdom.resources import PingdomCheck
from pingdom.resources import PingdomContact
from pingdom.exception import PingdomError


class PingdomRequest(urllib2.Request):
    def __init__(self, connection, resource, post_data=None, method=None, enable_gzip=True):
        """Representation of a Pingdom API HTTP request.
        
        :type connection: :class:`PingdomConnection`
        :param connection: Pingdom connection object populated with a username, password and base URL
        
        :type resource: string
        :param resource: Pingdom resource to query (in all lowercase)
        
        :type post_data: dict
        :param post_data: Data to be sent with a POST request
        
        :type method: string
        :param method: HTTP verb (GET, POST, DELETE, etc.) to use (defaults to GET or POST, depending on the presence of post_data)
        
        :type enable_gzip: bool
        :param enable_gzip: Whether or not to gzip the request (thus telling Pingdom to gzip the response)
        """
        url = connection.base_url + '/' + resource
        
        if post_data:
            if not method: method = 'POST'
            data = urllib.urlencode(post_data)
            urllib2.Request.__init__(self, url, data)
        else:
            if not method: method = 'GET'
            urllib2.Request.__init__(self, url)
        
        # Trick to support DELETE, PUT, etc.
        if method not in ['GET', 'POST']:
            self.get_method = lambda: '%s' % method
        
        # Add auth header
        base64string = base64.encodestring('%s:%s' % (connection.username, connection.password)).replace('\n','')
        self.add_header("Authorization", "Basic %s" % base64string)

        if connection.apikey:
            self.add_header("App-Key", connection.apikey)
        
        # Enable gzip
        if enable_gzip:
            self.add_header('Accept-Encoding', 'gzip')
        
    
    def __repr__(self):
        return 'PingdomRequest: %s %s' % (self.get_method(), self.get_full_url())
        
        
    def fetch(self):
        """Execute the request."""
        try:
            response = urllib2.urlopen(self)
        except urllib2.HTTPError, e:
            raise PingdomError(e)
        else:
            return PingdomResponse(response)
        


class PingdomResponse(object):
    def __init__(self, response):
        """Representation of a Pingdom API HTTP response."""
        if response.headers.get('content-encoding') == 'gzip':
            self.data = gzip.GzipFile(fileobj=StringIO.StringIO(response.read())).read()
        else:
            self.data = response.read()

        self.headers = response.headers
        self.content = json.loads(self.data)
        
        if 'error' in self.content:
            raise PingdomError(self.content)


    def __repr__(self):
        return 'PingdomResponse: %s' % self.content.keys()

        
        
class PingdomConnection(object):
    def __init__(self, username, password, apikey = '', base_url='https://api.pingdom.com/api/2.0'):
        """Interface to the Pingdom API."""
        
        self.username = username
        self.password = password
        self.apikey = apikey
        self.base_url = base_url
    
    
    def __repr__(self):
        return "Connection:%s" % self.base_url
        
        
    def list_checks(self):
        """List all Pingdom check names"""
        pingdom_checks = self.get_all_checks()
        check_list = [i.name for i in pingdom_checks]
        return check_list
        
        
    def get_all_checks(self, check_names=None, **kwargs):
        """Get a list of Pingdom checks, optionally filtered by check name"""
        limit = int(kwargs.get("limit", 25000))
        offset = int(kwargs.get("offset", 0))
        response2 = PingdomRequest(self, 'reports.public').fetch()
        result2 = response2.content
        public_reports = set([item['checkid'] for item in result2['public']])
        response = PingdomRequest(self, 'checks?limit=%s&offset=%s' % (limit, offset)).fetch()
        result = response.content
        pingdom_checks = []
        if check_names:
            for check_name in check_names:
                pingdom_checks += [PingdomCheck(r) for r in result['checks'] if r['name'] == check_name]
        else:
            pingdom_checks += [PingdomCheck(r) for r in result['checks']]

        results_final = []
        for item in pingdom_checks:
            if item.id in public_reports:
                 results_final.append(item)
            
        return results_final

    def get_performance(self, checkid, **kwargs):
        starttime = int(kwargs.get("timefrom", 0))
        endtime = int(kwargs.get("timeto", time.time()))
        resolution = kwargs.get("resolution", "day")
        response = PingdomRequest(self, 'summary.performance/%s?from=%s&to=%s&includeuptime=true&resolution=%s' % (checkid, starttime, endtime, resolution)).fetch()
        return response

    def get_outages(self, checkid, **kwargs):
        starttime = int(kwargs.get("timefrom", 0))
        endtime = int(kwargs.get("timeto", time.time()))
        order = kwargs.get("order", "asc")
        response = PingdomRequest(self, 'summary.outage/%s?from=%s&to=%s&order=%s' % (checkid, starttime, endtime, order)).fetch()
        return response.content['summary']

    def get_alerts(self, **kwargs):
        """ Get actions (alerts). Optional keyword arguments "timefrom" and "timeto" are unix timestamps for specifying time range. "limit" is maximum number of returned elements and "offset" is offset for listing (for paging, for example). """
        starttime = int(kwargs.get("timefrom", 0))
        endtime = int(kwargs.get("timeto", time.time()))
        limit = int(kwargs.get("limit", 100))
        offset = int(kwargs.get("offset", 0))
        response = PingdomRequest(self, 'actions/?from=%s&to=%s&limit=%s&offset=%s' % (starttime, endtime, limit, offset)).fetch()
        return response.content["actions"]

    def get_check_averages(self, checkid, **kwargs):
        """ Get average of response time & uptime. Additional keyword arguments "timefrom" and "timeto" are unix timestamps for specifying time range. """
        starttime = int(kwargs.get("timefrom", 0))
        endtime = int(kwargs.get("timeto", time.time()))
        response = PingdomRequest(self, 'summary.average/%s/?includeuptime=true&bycountry=true&from=%s&to=%s' % (checkid, starttime, endtime)).fetch()
        return response.content

    
    def get_check(self, check_id):
        """Get a Pingdom check by ID"""
        response = PingdomRequest(self, 'checks/%s' % check_id).fetch()
        pingdom_check = PingdomCheck(response.content['check'])
        return pingdom_check

    
    def get_raw_check_results(self, check_id, limit=100, **kwargs):
        """Get raw check results for a specific Pingdom check by ID and limit"""
        endtime = int(kwargs("timeto", time.time()))
        starttime = int(kwargs.get("timefrom", endtime - 86400))
        limit = int(kwargs("limit", limit))
        offset = int(kwargs("offset", 0))
        response = PingdomRequest(self, 'results/%s?limit=%s&offset=%s&to=%s&from=%s' %(check_id,limit,offset,endtime,starttime)).fetch()
        return response.content['results']

    def create_check(self, name, host, check_type, **kwargs):
        """Create a Pingdom check"""
        post_data = {'name': name,
                     'host': host,
                     'type': check_type}
        for key in kwargs:
            post_data[key] = kwargs[key]

        try:
            response = PingdomRequest(self, 'checks', post_data=post_data).fetch()
        except PingdomError, e:
            logging.error(e)
        else:
            return PingdomCheck(response.content['check'])


    def modify_check(self, check_id, **kwargs):
        """Modify a Pingdom check by ID"""
        post_data = {}
        for key in kwargs:
            post_data[key] = kwargs[key]

        try:
            response = PingdomRequest(self, 'checks/%s' % check_id, post_data=post_data, method='PUT').fetch()
        except PingdomError, e:
            logging.error(e)
        else:
            return response.content['message']
    
    
    def delete_check(self, check_id):
        """Delete a Pingdom check by ID"""
        response = PingdomRequest(self, 'checks/%s' % check_id, method='DELETE').fetch()
        return response.content


    def get_all_contacts(self, **kwargs):
        """Get a list of Pingdom contacts"""
        limit = int(kwargs.get("limit", 100))
        offset = int(kwargs.get("offset", 0))
        response = PingdomRequest(self, 'contacts?limit=%s&offset=%s').fetch()
        result = response.content

        contacts = [PingdomContact(r) for r in result['contacts']]
        return contacts
