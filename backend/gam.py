#!/usr/bin/env python
#
# Google Apps Manager
#
# Copyright 2012 Dito, LLC All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Google Apps Manager (GAM) is a command line tool which allows Administrators to control their Google Apps domain and accounts.

With GAM you can programatically create users, turn on/off services for users like POP and Forwarding and much more.
For more information, see http://code.google.com/p/google-apps-manager

"""

__author__ = 'jay@ditoweb.com (Jay Lee)'
__version__ = '2.55'
__license__ = 'Apache License 2.0 (http://www.apache.org/licenses/LICENSE-2.0)'

import sys, os, time, datetime, random, cgi, socket, urllib, urllib2, csv, getpass, platform, re, webbrowser, pickle, calendar, struct
import xml.dom.minidom
from sys import exit
import gdata.apps.service
import gdata.apps.emailsettings.service
import gdata.apps.adminsettings.service
import gdata.apps.groups.service
import gdata.apps.audit.service
try:
  import gdata.apps.adminaudit.service
except ImportError:
  pass
import gdata.apps.multidomain.service
import gdata.apps.orgs.service
import gdata.apps.res_cal.service
import gdata.calendar
import gdata.calendar.service
import gdata.apps.groupsettings.service
import gdata.apps.reporting.service
import gdata.auth
import atom
import gdata.contacts
import gdata.contacts.service
from hashlib import sha1

def showUsage():
  doGAMVersion()
  print '''
Usage: gam [OPTIONS]...

Google Apps Manager. Retrieve or set Google Apps domain,
user, group and alias settings. Exhaustive list of commands
can be found at: http://code.google.com/p/google-apps-manager/wiki

Examples:
gam info domain
gam create user jsmith firstname John lastname Smith password secretpass
gam update user jsmith suspended on
gam.exe update group announcements add member jsmith
...

'''

def getGamPath():
  if os.name == 'windows' or os.name == 'nt':
    divider = '\\'
  else:
    divider = '/'
  return os.path.dirname(os.path.realpath(sys.argv[0]))+divider

def doGAMVersion():
  print 'Google Apps Manager %s\r\n%s\r\nPython %s.%s.%s %s-bit %s\r\n%s %s' % (__version__, __author__,
                   sys.version_info[0], sys.version_info[1], sys.version_info[2], struct.calcsize('P')*8,
                   sys.version_info[3], platform.platform(), platform.machine())

def doGAMCheckForUpdates():
  if os.path.isfile(getGamPath()+'noupdatecheck.txt'): return
  if os.path.isfile(getGamPath()+'lastupdatecheck.txt'):
    f = open(getGamPath()+'lastupdatecheck.txt', 'r')
    last_check_time = int(f.readline())
    f.close()
  else:
    last_check_time = 0
  now_time = calendar.timegm(time.gmtime())
  one_week_ago_time = now_time - 604800
  if last_check_time > one_week_ago_time: return
  try:
    c = urllib2.urlopen('https://gam-update.appspot.com/latest-version.txt?v=%s' % __version__)
    try:
      latest_version = float(c.read())
    except ValueError:
      return
    current_version = float(__version__)
    if latest_version <= current_version:
      f = open(getGamPath()+'lastupdatecheck.txt', 'w')
      f.write(str(now_time))
      f.close()
      return
    a = urllib2.urlopen('https://gam-update.appspot.com/latest-version-announcement.txt')
    announcement = a.read()
    sys.stderr.write(announcement)
    visit_gam = raw_input("\n\nHit Y to visit the GAM website and download the latest release. Hit Enter to just continue with this boring old version. GAM won't bother you with this announcemnt for 1 week or you can create a file named noupdatecheck.txt in the same location as gam.py or gam.exe and GAM won't ever check for updates: ")
    if visit_gam.lower() == 'y':
      webbrowser.open('http://google-apps-manager.googlecode.com')
      print 'GAM is now exiting so that you can overwrite this old version with the latest release'
      sys.exit(0)
    f = open(getGamPath()+'lastupdatecheck.txt', 'w')
    f.write(str(now_time))
    f.close()
  except urllib2.HTTPError:
    return
  except urllib2.URLError:
    return

def commonAppsObjInit(appsObj):
  #Identify GAM to Google's Servers
  appsObj.source = 'Google Apps Manager %s / %s / Python %s.%s.%s %s / %s %s /' % (__version__, __author__,
                   sys.version_info[0], sys.version_info[1], sys.version_info[2],
                   sys.version_info[3], platform.platform(), platform.machine())
  #Show debugging output if debug.gam exists
  if os.path.isfile(getGamPath()+'debug.gam'):
    appsObj.debug = True
  return appsObj

def checkErrorCode(e):
  if e[0]['body'][:34] == 'Required field must not be blank: ' or e[0]['body'][:34] == 'These characters are not allowed: ':
    return e[0]['body']
  if e.error_code == 600 and e[0]['body'] == 'Quota exceeded for the current request' or e[0]['reason'] == 'Bad Gateway': 
    return False
  if e.error_code == 600 and e[0]['reason'] == 'Token invalid - Invalid token: Token disabled, revoked, or expired.':
    return '403 - Token disabled, revoked, or expired. Please delete and re-create oauth.txt'
  if e.error_code == 1000: # UnknownError
    return False
  elif e.error_code == 1001: # ServerBusy
    return False
  elif e.error_code == 1002:
    return '1002 - Unauthorized and forbidden'
  elif e.error_code == 1100:
    return '1100 - User deleted recently'
  elif e.error_code == 1200:
    return '1200 - Domain user limit exceeded'
  elif e.error_code == 1201:
    return '1201 - Domain alias limit exceeded'
  elif e.error_code == 1202:
    return '1202 - Domain suspended'
  elif e.error_code == 1203:
    return '1203 - Domain feature unavailable'
  elif e.error_code == 1300:
    if e.invalidInput != '':
      return '1300 - Entity %s exists' % e.invalidInput
    else:
      return '1300 - Entity exists'
  elif e.error_code == 1301:
    if e.invalidInput != '':
      return '1301 - Entity %s Does Not Exist' % e.invalidInput
    else:
      return '1301 - Entity Does Not Exist'
  elif e.error_code == 1302:
    return '1302 - Entity Name Is Reserved'
  elif e.error_code == 1303:
    if e.invalidInput != '':
      return '1303 - Entity %s name not valid' % e.invalidInput
    else:
      return '1303 - Entity name not valid'
  elif e.error_code == 1306:
    if e.invalidInput != '':
      return '1306 - %s has members. Cannot delete.' % e.invalidInput
    else:
      return '1306 - Entity has members. Cannot delete.'
  elif e.error_code == 1400:
    return '1400 - Invalid Given Name'
  elif e.error_code == 1401:
    return '1401 - Invalid Family Name'
  elif e.error_code == 1402:
    return '1402 - Invalid Password'
  elif e.error_code == 1403:
    return '1403 - Invalid Username'
  elif e.error_code == 1404:
    return '1404 - Invalid Hash Function Name'
  elif e.error_code == 1405:
    return '1405 - Invalid Hash Digest Length'
  elif e.error_code == 1406:
    return '1406 - Invalid Email Address'
  elif e.error_code == 1407:
    return '1407 - Invalid Query Parameter Value'
  elif e.error_code == 1408:
    return '1408 - Invalid SSO Signing Key'
  elif e.error_code == 1500:
    return '1500 - Too Many Recipients On Email List'
  elif e.error_code == 1501:
    return '1501 - Too Many Nicknames For User'
  elif e.error_code == 1502:
    return '1502 - Too Many Delegates For User'
  elif e.error_code == 1601:
    return '1601 - Duplicate Destinations'
  elif e.error_code == 1602:
    return '1602 - Too Many Destinations'
  elif e.error_code == 1603:
    return '1603 - Invalid Route Address'
  elif e.error_code == 1700:
    return '1700 - Group Cannot Contain Cycle'
  elif e.error_code == 1800:
    return '1800 - Invalid Domain Edition'
  elif e.error_code == 1801:
    if e.invalidInput != '':
      return '1801 - Invalid value %s' % e.invalidInput
    else:
      return '1801 - Invalid Value'
  else:
    return '%s: Unknown Error: %s' % (e.error_code, str(e))

def tryOAuth(gdataObject):
  global domain
  oauth_filename = 'oauth.txt'
  try:
    oauth_filename = os.environ['OAUTHFILE']
  except KeyError:
    pass
  if os.path.isfile(getGamPath()+oauth_filename):
    oauthfile = open(getGamPath()+oauth_filename, 'rb')
    domain = oauthfile.readline()[0:-1]
    try:
      token = pickle.load(oauthfile)
      oauthfile.close()
    except ImportError: # Deals with tokens created by windows on old GAM versions. Rewrites them with binary mode set
      oauthfile = open(getGamPath()+oauth_filename, 'r')
      domain = oauthfile.readline()[0:-1]
      try:
        token = pickle.load(oauthfile)
        oauthfile.close()
        f = open(getGamPath()+oauth_filename, 'wb')
        f.write('%s\n' % (domain,))
        pickle.dump(token, f)
        f.close()
      except ImportError: # Deals with stupid issue where gdata and atom were copied inside existing folder for awhile and pickle got confused on token creation. Rewrites token.
        oauthfile = open(getGamPath()+oauth_filename, 'r')
        domain = oauthfile.readline()[0:-1]
        token_string = oauthfile.read()
        oauthfile.close()
        token_string = token_string.replace('gdata.gdata', 'gdata')
        token = pickle.loads(token_string)
        f = open(getGamPath()+oauth_filename, 'wb')
        f.write('%s\n' % (domain,))
        pickle.dump(token, f)
        f.close()
    gdataObject.domain = domain
    gdataObject.SetOAuthInputParameters(gdata.auth.OAuthSignatureMethod.HMAC_SHA1, consumer_key=token.oauth_input_params._consumer.key, consumer_secret=token.oauth_input_params._consumer.secret)
    token.oauth_input_params = gdataObject._oauth_input_params
    gdataObject.SetOAuthToken(token)
    return True
  else:
    return False

def getAppsObject():
  apps = gdata.apps.service.AppsService()
  if not tryOAuth(apps):
    doRequestOAuth()
    tryOAuth(apps)
  apps = commonAppsObjInit(apps)
  return apps

def getProfilesObject():
  profiles = gdata.contacts.service.ContactsService(contact_list='domain')
  profiles.ssl = True
  if not tryOAuth(profiles):
    doRequestOAuth()
    tryOAuth(profiles)
  profiles = commonAppsObjInit(profiles)
  return profiles

def getCalendarObject():
  calendars = gdata.calendar.service.CalendarService()
  calendars.ssl = True
  if not tryOAuth(calendars):
    doRequestOAuth()
    tryOAuth(calendars)
  calendars = commonAppsObjInit(calendars)
  return calendars

def getGroupSettingsObject():
  groupsettings = gdata.apps.groupsettings.service.GroupSettingsService()
  if not tryOAuth(groupsettings):
    doRequestOAuth()
    tryOAuth(groupsettings)
  groupsettings = commonAppsObjInit(groupsettings)
  return groupsettings

def getEmailSettingsObject():
  emailsettings = gdata.apps.emailsettings.service.EmailSettingsService()
  if not tryOAuth(emailsettings):
    doRequestOAuth()
    tryOAuth(emailsettings)
  emailsettings = emailsettings = commonAppsObjInit(emailsettings)
  return emailsettings

def getAdminSettingsObject():
  global domain
  adminsettings = gdata.apps.adminsettings.service.AdminSettingsService()
  if not tryOAuth(adminsettings):
    doRequestOAuth()
    tryOAuth(adminsettings)
  adminsettings = commonAppsObjInit(adminsettings)
  return adminsettings
  
def getGroupsObject():
  global domain
  groupsObj = gdata.apps.groups.service.GroupsService()
  if not tryOAuth(groupsObj):
    doRequestOAuth()
    tryOAuth(groupsObj)
  groupsObj = commonAppsObjInit(groupsObj)
  return groupsObj

def getAuditObject():
  auditObj = gdata.apps.audit.service.AuditService()
  if not tryOAuth(auditObj):
    doRequestOAuth()
    tryOAuth(auditObj)
  auditObj = commonAppsObjInit(auditObj)
  return auditObj

def getAdminAuditObject():
  try:
    adminAuditObj = gdata.apps.adminaudit.service.AdminAuditService()
  except AttributeError:
    print "gam audit admin commands require Python 2.6 or 2.7"
    sys.exit(3)
  if not tryOAuth(adminAuditObj):
    doRequestOAuth()
    tryOAuth(adminAuditObj)
  adminAuditObj = commonAppsObjInit(adminAuditObj)
  return adminAuditObj

def getMultiDomainObject():
  multidomainObj = gdata.apps.multidomain.service.MultiDomainService()
  if not tryOAuth(multidomainObj):
    doRequestOAuth()
    tryOAuth(multidomainObj)
  multidomainObj = commonAppsObjInit(multidomainObj)
  return multidomainObj

def getOrgObject():
  orgObj = gdata.apps.orgs.service.OrganizationService()
  if not tryOAuth(orgObj):
    doRequestOAuth()
    tryOAuth(orgObj)
  orgObj = commonAppsObjInit(orgObj)
  return orgObj

def getResCalObject():
  resCalObj = gdata.apps.res_cal.service.ResCalService()
  if not tryOAuth(resCalObj):
    doRequestOAuth()
    tryOAuth(resCalObj)
  resCalObj = commonAppsObjInit(resCalObj)
  return resCalObj

def getRepObject():
  repObj = gdata.apps.reporting.service.ReportService()
  if not tryOAuth(repObj):
    doRequestOAuth()
    tryOAuth(repObj)
  repObj = commonAppsObjInit(repObj)
  return repObj

def _reporthook(numblocks, blocksize, filesize, url=None):
    base = os.path.basename(url)
    #XXX Should handle possible filesize=-1.
    try:
        percent = min((numblocks*blocksize*100)/filesize, 100)
    except:
        percent = 100
    if numblocks != 0:
        sys.stdout.write("\b"*70)
    sys.stdout.write(str(percent)+'% ')
    #print str(percent)+"%\b\b"

def geturl(url, dst):
    if sys.stdout.isatty():
        urllib.urlretrieve(url, dst,
                           lambda nb, bs, fs, url=url: _reporthook(nb,bs,fs,url))
        sys.stdout.write('\n')
    else:
        urllib.urlretrieve(url, dst)

def showReport():
  report = sys.argv[2].lower()
  date = page = None
  if len(sys.argv) > 3:
    date = sys.argv[3]
  rep = getRepObject()
  try_count = 0
  wait_on_fail = .5
  while try_count < 10:
    try:
      report_data = rep.retrieve_report(report=report, date=date)
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
    sys.exit(e.error_code)
  sys.stdout.write(report_data)

def doDelegates(users):
  emailsettings = getEmailSettingsObject()
  if sys.argv[4].lower() == 'to':
    delegate = sys.argv[5].lower()
    #delegate needs to be a full email address, tack
    #on domain of 1st user if there isn't one
    if not delegate.find('@') > 0:
      delegate_domain = domain.lower()
      delegate_email = '%s@%s' % (delegate, delegate_domain)
    else:
      delegate_domain = delegate[delegate.find('@')+1:].lower()
      delegate_email = delegate
  else:
    showUsage()
    exit(6)
  count = len(users)
  i = 1
  for delegator in users:
    if delegator.find('@') > 0:
      delegator_domain = delegator[delegator.find('@')+1:].lower()
      delegator_email = delegator
      delegator = delegator[:delegator.find('@')]
    else:
      delegator_domain = domain.lower()
      delegator_email = '%s@%s' % (delegator, delegator_domain)
    emailsettings.domain = delegator_domain
    print "Giving %s delegate access to %s (%s of %s)" % (delegate_email, delegator_email, i, count)
    i = i + 1
    delete_alias = False
    if delegate_domain == delegator_domain:
      use_delegate_address = delegate_email
    else:
      # Need to use an alias in delegator domain, first check to see if delegate already has one...
      multi = getMultiDomainObject()
      try_count = 0
      wait_on_fail = .5
      hard_fail = False
      while try_count < 10:
        try:
          aliases = multi.GetUserAliases(delegate_email)
          break
        except gdata.apps.service.AppsForYourDomainException, e:
          terminating_error = checkErrorCode(e)
          if not terminating_error:
            try_count = try_count + 1
            if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
            time.sleep(wait_on_fail)
            wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
            continue
          else:
            sys.stderr.write('Error: %s\n' % terminating_error)
            hard_fail = True
            break
      if try_count == 10 or hard_fail:
        sys.stderr.write('Giving up\n')
        continue
      found_alias_in_delegator_domain = False
      for alias in aliases:
        alias_domain = alias['aliasEmail'][alias['aliasEmail'].find('@')+1:].lower()
        if alias_domain == delegator_domain:
          use_delegate_address = alias['aliasEmail']
          print '  Using existing alias %s for delegation' % use_delegate_address
          found_alias_in_delegator_domain = True
          break
      if not found_alias_in_delegator_domain:
        delete_alias = True
        use_delegate_address = '%s@%s' % (''.join(random.sample('abcdefghijklmnopqrstuvwxyz0123456789', 10)), delegator_domain)
        print '  Giving %s temporary alias %s for delegation' % (delegate_email, use_delegate_address)
        try_count = 0
        wait_on_fail = .5
        hard_fail = False
        while try_count < 10:
          try:
            multi.CreateAlias(user_email=delegate_email, alias_email=use_delegate_address)
            break
          except gdata.apps.service.AppsForYourDomainException, e:
            terminating_error = checkErrorCode(e)
            if not terminating_error:
              try_count = try_count + 1
              if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
              time.sleep(wait_on_fail)
              wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
              continue
            else:
              sys.stderr.write('Error: %s\n' % terminating_error)
              hard_fail = True
              break
        if try_count == 10 or hard_fail:
          sys.stderr.write('Giving up\n')
          continue
        time.sleep(5)
    try_count = 0
    wait_on_fail = .5
    hard_fail = False
    while try_count < 10:
      try:
        emailsettings.CreateDelegate(delegate=use_delegate_address, delegator=delegator)
        break
      except gdata.apps.service.AppsForYourDomainException, e:
        terminating_error = checkErrorCode(e)
        if not terminating_error:
          if try_count == 0:
            get_try_count = 0
            get_wait_on_fail = .5
            get_hard_fail = False
            while get_try_count < 10:
              try:
                get_delegates = emailsettings.GetDelegates(delegator=delegator)
                break
              except gdata.apps.service.AppsForYourDomainException, get_e:
                get_terminating_error = checkErrorCode(get_e)
                if not get_terminating_error:
                  get_try_count = get_try_count + 1
                  if get_try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(get_e.error_code), get_try_count, str(get_wait_on_fail)))
                  time.sleep(get_wait_on_fail)
                  get_wait_on_fail = get_wait_on_fail * 2 if get_wait_on_fail < 32 else 60
                  continue
                else:
                  sys.stderr.write('Error: %s\n' % get_terminating_error)
                  get_hard_fail = True
                  break
            if get_try_count == 10 or get_hard_fail:
              sys.stderr.write('Giving up\n')
              continue
            for get_delegate in get_delegates:
              if get_delegate['address'].lower() == delegate_email: # Delegation is already in place
                if delete_alias:
                  print '  Deleting temporary alias...'
                  doDeleteNickName(alias_email=use_delegate_address)
                sys.exit(0) # Emulate functionality of duplicate delegation between users in same domain, returning clean

            #Check if either user account is suspended or requires password change
            multi = getMultiDomainObject()
            prov_try_count = 0
            prov_wait_on_fail = .5
            while prov_try_count < 10:
              try:
                delegate_user_details = multi.RetrieveUser(delegate_email)
                delegator_user_details = multi.RetrieveUser(delegator_email)
                break
              except gdata.apps.service.AppsForYourDomainException, prov_e:
                prov_terminating_error = checkErrorCode(prov_e)
                if not prov_terminating_error:
                  prov_try_count = prov_try_count + 1
                  if prov_try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(prov_e.error_code), prov_try_count, str(prov_wait_on_fail)))
                  time.sleep(prov_wait_on_fail)
                  prov_wait_on_fail = prov_wait_on_fail * 2 if prov_wait_on_fail < 32 else 60
                  continue
                else:
                  sys.stderr.write('Error: %s\n' % prov_terminating_error)
                  sys.exit(prov_e.error_code)
            if prov_try_count == 10:
              sys.stderr.write('Giving up\n')
              sys.exit(prov_e.error_code)
            if delegate_user_details['isSuspended'] == 'true':
              sys.stderr.write('Error: User %s is suspended. You must unsuspend for delegation.\n' % delegate_email)
              sys.exit(5)
            if delegator_user_details['isSuspended'] == 'true':
              sys.stderr.write('Error: User %s is suspended. You must unsuspend for delegation.\n' % delegator_email)
              sys.exit(5)
            if delegate_user_details['isChangePasswordAtNextLogin'] == 'true':
              sys.stderr.write('Error: User %s is required to change password at next login. You must change password or clear changepassword flag for delegation.\n' % delegate_email)
              sys.exit(5)
            if delegator_user_details['isChangePasswordAtNextLogin'] == 'true':
              sys.stderr.write('Error: User %s is required to change password at next login. You must change password or clear changepassword flag for delegation.\n' % delegator_email)
              sys.exit(5)
          try_count = try_count + 1
          if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
          time.sleep(wait_on_fail)
          wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
          continue
        else:
          sys.stderr.write('Error: %s\n' % terminating_error)
          hard_fail = True
          break
    if try_count == 10 or hard_fail:
      sys.stderr.write('Giving up\n')
      continue
    time.sleep(10)
    if delete_alias:
      print '  Deleting temporary alias...'
      doDeleteNickName(alias_email=use_delegate_address)
  
def getDelegates(users):
  emailsettings = getEmailSettingsObject()
  csv_format = False
  try:
    if sys.argv[5].lower() == 'csv':
      csv_format = True
  except IndexError:
    pass
  for user in users:
    if user.find('@') > 0:
      emailsettings.domain = user[user.find('@')+1:]
      user = user[:user.find('@')]
    else:
      emailsettings.domain = domain
    sys.stderr.write("Getting delegates for %s...\n" % (user + '@' + emailsettings.domain))
    try_count = 0
    wait_on_fail = .5
    hard_fail = False
    while try_count < 10:
      try:
        delegates = emailsettings.GetDelegates(delegator=user)
        break
      except gdata.apps.service.AppsForYourDomainException, e:
        terminating_error = checkErrorCode(e)
        if not terminating_error:
          try_count = try_count + 1
          if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
          time.sleep(wait_on_fail)
          wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
          continue
        else:
          sys.stderr.write('Error: %s\n' % terminating_error)
          hard_fail = True
          break
    if try_count == 10 or hard_fail:
      sys.stderr.write('Giving up\n')
      continue
    for delegate in delegates:
      if csv_format:
        print '%s,%s,%s' % (user + '@' + emailsettings.domain, delegate['address'], delegate['status'])
      else:
        print "Delegator: %s\n Delegate: %s\n Status: %s\n Delegate Email: %s\n Delegate ID: %s\n" % (user, delegate['delegate'], delegate['status'], delegate['address'], delegate['delegationId'])

def deleteDelegate(users):
  emailsettings = getEmailSettingsObject()
  delegate = sys.argv[5]
  if not delegate.find('@') > 0:
    if users[0].find('@') > 0:
      delegatedomain = users[0][users[0].find('@')+1:]
    else:
      delegatedomain = domain
    delegate = delegate+'@'+delegatedomain
  count = len(users)
  i = 1
  for user in users:
    if user.find('@') > 0:
      emailsettings.domain = user[user.find('@')+1:]
      user = user[:user.find('@')]
    else:
      emailsettings.domain = domain #make sure it's back at default domain
    print "Deleting %s delegate access to %s (%s of %s)" % (delegate, user+'@'+emailsettings.domain, i, count)
    i = i + 1
    try_count = 0
    wait_on_fail = .5
    hard_fail = False
    while try_count < 10:
      try:
        emailsettings.DeleteDelegate(delegate=delegate, delegator=user)
        break
      except gdata.apps.service.AppsForYourDomainException, e:
        terminating_error = checkErrorCode(e)
        if not terminating_error:
          try_count = try_count + 1
          if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
          time.sleep(wait_on_fail)
          wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
          continue
        else:
          sys.stderr.write('Error: %s\n' % terminating_error)
          hard_fail = True
          break
    if try_count == 10 or hard_fail:
      sys.stderr.write('Giving up\n')
      continue

def deleteCalendar(users):
  del_cal = sys.argv[5]
  cal = getCalendarObject()
  count = len(users)
  i = 1
  for user in users:
    if user.find('@') > 0:
      user_domain = user[user.find('@')+1:]
      user = user[:user.find('@')]
    else:
      user_domain = domain
    uri = 'https://www.google.com/calendar/feeds/%s/allcalendars/full/%s' % (user+'@'+user_domain, del_cal)
    try:
      calendar_entry = cal.GetCalendarListEntry(uri)
    except gdata.service.RequestError, e:
      print 'Error: %s - %s' % (e[0]['reason'], e[0]['body'])
      continue
    try:
      edit_uri = calendar_entry.GetEditLink().href
      print "Removing user %s's subscription to %s calendar (%s of %s)" % (user+'@'+user_domain, del_cal, i, count)
      cal.DeleteCalendarEntry(edit_uri)
    except gdata.service.RequestError, e:
      print 'Error: %s - %s' % (e[0]['reason'], e[0]['body'])
    i = i + 1

def addCalendar(users):
  add_cal = sys.argv[5]
  cal = getCalendarObject()
  selected = 'true'
  hidden = 'false'
  color = None
  i = 6
  while i < len(sys.argv):
    if sys.argv[i].lower() == 'selected':
      if sys.argv[i+1].lower() == 'true':
        selected = 'true'
      elif sys.argv[i+1].lower() == 'false':
        selected = 'false'
      else:
        showUsage()
        print 'Value for selected must be true or false, not %s' % sys.argv[i+1]
        exit(4)
      i = i + 2
    elif sys.argv[i].lower() == 'hidden':
      if sys.argv[i+1].lower() == 'true':
        hidden = 'true'
      elif sys.argv[i+1].lower() == 'false':
        hidden = 'false'
      else:
        showUsage()
        print 'Value for hidden must be true or false, not %s' % sys.argv[i+1]
        exit(4)
      i = i + 2
    elif sys.argv[i].lower() == 'color':
      color = sys.argv[i+1]
      i = i + 2
    else:
      showUsage()
      print '%s is not a valid argument for "gam add calendar"' % sys.argv[i]
  i = 1
  count = len(users)
  for user in users:
    if user.find('@') > 0:
      user_domain = user[user.find('@')+1:]
      user = user[:user.find('@')]
    else:
      user_domain = domain
    calendar_entry = gdata.calendar.CalendarListEntry()
    try:
      insert_uri = 'https://www.google.com/calendar/feeds/%s/allcalendars/full' % (user+'@'+user_domain)
      calendar_entry.id = atom.Id(text=add_cal)
      calendar_entry.hidden = gdata.calendar.Hidden(value=hidden)
      calendar_entry.selected =  gdata.calendar.Selected(value=selected)
      if color != None:
        calendar_entry.color = gdata.calendar.Color(value=color)
      print "Subscribing %s to %s calendar (%s of %s)" % (user+'@'+user_domain, add_cal, i, count)
      cal.InsertCalendarSubscription(insert_uri=insert_uri, calendar=calendar_entry)
    except gdata.service.RequestError, e:
      print 'Error: %s - %s' % (e[0]['reason'], e[0]['body'])
    i = i + 1

def updateCalendar(users):
  update_cal = sys.argv[5]
  cal = getCalendarObject()
  selected = hidden = color = None
  i = 6
  while i < len(sys.argv):
    if sys.argv[i].lower() == 'selected':
      if sys.argv[i+1].lower() == 'true':
        selected = 'true'
      elif sys.argv[i+1].lower() == 'false':
        selected = 'false'
      else:
        showUsage()
        print 'Value for selected must be true or false, not %s' % sys.argv[i+1]
        exit(4)
      i = i + 2
    elif sys.argv[i].lower() == 'hidden':
      if sys.argv[i+1].lower() == 'true':
        hidden = 'true'
      elif sys.argv[i+1].lower() == 'false':
        calendar_entry.hidden =  gdata.calendar.Hidden(value='false')
        hidden = 'false'
      else:
        showUsage()
        print 'Value for hidden must be true or false, not %s' % sys.argv[i+1]
        exit(4)
      i = i + 2
    elif sys.argv[i].lower() == 'color':
      color = sys.argv[i+1]
      i = i + 2
    else:
      showUsage()
      print '%s is not a valid argument for "gam update calendar"' % sys.argv[i]
  i = 1
  count = len(users)
  for user in users:
    if user.find('@') > 0:
      user_domain = user[user.find('@')+1:]
      user = user[:user.find('@')]
    else:
      user_domain = domain
    uri = 'https://www.google.com/calendar/feeds/%s/allcalendars/full/%s' % (user+'@'+user_domain, update_cal)
    try:
      calendar_entry = cal.GetCalendarListEntry(uri)
    except gdata.service.RequestError, e:
      print 'Error: %s - %s' % (e[0]['reason'], e[0]['body'])
      continue
    if selected != None:
      calendar_entry.selected =  gdata.calendar.Selected(value=selected)
    if hidden != None:
      calendar_entry.hidden =  gdata.calendar.Hidden(value=hidden)
    if color != None:
      calendar_entry.color = gdata.calendar.Color(value=color)
    try:
      edit_uri = calendar_entry.GetEditLink().href
      print "Updating %s's subscription to calendar %s (%s of %s)" % (user+'@'+user_domain, update_cal, i, count)
      cal.UpdateCalendar(calendar_entry)
    except gdata.service.RequestError, e:
      print 'Error: %s - %s' % (e[0]['reason'], e[0]['body'])
      continue

def doCalendarShowACL():
  show_cal = sys.argv[2]
  cal = getCalendarObject()
  if show_cal.find('@') == -1:
    show_cal = show_cal+'@'+cal.domain
  uri = 'https://www.google.com/calendar/feeds/%s/acl/full' % (show_cal)
  try:
    feed = cal.GetCalendarAclFeed(uri=uri)
  except gdata.service.RequestError, e:
      print 'Error: %s - %s' % (e[0]['reason'], e[0]['body'])
      sys.exit(e[0]['status'])
  print feed.title.text
  for i, a_rule in enumerate(feed.entry):
    print '  Scope %s - %s' % (a_rule.scope.type, a_rule.scope.value)
    print '  Role: %s' % (a_rule.title.text)
    print ''

def doCalendarAddACL():
  use_cal = sys.argv[2]
  role = sys.argv[4].lower()
  if role != 'freebusy' and role != 'read' and role != 'editor' and role != 'owner':
    print 'Error: Role must be freebusy, read, editor or owner. Not %s' % role
    sys.exit (33)
  cal = getCalendarObject()
  user_to_add = sys.argv[5].lower()
  if user_to_add == 'domain' or user_to_add == 'default':
    print 'Error: The special users domain and default can\'t be added, please use update instead of add.'
    sys.exit(34)
  if user_to_add.find('@') == -1:
    user_to_add = user_to_add+'@'+cal.domain
  if use_cal.find('@') == -1:
    use_cal = use_cal+'@'+cal.domain
  rule = gdata.calendar.CalendarAclEntry()
  rule.scope = gdata.calendar.Scope(value=user_to_add)
  rule.scope.type = 'user'
  roleValue = 'http://schemas.google.com/gCal/2005#%s' % (role)
  rule.role = gdata.calendar.Role(value=roleValue)
  aclUrl = '/calendar/feeds/%s/acl/full' % use_cal
  try:
    print "Giving %s %s access to calendar %s" % (user_to_add, role, use_cal)
    returned_rule = cal.InsertAclEntry(rule, aclUrl)
  except gdata.service.RequestError, e:
      print 'Error: %s - %s' % (e[0]['reason'], e[0]['body'])
      sys.exit(e[0]['status'])

def doCalendarWipeData():
  use_cal = sys.argv[2]
  cal = getCalendarObject()
  try:
    response = cal.Post('calendarId=%s' % use_cal, 'https://www.googleapis.com/calendar/v3/calendars/%s/clear' % use_cal)
  except gdata.service.RequestError, e:
    if e[0]['status'] == 204:
      print 'All data for Calendar %s has been wiped' % use_cal
    else:
      print 'Error: %s - %s' % (e[0]['status'], e[0]['reason'])

def doCalendarUpdateACL():
  use_cal = sys.argv[2]
  role = sys.argv[4].lower()
  if role != 'freebusy' and role != 'read' and role != 'editor' and role != 'owner':
    print 'Error: Role must be freebusy, read, editor or owner. Not %s' % role
    exit (33)
  user_to_add = sys.argv[5].lower()
  cal = getCalendarObject()
  if use_cal.find('@') == -1:
    use_cal = use_cal+'@'+cal.domain
  if user_to_add.find('@') == -1 and user_to_add != 'domain' and user_to_add != 'default':
    user_to_add = user_to_add+'@'+cal.domain
  rule = gdata.calendar.CalendarAclEntry()
  if user_to_add == 'domain':
    rule_value = cal.domain
    rule_type = 'domain'
  elif user_to_add == 'default':
    rule_value = None
    rule_type = 'default'
  else:
    rule_value = user_to_add
    rule_type = 'user'
  rule.scope = gdata.calendar.Scope(value=rule_value)
  rule.scope.type = rule_type
  roleValue = 'http://schemas.google.com/gCal/2005#%s' % (role)
  rule.role = gdata.calendar.Role(value=roleValue)
  if rule_type != 'default':
    aclUrl = '/calendar/feeds/%s/acl/full/%s%%3A%s' % (use_cal, rule_type, rule_value)
  else:
    aclUrl = '/calendar/feeds/%s/acl/full/default' % (use_cal)
  try:
    returned_rule = cal.UpdateAclEntry(edit_uri=aclUrl, updated_rule=rule)
  except gdata.service.RequestError, e:
      print 'Error: %s - %s' % (e[0]['reason'], e[0]['body'])
      sys.exit(e[0]['status'])

def doCalendarDelACL():
  use_cal = sys.argv[2]
  if sys.argv[4].lower() != 'user':
    print 'invalid syntax'
    exit(9)
  user_to_del = sys.argv[5].lower()
  cal = getCalendarObject()
  if use_cal.find('@') == -1:
    use_cal = use_cal+'@'+cal.domain
  if user_to_del.find('@') == -1 and user_to_del != 'domain' and user_to_del != 'default':
    user_to_del = user_to_del+'@'+cal.domain
  uri = 'https://www.google.com/calendar/feeds/%s/acl/full' % (use_cal)
  try:
    feed = cal.GetCalendarAclFeed(uri=uri)
  except gdata.service.RequestError, e:
      print 'Error: %s - %s' % (e[0]['reason'], e[0]['body'])
      sys.exit(e[0]['status'])  
  found_rule = False
  print "Removing %s's access to calendar %s" % (user_to_del, use_cal)
  for i, a_rule in enumerate(feed.entry):
      try:
        if (user_to_del == 'default' and a_rule.scope.value == None) or (a_rule.scope.type.lower() == 'domain' and user_to_del == 'domain') or a_rule.scope.value.lower() == user_to_del:
          found_rule = True
          try:
            result = cal.DeleteAclEntry(a_rule.GetEditLink().href)
          except gdata.service.RequestError, e:
            print 'Error: %s - %s' % (e[0]['reason'], e[0]['body'])
            sys.exit(e[0]['status'])
          break
      except AttributeError:
        continue
  if not found_rule:
    print 'Error: that object does not seem to have access to that calendar'
    exit(34)

def doProfile(users):
  if sys.argv[4].lower() == 'share' or sys.argv[4].lower() == 'shared':
    indexed = 'true'
  elif sys.argv[4].lower() == 'unshare' or sys.argv[4].lower() == 'unshared':
    indexed = 'false'
  profiles = getProfilesObject()
  count = len(users)
  i = 1
  for user in users:
    if user.find('@') > 0:
      user_domain = user[user.find('@')+1:]
      user = user[:user.find('@')]
    else:
      user_domain = domain
    print 'Setting Profile Sharing to %s for %s@%s (%s of %s)' % (indexed, user, user_domain, i, count)
    uri = '/m8/feeds/profiles/domain/%s/full/%s?v=3.0' % (user_domain, user)
    try:
      user_profile = profiles.GetProfile(uri)
      user_profile.extension_elements[2].attributes['indexed'] = indexed
      profiles.UpdateProfile(user_profile.GetEditLink().href, user_profile)
    except gdata.service.RequestError, e:
      print 'Error: %s@%s %s - %s' % (user, user_domain, e[0]['body'], e[0]['reason'])
    i += 1

def showProfile(users):
  profiles = getProfilesObject()
  for user in users:
    if user.find('@') > 0:
      user_domain = user[user.find('@')+1:]
      user = user[:user.find('@')]
    else:
      user_domain = domain
    uri = '/m8/feeds/profiles/domain/%s/full/%s?v=3.0' % (user_domain, user)
    try:
      user_profile = profiles.GetProfile(uri)
    except gdata.service.RequestError, e:
      print 'Error: %s@%s %s - %s' % (user, user_domain, e[0]['body'], e[0]['reason'])
      continue
    indexed = user_profile.extension_elements[2].attributes['indexed']
    print '''User: %s@%s
 Profile Shared: %s''' % (user, user_domain, indexed)

def doPhoto(users):
  filename = sys.argv[5]
  profiles = getProfilesObject()
  i = 1
  count = len(users)
  for user in users:
    if user.find('@') > 0:
      user_domain = user[user.find('@')+1:]
      user = user[:user.find('@')]
    else:
      user_domain = domain
    uri = '/m8/feeds/profiles/domain/%s/full/%s?v=3' % (user_domain, user)
    try:
      user_profile = profiles.GetProfile(uri)
      photo_uri = user_profile.link[0].href
      try:
        if sys.argv[6].lower() == 'nooverwrite':
          etag = user_profile.link[0].extension_attributes['{http://schemas.google.com/g/2005}etag']
          print 'Not overwriting existing photo for %s@%s' % (user, user_domain)
          continue
      except IndexError:
        pass
      except KeyError:
        pass
      print "Updating photo for %s (%s of %s)" % (user+'@'+user_domain, i, count)
      results = profiles.ChangePhoto(media=filename, content_type='image/jpeg', contact_entry_or_url=photo_uri)
    except gdata.service.RequestError, e:
      print 'Error: %s@%s %s - %s' % (user, user_domain, e[0]['body'], e[0]['reason'])
    i = i + 1

def getPhoto(users):
  profiles = getProfilesObject()
  i = 1
  count = len(users)
  for user in users:
    if user.find('@') > 0:
      user_domain = user[user.find('@')+1:]
      user = user[:user.find('@')]
    else:
      user_domain = domain
    uri = '/m8/feeds/profiles/domain/%s/full/%s?v=3' % (user_domain, user)
    try:
      user_profile = profiles.GetProfile(uri)
      try:
        etag = user_profile.link[0].extension_attributes['{http://schemas.google.com/g/2005}etag']
      except KeyError:
        print '  No photo for %s@%s' % (user, user_domain)
        i = i + 1
        continue
      photo_uri = user_profile.link[0].href
      filename = '%s-%s.jpg' % (user, user_domain)
      print "Saving photo for %s to %s (%s of %s)" % (user+'@'+user_domain, filename, i, count)
      photo = profiles.GetPhoto(contact_entry_or_url=photo_uri)
    except gdata.service.RequestError, e:
      print 'Error: %s@%s %s - %s' % (user, user_domain, e[0]['body'], e[0]['reason'])
      i = i + 1  
      continue
    photo_file = open(filename, 'wb')
    photo_file.write(photo)
    photo_file.close()
    i = i + 1

def deletePhoto(users):
  profiles = getProfilesObject()
  i = 1
  count = len(users)
  for user in users:
    if user.find('@') > 0:
      user_domain = user[user.find('@')+1:]
      user = user[:user.find('@')]
    else:
      user_domain = domain
    uri = '/m8/feeds/profiles/domain/%s/full/%s?v=3' % (user_domain, user)
    try:
      user_profile = profiles.GetProfile(uri)
      photo_uri = user_profile.link[0].href
      print "Deleting photo for %s (%s of %s)" % (user+'@'+user_domain, i, count)
      results = profiles.DeletePhoto(photo_uri)
    except gdata.service.RequestError, e:
      print 'Error: %s@%s %s - %s' % (user, user_domain, e[0]['body'], e[0]['reason'])
    i = i + 1

def showCalendars(users):
  cal = getCalendarObject()
  for user in users:
    if user.find('@') > 0:
      user_domain = user[user.find('@')+1:]
      user = user[:user.find('@')]
    else:
      user_domain = domain
    uri = '/calendar/feeds/%s/allcalendars/full' % (user+'@'+user_domain,)
    try:
      feed = cal.GetAllCalendarsFeed(uri)
    except gdata.service.RequestError, e:
      print 'Error: %s@%s %s - %s' % (user, user_domain, e[0]['body'], e[0]['reason'])
      continue
    print '%s' % feed.title.text
    for i, a_calendar in enumerate(feed.entry):
      print '  Name: %s' % str(a_calendar.title.text)
      print '    ID: %s' % urllib.unquote(str(a_calendar.id.text).rpartition('/')[2])
      print '    Access Level: %s' % str(a_calendar.access_level.value)
      print '    Timezone: %s' % str(a_calendar.timezone.value)
      print '    Hidden: %s' % str(a_calendar.hidden.value)
      print '    Selected: %s' % str(a_calendar.selected.value)
      print '    Color: %s' % str(a_calendar.color.value)
      print ''

def showCalSettings(users):
  cal = getCalendarObject()
  for user in users:
    if user.find('@') > 0:
      user_domain = user[user.find('@')+1:]
      user = user[:user.find('@')]
    else:
      user_domain = domain
    uri = 'https://www.googleapis.com/calendar/v3/users/%s/settings' % ('me')
    try:
      feed = cal.Get(uri, converter=str)
    except gdata.service.RequestError, e:
      print 'Error: %s - %s' % (e[0]['reason'], e[0]['body'])
      sys.exit(e[0]['status'])
    print feed

def doImap(users):
  checkTOS = False
  if sys.argv[4].lower() == 'on':
    enable = True
  elif sys.argv[4].lower() == 'off':
    enable = False
  if len(sys.argv) > 5 and sys.argv[5] == 'confirm':
    checkTOS = True
  emailsettings = getEmailSettingsObject()
  count = len(users)
  i = 1
  for user in users:
    if user.find('@') > 0:
      emailsettings.domain = user[user.find('@')+1:]
      user = user[:user.find('@')]
    else:
      emailsettings.domain = domain #make sure it's back at default domain
    print "Setting IMAP Access to %s for %s (%s of %s)" % (str(enable), user+'@'+emailsettings.domain, i, count)
    i = i + 1
    if checkTOS:
      if not hasAgreed2TOS(user+'@'+emailsettings.domain):
        print ' Warning: IMAP has been enabled but '+user+'@'+emailsettings.domain+' has not logged into GMail to agree to the terms of service (captcha).  IMAP will not work until they do.'
    try_count = 0
    wait_on_fail = .5
    hard_fail = False
    while try_count < 10:
      try:
        emailsettings.UpdateImap(username=user, enable=enable)
        break
      except gdata.apps.service.AppsForYourDomainException, e:
        terminating_error = checkErrorCode(e)
        if not terminating_error:
          try_count = try_count + 1
          if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
          time.sleep(wait_on_fail)
          wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
          continue
        else:
          sys.stderr.write('Error: %s\n' % terminating_error)
          hard_fail = True
          break
    if try_count == 10 or hard_fail:
      sys.stderr.write('Giving up\n')
      continue

def getImap(users):
  emailsettings = getEmailSettingsObject()
  i = 1
  for user in users:
    if user.find('@') > 0:
      emailsettings.domain = user[user.find('@')+1:]
      user = user[:user.find('@')]
    else:
      emailsettings.domain = domain
    count = len(users)
    try_count = 0
    wait_on_fail = .5
    hard_fail = False
    while try_count < 10:
      try:
        imapsettings = emailsettings.GetImap(username=user)
        break
      except gdata.apps.service.AppsForYourDomainException, e:
        terminating_error = checkErrorCode(e)
        if not terminating_error:
          try_count = try_count + 1
          if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
          time.sleep(wait_on_fail)
          wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
          continue
        else:
          sys.stderr.write('Error: %s\n' % terminating_error)
          hard_fail = True
          break
    if try_count == 10 or hard_fail:
      sys.stderr.write('Giving up\n')
      i = i + 1
      continue
    print 'User %s  IMAP Enabled:%s (%s of %s)' % (user+'@'+emailsettings.domain, imapsettings['enable'], i, count)
    i = i + 1

def doPop(users):
  checkTOS = False
  if sys.argv[4].lower() == 'on':
    enable = True
  elif sys.argv[4].lower() == 'off':
    enable = False
  enable_for = 'ALL_MAIL'
  action = 'KEEP'
  i = 5
  while i < len(sys.argv):
    if sys.argv[i].lower() == 'for':
      if sys.argv[i+1].lower() == 'allmail':
        enable_for = 'ALL_MAIL'
        i = i + 2
      elif sys.argv[i+1].lower() == 'newmail':
        enable_for = 'MAIL_FROM_NOW_ON'
        i = i + 2
    elif sys.argv[i].lower() == 'action':
      if sys.argv[i+1].lower() == 'keep':
        action = 'KEEP'
        i = i + 2
      elif sys.argv[i+1].lower() == 'archive':
        action = 'ARCHIVE'
        i = i + 2
      elif sys.argv[i+1].lower() == 'delete':
        action = 'DELETE'
        i = i + 2
    elif sys.argv[i].lower() == 'confirm':
      checkTOS = True
      i = i + 1
    else:
      showUsage()
      sys.exit(2)
  emailsettings = getEmailSettingsObject()
  count = len(users)
  i = 1
  for user in users:
    if user.find('@') > 0:
      emailsettings.domain = user[user.find('@')+1:]
      user = user[:user.find('@')]
    else:
      emailsettings.domain = domain #make sure it's back at default domain
    print "Setting POP Access to %s for %s (%s of %s)" % (str(enable), user+'@'+emailsettings.domain, i, count)
    i = i + 1
    if checkTOS:
      if not hasAgreed2TOS(user):
        print ' Warning: POP has been enabled but '+user+'@'+emailsettings.domain+' has not logged into GMail to agree to the terms of service (captcha).  POP will not work until they do.'
    try_count = 0
    wait_on_fail = .5
    hard_fail = False
    while try_count < 10:
      try:
        emailsettings.UpdatePop(username=user, enable=enable, enable_for=enable_for, action=action)
        break
      except gdata.apps.service.AppsForYourDomainException, e:
        terminating_error = checkErrorCode(e)
        if not terminating_error:
          try_count = try_count + 1
          if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
          time.sleep(wait_on_fail)
          wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
          continue
        else:
          sys.stderr.write('Error: %s\n' % terminating_error)
          hard_fail = True
          break
    if try_count == 10 or hard_fail:
      sys.stderr.write('Giving up\n')
      continue

def getPop(users):
  emailsettings = getEmailSettingsObject()
  for user in users:
    if user.find('@') > 0:
      emailsettings.domain = user[user.find('@')+1:]
      user = user[:user.find('@')]
    else:
      emailsettings.domain = domain
    try_count = 0
    wait_on_fail = .5
    hard_fail = False
    while try_count < 10:
      try:
        popsettings = emailsettings.GetPop(username=user)
        break
      except gdata.apps.service.AppsForYourDomainException, e:
        terminating_error = checkErrorCode(e)
        if not terminating_error:
          try_count = try_count + 1
          if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
          time.sleep(wait_on_fail)
          wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
          continue
        else:
          sys.stderr.write('Error: %s\n' % terminating_error)
          hard_fail = True
          break
    if try_count == 10 or hard_fail:
      sys.stderr.write('Giving up\n')
      continue
    print 'User %s  POP Enabled:%s  Action:%s' % (user+'@'+emailsettings.domain, popsettings['enable'], popsettings['action'])

def doSendAs(users):
  sendas = sys.argv[4]
  sendasName = sys.argv[5]
  make_default = reply_to = None
  i = 6
  while i < len(sys.argv):
    if sys.argv[i].lower() == 'default':
      make_default = True
      i = i + 1
    elif sys.argv[i].lower() == 'replyto':
      reply_to = sys.argv[i+1]
      i = i + 2
    else:
      showUsage()
      sys.exit(2)
  emailsettings = getEmailSettingsObject()
  if sendas.find('@') < 0:
    sendas = sendas+'@'+domain
  count = len(users)
  i = 1
  for user in users:
    if user.find('@') > 0:
      emailsettings.domain = user[user.find('@')+1:]
      user = user[:user.find('@')]
    else:
      emailsettings.domain = domain #make sure it's back at default domain
    print "Allowing %s to send as %s (%s of %s)" % (user+'@'+emailsettings.domain, sendas, i, count)
    i = i + 1
    try_count = 0
    wait_on_fail = .5
    hard_fail = False
    while try_count < 10:
      try:
        emailsettings.CreateSendAsAlias(username=user, name=sendasName, address=sendas, make_default=make_default, reply_to=reply_to)
        break
      except gdata.apps.service.AppsForYourDomainException, e:
        terminating_error = checkErrorCode(e)
        if not terminating_error:
          try_count = try_count + 1
          if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
          time.sleep(wait_on_fail)
          wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
          continue
        else:
          sys.stderr.write('Error: %s\n' % terminating_error)
          hard_fail = True
          break
    if try_count == 10 or hard_fail:
      sys.stderr.write('Giving up\n')
      continue

def showSendAs(users):
  emailsettings = getEmailSettingsObject()
  for user in users:
    if user.find('@') > 0:
      emailsettings.domain = user[user.find('@')+1:]
      user = user[:user.find('@')]
    else:
      emailsettings.domain = domain
    print '%s has the following send as aliases:' %  (user+'@'+emailsettings.domain)
    try_count = 0
    wait_on_fail = .5
    hard_fail = False
    while try_count < 10:
      try:
        sendases = emailsettings.GetSendAsAlias(username=user) 
        break
      except gdata.apps.service.AppsForYourDomainException, e:
        terminating_error = checkErrorCode(e)
        if not terminating_error:
          try_count = try_count + 1
          if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
          time.sleep(wait_on_fail)
          wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
          continue
        else:
          sys.stderr.write('Error: %s\n' % terminating_error)
          hard_fail = True
          break
    if try_count == 10 or hard_fail:
      sys.stderr.write('Giving up\n')
      continue
    for sendas in sendases:
      if sendas['isDefault'] == 'true':
        default = 'yes'
      else:
        default = 'no'
      if sendas['replyTo']:
        replyto = ' Reply To:<'+sendas['replyTo']+'>'
      else:
        replyto = ''
      if sendas['verified'] == 'true':
        verified = 'yes'
      else:
        verified = 'no'
      print ' "%s" <%s>%s Default:%s Verified:%s' % (sendas['name'], sendas['address'], replyto, default, verified)
    print ''

def doLanguage(users):
  language = sys.argv[4].lower()
  emailsettings = getEmailSettingsObject()
  count = len(users)
  i = 1
  for user in users:
    if user.find('@') > 0:
      emailsettings.domain = user[user.find('@')+1:]
      user = user[:user.find('@')]
    else:
      emailsettings.domain = domain #make sure it's back at default domain
    print "Setting the language for %s to %s (%s of %s)" % (user+'@'+emailsettings.domain, language, i, count)
    i = i + 1
    try_count = 0
    wait_on_fail = .5
    hard_fail = False
    while try_count < 10:
      try:
        emailsettings.UpdateLanguage(username=user, language=language)
        break
      except gdata.apps.service.AppsForYourDomainException, e:
        terminating_error = checkErrorCode(e)
        if not terminating_error:
          try_count = try_count + 1
          if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
          time.sleep(wait_on_fail)
          wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
          continue
        else:
          sys.stderr.write('Error: %s\n' % terminating_error)
          hard_fail = True
          break
    if try_count == 10 or hard_fail:
      sys.stderr.write('Giving up\n')
      continue
  
def doUTF(users):
  if sys.argv[4].lower() == 'on':
    SetUTF = True
  elif sys.argv[4].lower() == 'off':
    SetUTF = False
  emailsettings = getEmailSettingsObject()
  count = len(users)
  i = 1
  for user in users:
    if user.find('@') > 0:
      emailsettings.domain = user[user.find('@')+1:]
      user = user[:user.find('@')]
    else:
      emailsettings.domain = domain #make sure it's back at default domain
    print "Setting UTF-8 to %s for %s (%s of %s)" % (str(SetUTF), user+'@'+emailsettings.domain, i, count)
    i = i + 1
    try_count = 0
    wait_on_fail = .5
    hard_fail = False
    while try_count < 10:
      try:
        emailsettings.UpdateGeneral(username=user, unicode=SetUTF)
        break
      except gdata.apps.service.AppsForYourDomainException, e:
        terminating_error = checkErrorCode(e)
        if not terminating_error:
          try_count = try_count + 1
          if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
          time.sleep(wait_on_fail)
          wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
          continue
        else:
          sys.stderr.write('Error: %s\n' % terminating_error)
          hard_fail = True
          break
    if try_count == 10 or hard_fail:
      sys.stderr.write('Giving up\n')
      continue

def doPageSize(users):
  if sys.argv[4] == '25' or sys.argv[4] == '50' or sys.argv[4] == '100':
    PageSize = sys.argv[4]
  else:
    showUsage()
    sys.exit(2)
  emailsettings = getEmailSettingsObject()
  count = len(users)
  i = 1
  for user in users:
    if user.find('@') > 0:
      emailsettings.domain = user[user.find('@')+1:]
      user = user[:user.find('@')]
    else:
      emailsettings.domain = domain #make sure it's back at default domain
    print "Setting Page Size to %s for %s (%s of %s)" % (PageSize, user+'@'+emailsettings.domain, i, count)
    i = i + 1
    try_count = 0
    wait_on_fail = .5
    hard_fail = False
    while try_count < 10:
      try:
        emailsettings.UpdateGeneral(username=user, page_size=PageSize)
        break
      except gdata.apps.service.AppsForYourDomainException, e:
        terminating_error = checkErrorCode(e)
        if not terminating_error:
          try_count = try_count + 1
          if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
          time.sleep(wait_on_fail)
          wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
          continue
        else:
          sys.stderr.write('Error: %s\n' % terminating_error)
          hard_fail = True
          break
    if try_count == 10 or hard_fail:
      sys.stderr.write('Giving up\n')
      continue

def doShortCuts(users):
  if sys.argv[4].lower() == 'on':
    SetShortCuts = True
  elif sys.argv[4].lower() == 'off':
    SetShortCuts = False
  emailsettings = getEmailSettingsObject()
  count = len(users)
  i = 1
  for user in users:
    if user.find('@') > 0:
      emailsettings.domain = user[user.find('@')+1:]
      user = user[:user.find('@')]
    else:
      emailsettings.domain = domain #make sure it's back at default domain
    print "Setting Keyboard Short Cuts to %s for %s (%s of %s)" % (str(SetShortCuts), user+'@'+emailsettings.domain, i, count)
    i = i + 1
    try_count = 0
    wait_on_fail = .5
    hard_fail = False
    while try_count < 10:
      try:
        emailsettings.UpdateGeneral(username=user, shortcuts=SetShortCuts)
        break
      except gdata.apps.service.AppsForYourDomainException, e:
        terminating_error = checkErrorCode(e)
        if not terminating_error:
          try_count = try_count + 1
          if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
          time.sleep(wait_on_fail)
          wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
          continue
        else:
          sys.stderr.write('Error: %s\n' % terminating_error)
          hard_fail = True
          break
    if try_count == 10 or hard_fail:
      sys.stderr.write('Giving up\n')
      continue

def doAdminAudit():
  i = 3
  admin = event = start_date = end_date = max_results = None
  while i < len(sys.argv):
    if sys.argv[i].lower() == 'admin':
      admin = sys.argv[i+1]
      i = i + 2
    elif sys.argv[i].lower() == 'event':
      event = sys.argv[i+1]
      i = i + 2
    elif sys.argv[i].lower() == 'start_date':
      start_date = sys.argv[i+1]
      i = i + 2
    elif sys.argv[i].lower() == 'end_date':
      end_date = sys.argv[i+1]
      i = i + 2
    elif sys.argv[i].lower() == 'max_results':
      max_results = sys.argv[i+1]
      i = i + 2
    else:
      showUsage()
      sys.exit(2)
  orgs = getOrgObject()
  try_count = 0
  wait_on_fail = .5
  hard_fail = False
  while try_count < 10:
    try:
      customer_id = orgs.RetrieveCustomerId()['customerId']
      break
    except gdata.apps.service.AppsForYourDomainException, e:
      terminating_error = checkErrorCode(e)
      if not terminating_error:
        try_count = try_count + 1
        if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
        time.sleep(wait_on_fail)
        wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
        continue
      else:
        sys.stderr.write('Error: %s\n' % terminating_error)
        sys.exit(e.error_code)
  if try_count == 10:
    sys.stderr.write('Giving up\n')
    sys.exit(e.error_code)
  aa = getAdminAuditObject()
  try_count = 0
  wait_on_fail = .5
  hard_fail = False
  while try_count < 10:
    try:
      results = aa.retrieve_audit(customer_id=customer_id, admin=admin, event=event, start_date=start_date, end_date=end_date, max_results=max_results)
      break
    except gdata.apps.service.AppsForYourDomainException, e:
      terminating_error = checkErrorCode(e)
      if not terminating_error:
        try_count = try_count + 1
        if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
        time.sleep(wait_on_fail)
        wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
        continue
      else:
        sys.stderr.write('Error: %s\n' % terminating_error)
        hard_fail = True
        break
  if try_count == 10 or hard_fail:
    sys.stderr.write('Giving up\n')
    sys.exit(e.error_code)
  print results

def doArrows(users):
  if sys.argv[4].lower() == 'on':
    SetArrows = True
  elif sys.argv[4].lower() == 'off':
    SetArrows = False
  emailsettings = getEmailSettingsObject()
  count = len(users)
  i = 1
  for user in users:
    if user.find('@') > 0:
      emailsettings.domain = user[user.find('@')+1:]
      user = user[:user.find('@')]
    else:
      emailsettings.domain = domain #make sure it's back at default domain
    print "Setting Personal Indicator Arrows to %s for %s (%s of %s)" % (str(SetArrows), user+'@'+emailsettings.domain, i, count)
    i = i + 1
    try_count = 0
    wait_on_fail = .5
    hard_fail = False
    while try_count < 10:
      try:
        emailsettings.UpdateGeneral(username=user, arrows=SetArrows)
        break
      except gdata.apps.service.AppsForYourDomainException, e:
        terminating_error = checkErrorCode(e)
        if not terminating_error:
          try_count = try_count + 1
          if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
          time.sleep(wait_on_fail)
          wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
          continue
        else:
          sys.stderr.write('Error: %s\n' % terminating_error)
          hard_fail = True
          break
    if try_count == 10 or hard_fail:
      sys.stderr.write('Giving up\n')
      continue

def doSnippets(users):
  if sys.argv[4].lower() == 'on':
    SetSnippets = True
  elif sys.argv[4].lower() == 'off':
    SetSnippets = False
  emailsettings = getEmailSettingsObject()
  count = len(users)
  i = 1
  for user in users:
    if user.find('@') > 0:
      emailsettings.domain = user[user.find('@')+1:]
      user = user[:user.find('@')]
    else:
      emailsettings.domain = domain #make sure it's back at default domain
    print "Setting Preview Snippets to %s for %s (%s of %s)" % (str(SetSnippets), user+'@'+emailsettings.domain, i, count)
    i = i + 1
    try_count = 0
    wait_on_fail = .5
    hard_fail = False
    while try_count < 10:
      try:
        emailsettings.UpdateGeneral(username=user, snippets=SetSnippets)
        break
      except gdata.apps.service.AppsForYourDomainException, e:
        terminating_error = checkErrorCode(e)
        if not terminating_error:
          try_count = try_count + 1
          if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
          time.sleep(wait_on_fail)
          wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
          continue
        else:
          sys.stderr.write('Error: %s\n' % terminating_error)
          hard_fail = True
          break
    if try_count == 10 or hard_fail:
      sys.stderr.write('Giving up\n')
      continue

def doLabel(users):
  label = sys.argv[4]
  emailsettings = getEmailSettingsObject()
  count = len(users)
  i = 1
  for user in users:
    if user.find('@') > 0:
      emailsettings.domain = user[user.find('@')+1:]
      user = user[:user.find('@')]
    else:
      emailsettings.domain = domain #make sure it's back at default domain
    print "Creating label %s for %s (%s of %s)" % (label, user+'@'+emailsettings.domain, i, count)
    i = i + 1
    try_count = 0
    wait_on_fail = .5
    hard_fail = False
    while try_count < 10:
      try:
        emailsettings.CreateLabel(username=user, label=label)
        break
      except gdata.apps.service.AppsForYourDomainException, e:
        terminating_error = checkErrorCode(e)
        if not terminating_error:
          try_count = try_count + 1
          if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
          time.sleep(wait_on_fail)
          wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
          continue
        else:
          sys.stderr.write('Error: %s\n' % terminating_error)
          hard_fail = True
          break
    if try_count == 10 or hard_fail:
      sys.stderr.write('Giving up\n')
      continue

def doDeleteLabel(users):
  label = sys.argv[5]
  emailsettings = getEmailSettingsObject()
  count = len(users)
  i = 1
  for user in users:
    if user.find('@') > 0:
      emailsettings.domain = user[user.find('@')+1:]
      user = user[:user.find('@')]
    else:
      emailsettings.domain = domain
    print "Deleting label %s for %s (%s of %s)" % (label, user+'@'+emailsettings.domain, i, count)
    i = i + 1
    try_count = 0
    wait_on_fail = .5
    hard_fail = False
    while try_count < 10:
      try:
        results = emailsettings.DeleteLabel(username=user, label=label)
        break
      except gdata.apps.service.AppsForYourDomainException, e:
        terminating_error = checkErrorCode(e)
        if not terminating_error:
          try_count = try_count + 1
          if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
          time.sleep(wait_on_fail)
          wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
          continue
        else:
          sys.stderr.write('Error: %s\n' % terminating_error)
          hard_fail = True
          break
    if try_count == 10 or hard_fail:
      sys.stderr.write('Giving up\n')
      continue

def showLabels(users):
  emailsettings = getEmailSettingsObject()
  for user in users:
    if user.find('@') > 0:
      emailsettings.domain = user[user.find('@')+1:]
      user = user[:user.find('@')]
    else:
      emailsettings.domain = domain
    print '%s has the following labels:' %  (user+'@'+emailsettings.domain)
    try_count = 0
    wait_on_fail = .5
    hard_fail = False
    while try_count < 10:
      try:
        labels = emailsettings.GetLabels(username=user)
        break
      except gdata.apps.service.AppsForYourDomainException, e:
        terminating_error = checkErrorCode(e)
        if not terminating_error:
          try_count = try_count + 1
          if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
          time.sleep(wait_on_fail)
          wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
          continue
        else:
          sys.stderr.write('Error: %s\n' % terminating_error)
          hard_fail = True
          break
    if try_count == 10 or hard_fail:
      sys.stderr.write('Giving up\n')
      continue
    for label in labels:
      print ' %s  Unread:%s  Visibility:%s' % (label['label'], label['unreadCount'], label['visibility'])
    print ''

def doFilter(users):
  i = 4 # filter arguments start here
  from_ = to = subject = has_the_word = does_not_have_the_word = has_attachment = label = should_mark_as_read = should_archive = should_star = forward_to = should_trash = should_not_spam = None
  haveCondition = False
  while sys.argv[i].lower() == 'from' or sys.argv[i].lower() == 'to' or sys.argv[i].lower() == 'subject' or sys.argv[i].lower() == 'haswords' or sys.argv[i].lower() == 'nowords' or sys.argv[i].lower() == 'musthaveattachment':
    if sys.argv[i].lower() == 'from':
      from_ = sys.argv[i+1]
      i = i + 2
      haveCondition = True
    elif sys.argv[i].lower() == 'to':
      to = sys.argv[i+1]
      i = i + 2
      haveCondition = True
    elif sys.argv[i].lower() == 'subject':
      subject = sys.argv[i+1]
      i = i + 2
      haveCondition = True
    elif sys.argv[i].lower() == 'haswords':
      has_the_word = sys.argv[i+1]
      i = i + 2
      haveCondition = True
    elif sys.argv[i].lower() == 'nowords':
      does_not_have_the_word = sys.argv[i+1]
      i = i + 2
      haveCondition = True
    elif sys.argv[i].lower() == 'musthaveattachment':
      has_attachment = True
      i = i + 1
      haveCondition = True
  if not haveCondition:
    showUsage()
    sys.exit(2)
  haveAction = False
  while i < len(sys.argv):
    if sys.argv[i].lower() == 'label':
      label = sys.argv[i+1]
      i = i + 2
      haveAction = True
    elif sys.argv[i].lower() == 'markread':
      should_mark_as_read = True
      i = i + 1
      haveAction = True
    elif sys.argv[i].lower() == 'archive':
      should_archive = True
      i = i + 1
      haveAction = True
    elif sys.argv[i].lower() == 'star':
      should_star = True
      i = i + 1
      haveAction = True
    elif sys.argv[i].lower() == 'forward':
      forward_to = sys.argv[i+1]
      i = i + 2
      haveAction = True
    elif sys.argv[i].lower() == 'trash':
      should_trash = True
      i = i + 1
      haveAction = True
    elif sys.argv[i].lower() == 'neverspam':
      should_not_spam = True
      i = i + 1
      haveAction = True
    else:
      showUsage()
      sys.exit(2)
  if not haveAction:
    showUsage()
    sys.exit(2)
  emailsettings = getEmailSettingsObject()
  count = len(users)
  i = 1
  for user in users:
    if user.find('@') > 0:
      emailsettings.domain = user[user.find('@')+1:]
      user = user[:user.find('@')]
    else:
      emailsettings.domain = domain #make sure it's back at default domain
    print "Creating filter for %s (%s of %s)" % (user+'@'+emailsettings.domain, i, count)
    i = i + 1
    try_count = 0
    wait_on_fail = .5
    hard_fail = False
    while try_count < 10:
      try:
        emailsettings.CreateFilter(username=user, from_=from_, to=to, subject=subject, has_the_word=has_the_word, does_not_have_the_word=does_not_have_the_word, has_attachment=has_attachment, label=label, should_mark_as_read=should_mark_as_read, should_archive=should_archive, should_star=should_star, forward_to=forward_to, should_trash=should_trash, should_not_spam=should_not_spam)
        break
      except gdata.apps.service.AppsForYourDomainException, e:
        terminating_error = checkErrorCode(e)
        if not terminating_error:
          try_count = try_count + 1
          if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
          time.sleep(wait_on_fail)
          wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
          continue
        else:
          sys.stderr.write('Error: %s\n' % terminating_error)
          hard_fail = True
          break
    if try_count == 10 or hard_fail:
      sys.stderr.write('Giving up\n')
      continue

def doForward(users):
  checkTOS = False
  action = forward_to = None
  gotAction = gotForward = False
  if sys.argv[4] == 'on':
    enable = True
  elif sys.argv[4] == 'off':
    enable = False
  else:
    showUsage()
    sys.exit(2)
  i = 5
  while i < len(sys.argv):
    if sys.argv[i].lower() == 'keep' or sys.argv[i].lower() == 'archive' or sys.argv[i].lower() == 'delete':
      action = sys.argv[i].upper()
      i = i + 1
      gotAction = True
    elif sys.argv[i].lower() == 'confirm':
      checkTOS = True
      i = i + 1
    elif sys.argv[i].find('@') != -1:
      forward_to = sys.argv[i]
      gotForward = True
      i = i + 1
    else:
      showUsage()
      sys.exit(2)
  if enable and (not gotAction or not gotForward):
    showUsage()
    sys.exit()
  emailsettings = getEmailSettingsObject()
  count = len(users)
  i = 1
  for user in users:
    if user.find('@') > 0:
      emailsettings.domain = user[user.find('@')+1:]
      user = user[:user.find('@')]
    else:
      emailsettings.domain = domain #make sure it's back at default domain
    print "Turning forward %s for %s, emails will be %s (%s of %s)" % (sys.argv[4], user+'@'+emailsettings.domain, action, i, count)
    i = i + 1
    if checkTOS:
      if not hasAgreed2TOS(user):
        print ' Warning: Forwarding has been enabled but '+user+'@'+emailsettings.domain+' has not logged into GMail to agree to the terms of service (captcha).  Forwarding will not work until they do.'
    try_count = 0
    wait_on_fail = .5
    hard_fail = False
    while try_count < 10:
      try:
        emailsettings.UpdateForwarding(username=user, enable=enable, action=action, forward_to=forward_to)
        break
      except gdata.apps.service.AppsForYourDomainException, e:
        terminating_error = checkErrorCode(e)
        if not terminating_error:
          try_count = try_count + 1
          if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
          time.sleep(wait_on_fail)
          wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
          continue
        else:
          sys.stderr.write('Error: %s\n' % terminating_error)
          hard_fail = True
          break
    if try_count == 10 or hard_fail:
      sys.stderr.write('Giving up\n')
      continue

def getForward(users):
  emailsettings = getEmailSettingsObject()
  for user in users:
    if user.find('@') > 0:
      emailsettings.domain = user[user.find('@')+1:]
      user = user[:user.find('@')]
    else:
      emailsettings.domain = domain
    try_count = 0
    wait_on_fail = .5
    hard_fail = False
    while try_count < 10:
      try:
        forward = emailsettings.GetForward(username=user)
        break
      except gdata.apps.service.AppsForYourDomainException, e:
        terminating_error = checkErrorCode(e)
        if not terminating_error:
          try_count = try_count + 1
          if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
          time.sleep(wait_on_fail)
          wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
          continue
        else:
          sys.stderr.write('Error: %s\n' % terminating_error)
          hard_fail = True
          break
    if try_count == 10 or hard_fail:
      sys.stderr.write('Giving up\n')
      continue
    print "User %s:  Forward To:%s  Enabled:%s  Action:%s" % (user+'@'+emailsettings.domain, forward['forwardTo'], forward['enable'], forward['action'])

def doSignature(users):
  if sys.argv[4].lower() == 'file':
    fp = open(sys.argv[5], 'rb')
    signature = cgi.escape(fp.read().replace('\\n', '&#xA;').replace('"', "'"))
    fp.close()
  else:
    signature = cgi.escape(sys.argv[4]).replace('\\n', '&#xA;').replace('"', "'")
  xmlsig = '''<?xml version="1.0" encoding="utf-8"?>
<atom:entry xmlns:atom="http://www.w3.org/2005/Atom" xmlns:apps="http://schemas.google.com/apps/2006">
    <apps:property name="signature" value="%s" />
</atom:entry>''' % signature
  emailsettings = getEmailSettingsObject()
  count = len(users)
  i = 1
  for user in users:
    if user.find('@') > 0:
      emailsettings.domain = user[user.find('@')+1:]
      user = user[:user.find('@')]
    else:
      emailsettings.domain = domain #make sure it's back at default domain
    print "Setting Signature for %s (%s of %s)" % (user+'@'+emailsettings.domain, i, count)
    uri = 'https://apps-apis.google.com/a/feeds/emailsettings/2.0/%s/%s/signature' % (emailsettings.domain, user)
    i = i + 1
    try_count = 0
    wait_on_fail = .5
    hard_fail = False
    while try_count < 10:
      try:
        emailsettings.Put(xmlsig, uri)
        break
      except gdata.apps.service.AppsForYourDomainException, e:
        terminating_error = checkErrorCode(e)
        if not terminating_error:
          try_count = try_count + 1
          if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
          time.sleep(wait_on_fail)
          wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
          continue
        else:
          sys.stderr.write('Error: %s\n' % terminating_error)
          hard_fail = True
          break
    if try_count == 10 or hard_fail:
      sys.stderr.write('Giving up\n')
      continue

def getSignature(users):
  emailsettings = getEmailSettingsObject()
  for user in users:
    if user.find('@') > 0:
      emailsettings.domain = user[user.find('@')+1:]
      user = user[:user.find('@')]
    else:
      emailsettings.domain = domain
    try_count = 0
    wait_on_fail = .5
    hard_fail = False
    while try_count < 10:
      try:
        signature = emailsettings.GetSignature(username=user)
        break
      except gdata.apps.service.AppsForYourDomainException, e:
        terminating_error = checkErrorCode(e)
        if not terminating_error:
          try_count = try_count + 1
          if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
          time.sleep(wait_on_fail)
          wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
          continue
        else:
          sys.stderr.write('Error: %s\n' % terminating_error)
          hard_fail = True
          break
    if try_count == 10 or hard_fail:
      sys.stderr.write('Giving up\n')
      continue
    sys.stderr.write("User %s signature:\n  " % (user+'@'+emailsettings.domain))
    print "%s" % signature['signature']

def doWebClips(users):
  if sys.argv[4].lower() == 'on':
    enable = True
  elif sys.argv[4].lower() == 'off':
    enable = False
  else:
    showUsage()
    sys.exit(2)
  emailsettings = getEmailSettingsObject()
  count = len(users)
  i = 1
  for user in users:
    if user.find('@') > 0:
      emailsettings.domain = user[user.find('@')+1:]
      user = user[:user.find('@')]
    else:
      emailsettings.domain = domain #make sure it's back at default domain
    print "Turning Web Clips %s for %s (%s of %s)" % (sys.argv[4], user+'@'+emailsettings.domain, i, count)
    i = i + 1
    try_count = 0
    wait_on_fail = .5
    hard_fail = False
    while try_count < 10:
      try:
        emailsettings.UpdateWebClipSettings(username=user, enable=enable)
        break
      except gdata.apps.service.AppsForYourDomainException, e:
        terminating_error = checkErrorCode(e)
        if not terminating_error:
          try_count = try_count + 1
          if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
          time.sleep(wait_on_fail)
          wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
          continue
        else:
          sys.stderr.write('Error: %s\n' % terminating_error)
          hard_fail = True
          break
    if try_count == 10 or hard_fail:
      sys.stderr.write('Giving up\n')
      continue

def doVacation(users):
  subject = message = ''
  if sys.argv[4] == 'on':
    enable = 'true'
  elif sys.argv[4] == 'off':
    enable = 'false'
  else:
    showUsage()
    sys.exit(2)
  contacts_only = domain_only = 'false'
  start_date = end_date = None
  i = 5
  while i < len(sys.argv):
    if sys.argv[i].lower() == 'subject':
      subject = sys.argv[i+1]
      i = i + 2
    elif sys.argv[i].lower() == 'message':
      message = sys.argv[i+1]
      i = i + 2
    elif sys.argv[i].lower() == 'contactsonly':
      contacts_only = 'true'
      i = i + 1
    elif sys.argv[i].lower() == 'domainonly':
      domain_only = 'true'
      i = i + 1
    elif sys.argv[i].lower() == 'startdate':
      start_date = sys.argv[i+1]
      i = i + 2
    elif sys.argv[i].lower() == 'enddate':
      end_date = sys.argv[i+1]
      i = i + 2
    elif sys.argv[i].lower() == 'file':
      fp = open(sys.argv[i+1], 'rb')
      message = fp.read()
      fp.close()
      i = i + 2
    else:
      showUsage()
      sys.exit(2)
  i = 1
  count = len(users)
  emailsettings = getEmailSettingsObject()
  message = cgi.escape(message).replace('\\n', '&#xA;').replace('"', "'")
  vacxml = '''<?xml version="1.0" encoding="utf-8"?>
<atom:entry xmlns:atom="http://www.w3.org/2005/Atom" xmlns:apps="http://schemas.google.com/apps/2006">
    <apps:property name="enable" value="%s" />''' % enable
  vacxml += '''<apps:property name="subject" value="%s" />
    <apps:property name="message" value="%s" />
    <apps:property name="contactsOnly" value="%s" />
    <apps:property name="domainOnly" value="%s" />''' % (subject, message, contacts_only, domain_only)
  if start_date != None:
    vacxml += '''<apps:property name="startDate" value="%s" />''' % start_date
  if end_date != None:
    vacxml += '''<apps:property name="endDate" value="%s" />''' % end_date
  vacxml += '</atom:entry>'
  for user in users:
    if user.find('@') > 0:
      emailsettings.domain = user[user.find('@')+1:]
      user = user[:user.find('@')]
    else:
      emailsettings.domain = domain #make sure it's back at default domain
    print "Setting Vacation for %s (%s of %s)" % (user+'@'+emailsettings.domain, i, count)
    uri = 'https://apps-apis.google.com/a/feeds/emailsettings/2.0/%s/%s/vacation' % (emailsettings.domain, user)
    i = i + 1
    try_count = 0
    wait_on_fail = .5
    hard_fail = False
    while try_count < 10:
      try:
        emailsettings.Put(vacxml, uri)
        break
      except gdata.apps.service.AppsForYourDomainException, e:
        terminating_error = checkErrorCode(e)
        if not terminating_error:
          try_count = try_count + 1
          if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
          time.sleep(wait_on_fail)
          wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
          continue
        else:
          sys.stderr.write('Error: %s\n' % terminating_error)
          hard_fail = True
          break
    if try_count == 10 or hard_fail:
      sys.stderr.write('Giving up\n')
      continue

def getVacation(users):
  emailsettings = getEmailSettingsObject()
  for user in users:
    if user.find('@') > 0:
      emailsettings.domain = user[user.find('@')+1:]
      user = user[:user.find('@')]
    else:
      emailsettings.domain = domain
    try_count = 0
    wait_on_fail = .5
    hard_fail = False
    while try_count < 10:
      try:
        vacationsettings = emailsettings.GetVacation(username=user)
        break
      except gdata.apps.service.AppsForYourDomainException, e:
        terminating_error = checkErrorCode(e)
        if not terminating_error:
          try_count = try_count + 1
          if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
          time.sleep(wait_on_fail)
          wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
          continue
        else:
          sys.stderr.write('Error: %s\n' % terminating_error)
          hard_fail = True
          break
    if try_count == 10 or hard_fail:
      sys.stderr.write('Giving up\n')
      continue
    print '''User %s
 Enabled: %s
 Contacts Only: %s
 Domain Only: %s
 Subject: %s
 Message: %s
 Start Date: %s
 End Date: %s
''' % (user+'@'+emailsettings.domain, vacationsettings['enable'], vacationsettings['contactsOnly'], vacationsettings['domainOnly'], vacationsettings['subject'], vacationsettings['message'], vacationsettings['startDate'], vacationsettings['endDate'])

def doCreateUser():
  gotFirstName = gotLastName = gotPassword = doOrg = False
  suspended = hash_function = change_password = ip_whitelisted = quota_in_gb = is_admin = agreed_to_terms = nohash = customer_id = None
  user_email = sys.argv[3]
  i = 4
  while i < len(sys.argv):
    if sys.argv[i].lower() == 'firstname':
      first_name = sys.argv[i+1]
      gotFirstName = True
      i = i + 2
    elif sys.argv[i].lower() == 'lastname':
      last_name = sys.argv[i+1]
      gotLastName = True
      i = i + 2
    elif sys.argv[i].lower() == 'password':
      password = sys.argv[i+1]
      gotPassword = True
      i = i + 2
    elif sys.argv[i].lower() == 'suspended':
      if sys.argv[i+1].lower() == 'on':
        suspended = True
      elif sys.argv[i+1].lower() == 'off':
        suspended = False
      else:
        print 'Error: suspended should be on or off, not %s' % sys.argv[i+1]
        sys.exit(5)
      i = i + 2
    elif sys.argv[i].lower() == 'sha' or sys.argv[i].lower() == 'sha1' or sys.argv[i].lower() == 'sha-1':
      hash_function = 'SHA-1'
      i = i + 1
    elif sys.argv[i].lower() == 'md5':
      hash_function = 'MD5'
      i = i + 1
    elif sys.argv[i].lower() == 'nohash':
      nohash = True
      i = i + 1
    elif sys.argv[i].lower() == 'quota':
      quota_in_gb = sys.argv[i+1]
      i = i + 2
    elif sys.argv[i].lower() == 'changepassword':
      if sys.argv[i+1] == 'on':
        change_password = True
      elif sys.argv[i+1] == 'off':
        change_password = False
      else:
        print 'Error: changepassword should be on or off, not %s' % sys.argv[i+1]
        sys.exit(5)
      i = i + 2
    elif sys.argv[i].lower() == 'ipwhitelisted':
      if sys.argv[i+1] == 'on':
        ip_whitelisted = True
      elif sys.argv[i+1] == 'off':
        ip_whitelisted = False
      else:
        print 'Error: ipwhitelisted should be on or off, not %s' % sys.argv[i+1]
      i = i + 2
    elif sys.argv[i].lower() == 'admin':
      if sys.argv[i+1] == 'on':
        is_admin = True
      elif sys.argv[i+1] == 'off':
        is_admin = False
      else:
        print 'Error: admin should be on or off, not %s' % sys.argv[i+1]
        sys.exit(5)
      i = i + 2
    elif sys.argv[i].lower() == 'agreedtoterms':
      if sys.argv[i+1] == 'on':
        agreed_to_terms = True
      elif sys.argv[i+1] == 'off':
        agreed_to_terms = False
      else:
        print 'Error: agreedtoterms should be on or off, not %s' % sys.argv[i+1]
        sys.exit(5)
      i = i + 2
    elif sys.argv[i].lower() == 'org' or sys.argv[i].lower() == 'ou':
      org = sys.argv[i+1]
      doOrg = True
      i = i + 2
    elif sys.argv[i].lower() == 'customerid':
      customer_id = sys.argv[i+1]
      i = i + 2
    else:
      showUsage()
      sys.exit(2)
  if not gotFirstName:
    first_name = 'Unknown'
  if not gotLastName:
    last_name = 'Unknown'
  if not gotPassword:
    password = ''.join(random.sample('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789~`!@#$%^&*()-=_+:;"\'{}[]\\|', 25))
  if hash_function == None and not nohash:
    newhash = sha1()
    newhash.update(password)
    password = newhash.hexdigest()
    hash_function = 'SHA-1'
  multi = getMultiDomainObject()
  if user_email.find('@') == -1:
    user_email = '%s@%s' % (user_email, domain)
  print "Creating account for %s" % user_email
  try_count = 0
  wait_on_fail = .5
  while try_count < 10:
    try:
      multi.CreateUser(user_email=user_email, last_name=last_name, first_name=first_name, password=password, suspended=suspended, quota_in_gb=quota_in_gb, hash_function=hash_function, change_password=change_password, is_admin=is_admin, agreed_to_terms=agreed_to_terms, ip_whitelisted=ip_whitelisted)
      break
    except gdata.apps.service.AppsForYourDomainException, e:
      terminating_error = checkErrorCode(e)
      if not terminating_error:
        try_count = try_count + 1
        if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
        time.sleep(wait_on_fail)
        wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
        continue
      else:
        sys.stderr.write('Error: %s\n' % terminating_error)
        sys.exit(e.error_code)
  if try_count == 10:
    sys.stderr.write('Giving up\n')
    sys.exit(e.error_code)
  if doOrg:
    orgObj = getOrgObject()
    print "Moving %s to org %s" % (user_email, org)
    try_count = 0
    wait_on_fail = .5
    while try_count < 10:
      try:
        orgObj.UpdateUserOrganization(user=user_email, new_name=org, customer_id=customer_id)
        break
      except gdata.apps.service.AppsForYourDomainException, e:
        terminating_error = checkErrorCode(e)
        if not terminating_error:
          try_count = try_count + 1
          if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
          time.sleep(wait_on_fail)
          wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
          continue
        else:
          sys.stderr.write('Error: %s\n' % terminating_error)
          sys.exit(e.error_code)
    if try_count == 10:
      sys.stderr.write('Giving up\n')
      sys.exit(e.error_code)

def doCreateGroup():
  group = sys.argv[3]
  got_name = False
  group_description = None
  group_permission = None
  i = 4
  while i < len(sys.argv):
    if sys.argv[i].lower() == 'name':
      group_name = sys.argv[i+1]
      got_name = True
      i = i + 2
    elif sys.argv[i].lower() == 'description':
      group_description = sys.argv[i+1]
      i = i + 2
    elif sys.argv[i].lower() == 'permission':
      group_permission = sys.argv[i+1]
      if group_permission.lower() == 'owner':
        group_permission = 'Owner'
      elif group_permission.lower() == 'member':
        group_permission = 'Member'
      elif group_permission.lower() == 'domain':
        group_permission = 'Domain'
      elif group_permission.lower() == 'anyone':
        group_permission = 'Anyone'
      else:
        showUsage()
        sys.exit(2)
      got_permission = True
      i = i + 2
  groupObj = getGroupsObject()
  if group.find('@') == -1:
    group = '%s@%s' % (group, groupObj.domain)
  if not got_name:
    group_name = group
  try_count = 0
  wait_on_fail = .5
  hard_fail = False
  while try_count < 10:
    try:
      result = groupObj.CreateGroup(group, group_name, group_description, group_permission)
      break
    except gdata.apps.service.AppsForYourDomainException, e:
      terminating_error = checkErrorCode(e)
      if not terminating_error:
        try_count = try_count + 1
        if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
        time.sleep(wait_on_fail)
        wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
        continue
      else:
        sys.stderr.write('Error: %s\n' % terminating_error)
        hard_fail = True
        break
  if try_count == 10 or hard_fail:
    sys.stderr.write('Giving up\n')
    sys.exit(e.error_code)

def doCreateNickName():
  alias_email = sys.argv[3]
  if sys.argv[4].lower() != 'user':
    showUsage()
    sys.exit(2)
  user_email = sys.argv[5]
  multi = getMultiDomainObject()
  if alias_email.find('@') == -1:
    alias_email = '%s@%s' % (alias_email, domain)
  if user_email.find('@') == -1:
    user_email = '%s@%s' % (user_email, domain)
  print 'Creating alias %s for user %s' % (alias_email, user_email)
  try_count = 0
  wait_on_fail = .5
  hard_fail = False
  while try_count < 10:
    try:
      multi.CreateAlias(user_email=user_email, alias_email=alias_email)
      break
    except gdata.apps.service.AppsForYourDomainException, e:
      terminating_error = checkErrorCode(e)
      if not terminating_error:
        try_count = try_count + 1
        if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
        time.sleep(wait_on_fail)
        wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
        continue
      else:
        sys.stderr.write('Error: %s\n' % terminating_error)
        hard_fail = True
        break
  if try_count == 10 or hard_fail:
    sys.stderr.write('Giving up\n')
    sys.exit(e.error_code)

def doCreateOrg():
  name = sys.argv[3]
  description = ''
  parent_org_unit_path = '/'
  block_inheritance = False
  i = 4
  while i < len(sys.argv):
    if sys.argv[i].lower() == 'description':
      description = sys.argv[i+1]
      i = i + 2
    elif sys.argv[i].lower() == 'parent':
      parent_org_unit_path = sys.argv[i+1]
      i = i + 2
    elif sys.argv[i].lower() == 'noinherit':
      block_inheritance = True
      i = i + 1
  org = getOrgObject()
  try_count = 0
  wait_on_fail = .5
  hard_fail = False
  while try_count < 10:
    try:
      org.CreateOrganizationUnit(name=name, description=description, parent_org_unit_path=parent_org_unit_path, block_inheritance=block_inheritance)
      break
    except gdata.apps.service.AppsForYourDomainException, e:
      terminating_error = checkErrorCode(e)
      if not terminating_error:
        try_count = try_count + 1
        if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
        time.sleep(wait_on_fail)
        wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
        continue
      else:
        sys.stderr.write('Error: %s\n' % terminating_error)
        hard_fail = True
        break
  if try_count == 10 or hard_fail:
    sys.stderr.write('Giving up\n')
    sys.exit(e.error_code)

def doCreateResource():
  id = sys.argv[3]
  common_name = sys.argv[4]
  description = None
  type = None
  i = 5
  while i < len(sys.argv):
    if sys.argv[i].lower() == 'description':
      description = sys.argv[i+1]
      i = i + 2
    elif sys.argv[i].lower() == 'type':
      type = sys.argv[i+1]
      i = i + 2
  rescal = getResCalObject()
  try_count = 0
  wait_on_fail = .5
  hard_fail = False
  while try_count < 10:
    try:
      rescal.CreateResourceCalendar(id=id, common_name=common_name, description=description, type=type)
      break
    except gdata.apps.service.AppsForYourDomainException, e:
      terminating_error = checkErrorCode(e)
      if not terminating_error:
        try_count = try_count + 1
        if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
        time.sleep(wait_on_fail)
        wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
        continue
      else:
        sys.stderr.write('Error: %s\n' % terminating_error)
        hard_fail = True
        break
  if try_count == 10 or hard_fail:
    sys.stderr.write('Giving up\n')
    sys.exit(e.error_code)

def doUpdateUser():
  gotPassword = isMD5 = isSHA1 = doOrg = False
  first_name = last_name = password = suspended = hash_function = change_password = ip_whitelisted = quota_in_gb = is_admin = agreed_to_terms = nohash = customer_id = None
  user_email = sys.argv[3]
  i = 4
  do_update_user = False
  do_rename_user = False
  while i < len(sys.argv):
    if sys.argv[i].lower() == 'firstname':
      do_update_user = True
      first_name = sys.argv[i+1]
      i = i + 2
    elif sys.argv[i].lower() == 'lastname':
      do_update_user = True
      last_name = sys.argv[i+1]
      i = i + 2
    elif sys.argv[i].lower() == 'username':
      new_email = sys.argv[i+1]
      do_rename_user = True
      i = i + 2
    elif sys.argv[i].lower() == 'password':
      do_update_user = True
      password = sys.argv[i+1]
      i = i + 2
      gotPassword = True
    elif sys.argv[i].lower() == 'admin':
      do_update_user = True
      if sys.argv[i+1].lower() == 'on':
        is_admin = True
      elif sys.argv[i+1].lower() == 'off':
        is_admin = False
      i = i + 2
    elif sys.argv[i].lower() == 'suspended':
      do_update_user = True
      if sys.argv[i+1].lower() == 'on':
        suspended = True
      elif sys.argv[i+1].lower() == 'off':
        suspended = False
      i = i + 2
    elif sys.argv[i].lower() == 'ipwhitelisted':
      do_update_user = True
      if sys.argv[i+1].lower() == 'on':
        ip_whitelisted = True
      elif sys.argv[i+1].lower() == 'off':
        ip_whitelisted = False
      i = i + 2
    elif sys.argv[i].lower() == 'sha1' or sys.argv[i].lower() == 'sha1' or sys.argv[i].lower() == 'sha-1':
      do_update_user = True
      hash_function = 'SHA-1'
      i = i + 1
      isSHA1 = True
    elif sys.argv[i].lower() == 'md5':
      do_update_user = True
      hash_function = 'MD5'
      i = i + 1
      isMD5 = True
    elif sys.argv[i].lower() == 'nohash':
      nohash = True
      i = i + 1
    elif sys.argv[i].lower() == 'changepassword':
      do_update_user = True
      if sys.argv[i+1].lower() == 'on':
        change_password = True
      elif sys.argv[i+1].lower() == 'off':
        change_password = False
      i = i + 2
    elif sys.argv[i].lower() == 'org' or sys.argv[i].lower() == 'ou':
      doOrg = True
      org = sys.argv[i+1]
      i = i + 2
    elif sys.argv[i].lower() == 'customerid':
      customer_id = sys.argv[i+1]
      i = i + 2
    elif sys.argv[i].lower() == 'agreedtoterms':
      do_update_user = True
      if sys.argv[i+1].lower() == 'on':
        agreed_to_terms = True
      elif sys.argv[i+1].lower() == 'off':
        agreed_to_terms = False
      i = i + 2
    else:
      showUsage()
      sys.exit(2)
  if gotPassword and not (isSHA1 or isMD5 or nohash):
    newhash = sha1()
    newhash.update(password)
    password = newhash.hexdigest()
    hash_function = 'SHA-1'
  multi = getMultiDomainObject()
  if user_email.find('@') == -1:
    user_email = '%s@%s' % (user_email, domain)
  if do_update_user:
    try_count = 0
    wait_on_fail = .5
    while try_count < 10:
      try:
        result = multi.UpdateUser(user_email=user_email, password=password, first_name=first_name, last_name=last_name, is_admin=is_admin, hash_function=hash_function,   
                       change_password=change_password, agreed_to_terms=agreed_to_terms,
                       suspended=suspended, ip_whitelisted=ip_whitelisted, quota_in_gb=quota_in_gb)
        break
      except gdata.apps.service.AppsForYourDomainException, e:
        terminating_error = checkErrorCode(e)
        if not terminating_error:
          try_count = try_count + 1
          if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
          time.sleep(wait_on_fail)
          wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
          continue
        else:
          sys.stderr.write('Error: %s\n' % terminating_error)
          sys.exit(e.error_code)
    if try_count == 10:
      sys.stderr.write('Giving up\n')
      sys.exit(e.error_code)
  if do_rename_user:
    try_count = 0
    wait_on_fail = .5
    while try_count < 10:
      try:
        multi.RenameUser(old_email=user_email, new_email=new_email)
        break
      except gdata.apps.service.AppsForYourDomainException, e:
        terminating_error = checkErrorCode(e)
        if not terminating_error:
          try_count = try_count + 1
          if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
          time.sleep(wait_on_fail)
          wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
          continue
        else:
          sys.stderr.write('Error: %s\n' % terminating_error)
          sys.exit(e.error_code)
    if try_count == 10:
      sys.stderr.write('Giving up\n')
      sys.exit(e.error_code)
  if doOrg:
    orgObj = getOrgObject()
    print "Moving %s to org %s" % (user_email, org)
    try_count = 0
    wait_on_fail = .5
    while try_count < 10:
      try:
        orgObj.UpdateUserOrganization(user=user_email, new_name=org, customer_id=customer_id)
        break
      except gdata.apps.service.AppsForYourDomainException, e:
        terminating_error = checkErrorCode(e)
        if not terminating_error:
          try_count = try_count + 1
          if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
          time.sleep(wait_on_fail)
          wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
          continue
        else:
          sys.stderr.write('Error: %s\n' % terminating_error)
          sys.exit(e.error_code)
    if try_count == 10:
      sys.stderr.write('Giving up\n')
      sys.exit(e.error_code)

def doUpdateGroup():
  groupObj = getGroupsObject()
  group = sys.argv[3]
  if group.find('@') == -1:
    group = group+'@'+domain
  if sys.argv[4].lower() == 'add':
    if sys.argv[5].lower() == 'owner':
      userType = 'Owner'
    elif sys.argv[5].lower() == 'member':
      userType = 'Member'
    user = sys.argv[6]
    if user != '*' and user.find('@') == -1:
      email = user+'@'+domain
    else:
      email = user
    if userType == 'Member':
      try_count = 0
      wait_on_fail = .5
      while try_count < 10:
        try:
          result = groupObj.AddMemberToGroup(email, group)
          break
        except gdata.apps.service.AppsForYourDomainException, e:
          terminating_error = checkErrorCode(e)
          if not terminating_error:
            try_count = try_count + 1
            if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
            time.sleep(wait_on_fail)
            wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
            continue
          else:
            sys.stderr.write('Error: %s\n' % terminating_error)
            sys.exit(e.error_code)
      if try_count == 10:
        sys.stderr.write('Giving up\n')
        sys.exit(e.error_code)
    elif userType == 'Owner':
      try_count = 0
      wait_on_fail = .5
      while try_count < 10:
        try:
          result2 = groupObj.AddOwnerToGroup(email, group)
          break
        except gdata.apps.service.AppsForYourDomainException, e:
          terminating_error = checkErrorCode(e)
          if not terminating_error:
            try_count = try_count + 1
            if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
            time.sleep(wait_on_fail)
            wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
            continue
          else:
            sys.stderr.write('Error: %s\n' % terminating_error)
            sys.exit(e.error_code)
      if try_count == 10:
        sys.stderr.write('Giving up\n')
        sys.exit(e.error_code)
  elif sys.argv[4].lower() == 'remove':
    if sys.argv[5].lower() == 'owner':
      userType = 'Owner'
    elif sys.argv[5].lower() == 'member':
      userType = 'Member'
    user = sys.argv[6]
    if user != '*' and user.find('@') == -1:
      email = user+'@'+domain
    else:
      email = user
    if userType == 'Member':
      try_count = 0
      wait_on_fail = .5
      while try_count < 10:
        try:
          result = groupObj.RemoveMemberFromGroup(email, group)
          break
        except gdata.apps.service.AppsForYourDomainException, e:
          terminating_error = checkErrorCode(e)
          if not terminating_error:
            try_count = try_count + 1
            if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
            time.sleep(wait_on_fail)
            wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
            continue
          else:
            sys.stderr.write('Error: %s\n' % terminating_error)
            sys.exit(e.error_code)
      if try_count == 10:
        sys.stderr.write('Giving up\n')
        sys.exit(e.error_code)
    elif userType == 'Owner':
      try_count = 0
      wait_on_fail = .5
      while try_count < 10:
        try:
          result = groupObj.RemoveOwnerFromGroup(email, group)
          break
        except gdata.apps.service.AppsForYourDomainException, e:
          terminating_error = checkErrorCode(e)
          if not terminating_error:
            try_count = try_count + 1
            if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
            time.sleep(wait_on_fail)
            wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
            continue
          else:
            sys.stderr.write('Error: %s\n' % terminating_error)
            sys.exit(e.error_code)
      if try_count == 10:
        sys.stderr.write('Giving up\n')
        sys.exit(e.error_code)

  else:
    i = 4
    use_prov_api = True
    if not sys.argv[i].lower() == 'settings':
      groupInfo = groupObj.RetrieveGroup(group)
      while i < len(sys.argv):
        if sys.argv[i].lower() == 'name':
          groupInfo['groupName'] = sys.argv[i+1]
          i = i + 2        
        elif sys.argv[i].lower() == 'description':
          groupInfo['description'] = sys.argv[i+1]
          i = i + 2
        elif sys.argv[i].lower() == 'permission':
          if sys.argv[i+1].lower() == 'owner':
            groupInfo['emailPermission'] = 'Owner'
          elif sys.argv[i+1].lower() == 'member':
            groupInfo['emailPermission'] = 'Member'
          elif sys.argv[i+1].lower() == 'domain':
            groupInfo['emailPermission'] = 'Domain'
          elif sys.argv[i+1].lower() == 'anyone':
            groupInfo['emailPermission'] = 'Anyone'
          i = i + 2
    else:
      use_prov_api = False
      i = i + 1
    if use_prov_api:
      try_count = 0
      wait_on_fail = .5
      while try_count < 10:
        try:
          result = groupObj.UpdateGroup(group, groupInfo['groupName'], groupInfo['description'], groupInfo['emailPermission'])
          break
        except gdata.apps.service.AppsForYourDomainException, e:
          terminating_error = checkErrorCode(e)
          if not terminating_error:
            try_count = try_count + 1
            if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
            time.sleep(wait_on_fail)
            wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
            continue
          else:
            sys.stderr.write('Error: %s\n' % terminating_error)
            sys.exit(e.error_code)
      if try_count == 10:
        sys.stderr.write('Giving up\n')
        sys.exit(e.error_code)
    else:
      allow_external_members = allow_google_communication = allow_web_posting = archive_only = custom_reply_to = default_message_deny_notification_text = description = is_archived = max_message_bytes = members_can_post_as_the_group = message_display_font = message_moderation_level = name = primary_language = reply_to = send_message_deny_notification = show_in_group_directory = who_can_invite =  who_can_join = who_can_post_message = who_can_view_group = who_can_view_membership = include_in_global_address_list = spam_moderation_level = None
      while i < len(sys.argv):
        if sys.argv[i].lower() == 'allow_external_members':
          allow_external_members = sys.argv[i+1].lower()
          if allow_external_members != 'true' and allow_external_members != 'false':
            print 'Error: Value for allow_external_members must be true or false. Got %s' % allow_external_members
            sys.exit(9)
          i = i + 2
        elif sys.argv[i].lower() == 'include_in_global_address_list':
          include_in_global_address_list = sys.argv[i+1].lower()
          if include_in_global_address_list != 'true' and include_in_global_address_list != 'false':
            print 'Error: Value for include_in_global_address_list must be true or false. Got %s' % include_in_global_address_list
            sys.exit(9)
          i = i + 2
        elif sys.argv[i].lower() == 'spam_moderation_level':
          spam_moderation_level = sys.argv[i+1].upper()
          if spam_moderation_level != 'ALLOW' and spam_moderation_level != 'MODERATE' and spam_moderation_level != 'SILENTLY_MODERATE' and spam_moderation_level != 'REJECT':
            print 'Error: Value for spam_moderation_level must be allow, moderate, silently_moderate or reject. Got %s' % spam_moderation_level
            sys.exit(9)
          i = i + 2
        elif sys.argv[i].lower() == 'message_moderation_level':
          message_moderation_level = sys.argv[i+1].upper()
          if message_moderation_level != 'MODERATE_ALL_MESSAGES' and message_moderation_level != 'MODERATE_NEW_MEMBERS' and message_moderation_level != 'MODERATE_NONE' and message_moderation_level != 'MODERATE_NON_MEMBERS':
            print 'Error: Value for message_moderation_level must be moderate_all_messages, moderate_new_members, moderate_none or moderate_non_members. Got %s' % allow_external_members
            sys.exit(9)
          i = i + 2
        elif sys.argv[i].lower() == 'name':
          name = sys.argv[i+1]
          i = i + 2
        elif sys.argv[i].lower() == 'primary_language':
          primary_language = sys.argv[i+1]
          i = i + 2
        elif sys.argv[i].lower() == 'reply_to':
          reply_to = sys.argv[i+1].upper()
          if reply_to != 'REPLY_TO_CUSTOM' and reply_to != 'REPLY_TO_IGNORE' and reply_to != 'REPLY_TO_LIST' and reply_to != 'REPLY_TO_MANAGERS' and reply_to != 'REPLY_TO_OWNER' and reply_to != 'REPLY_TO_SENDER':
            print 'Error: Value for reply_to must be reply_to_custom, reply_to_ignore, reply_to_list, reply_to_managers, reply_to_owner or reply_to_sender. Got %s' % reply_to
            sys.exit(9)
          i = i + 2
        elif sys.argv[i].lower() == 'send_message_deny_notification':
          send_message_deny_notification = sys.argv[i+1].lower()
          if send_message_deny_notification != 'true' and send_message_deny_notification != 'false':
            print 'Error: Value for send_message_deny_notification must be true or false. Got %s' % send_message_deny_notification
            sys.exit(9)
          i = i + 2
        elif sys.argv[i].lower() == 'show_in_groups_directory' or sys.argv[i].lower() == 'show_in_group_directory':
          show_in_group_directory = sys.argv[i+1].lower()
          if show_in_group_directory != 'true' and show_in_group_directory != 'false':
            print 'Error: Value for show_in_group_directory must be true or false. Got %s' % show_in_group_directory
            sys.exit(9)
          i = i + 2
        elif sys.argv[i].lower() == 'who_can_invite':
          who_can_invite = sys.argv[i+1].upper()
          if who_can_invite != 'ALL_MANAGERS_CAN_INVITE' and who_can_invite != 'ALL_MEMBERS_CAN_INVITE':
            print 'Error: Value for who_can_invite must be all_managers_can_invite or all_members_can_invite. Got %s' % who_can_invite
            sys.exit(9)
          i = i + 2
        elif sys.argv[i].lower() == 'who_can_join':
          who_can_join = sys.argv[i+1].upper()
          if who_can_join != 'ALL_IN_DOMAIN_CAN_JOIN' and who_can_join != 'ANYONE_CAN_JOIN' and who_can_join != 'CAN_REQUEST_TO_JOIN' and who_can_join != 'INVITED_CAN_JOIN':
            print 'Error: Value for who_can_join must be all_in_domain_can_join, anyone_can_join, can_request_to_join or invited_can_join. Got %s' % who_can_join
            sys.exit(9)
          i = i + 2
        elif sys.argv[i].lower() == 'who_can_post_message':
          who_can_post_message = sys.argv[i+1].upper()
          if who_can_post_message != 'ALL_IN_DOMAIN_CAN_POST' and who_can_post_message != 'ALL_MANAGERS_CAN_POST' and who_can_post_message != 'ALL_MEMBERS_CAN_POST' and who_can_post_message != 'ANYONE_CAN_POST' and who_can_post_message != 'NONE_CAN_POST':
            print 'Error: Value for who_can_post_message must be all_in_domain_can_post, all_managers_can_post, all_members_can_post, anyone_can_post or none_can_post. Got %s' % who_can_post_message
            sys.exit(9)
          i = i + 2
        elif sys.argv[i].lower() == 'who_can_view_group':
          who_can_view_group = sys.argv[i+1].upper()
          if who_can_view_group != 'ALL_IN_DOMAIN_CAN_VIEW' and who_can_view_group != 'ALL_MANAGERS_CAN_VIEW' and who_can_view_group != 'ALL_MEMBERS_CAN_VIEW' and who_can_view_group != 'ANYONE_CAN_VIEW':
            print 'Error: Value for who_can_view_group must be all_in_domain_can_view, all_managers_can_view, all_members_can_view or anyone_can_view. Got %s' % who_can_view_group
            sys.exit(9)
          i = i + 2
        elif sys.argv[i].lower() == 'who_can_view_membership':
          who_can_view_membership = sys.argv[i+1].upper()
          if who_can_view_membership != 'ALL_IN_DOMAIN_CAN_VIEW' and who_can_view_membership != 'ALL_MANAGERS_CAN_VIEW' and who_can_view_membership != 'ALL_MEMBERS_CAN_VIEW':
            print 'Error: Value for who_can_view_membership must be all_in_domain_can_view, all_managers_can_view or all_members_can_view. Got %s' % who_can_view_membership
            sys.exit(9)
          i = i + 2
        elif sys.argv[i].lower() == 'allow_google_communication':
          allow_google_communication = sys.argv[i+1].lower()
          if allow_google_communication != 'true' and allow_google_communication != 'false':
            print 'Error: Value for allow_google_communication must be true or false. Got %s' % allow_google_communication
            sys.exit(9)
          i = i + 2
        elif sys.argv[i].lower() == 'allow_web_posting':
          allow_web_posting = sys.argv[i+1].lower()
          if allow_web_posting != 'true' and allow_web_posting != 'false':
            print 'Error: Value for allow_web_posting must be true or false. Got %s' % allow_web_posting
            sys.exit(9)
          i = i + 2
        elif sys.argv[i].lower() == 'archive_only':
          archive_only = sys.argv[i+1].lower()
          if archive_only != 'true' and archive_only != 'false':
            print 'Error: Value for archive_only must be true or false. Got %s' % archive_only
            sys.exit(9)
          i = i + 2
        elif sys.argv[i].lower() == 'custom_reply_to':
          custom_reply_to = sys.argv[i+1]
          i = i + 2
        elif sys.argv[i].lower() == 'default_message_deny_notification_text':
          default_message_deny_notification_text = sys.argv[i+1]
          i = i + 2
        elif sys.argv[i].lower() == 'description':
          description = sys.argv[i+1]
          i = i + 2
        elif sys.argv[i].lower() == 'is_archived':
          is_archived = sys.argv[i+1].lower()
          if is_archived != 'true' and is_archived != 'false':
            print 'Error: Value for is_archived must be true or false. Got %s' % is_archived
            sys.exit(9)
          i = i + 2
        elif sys.argv[i].lower() == 'max_message_bytes':
          max_message_bytes = sys.argv[i+1]
          try:
            if max_message_bytes[-1:].upper() == 'M':
              max_message_bytes = str(int(max_message_bytes[:-1]) * 1024 * 1024)
            elif max_message_bytes[-1:].upper() == 'K':
              max_message_bytes = str(int(max_message_bytes[:-1]) * 1024)
            elif max_message_bytes[-1].upper() == 'B':
              max_message_bytes = str(int(max_message_bytes[:-1]))
            else:
              max_message_bytes = str(int(max_message_bytes))
          except ValueError:
            print 'Error: max_message_bytes must be a number ending with M (megabytes), K (kilobytes) or nothing (bytes). Got %s' % max_message_bytes
            sys.exit(9)
          i = i + 2
        elif sys.argv[i].lower() == 'members_can_post_as_the_group':
          members_can_post_as_the_group = sys.argv[i+1].lower()
          if members_can_post_as_the_group != 'true' and members_can_post_as_the_group != 'false':
            print 'Error: Value for members_can_post_as_the_group must be true or false. Got %s' % members_can_post_as_the_group
            sys.exit(9)
          i = i + 2
        elif sys.argv[i].lower() == 'message_display_font':
          message_display_font = sys.argv[i+1].upper()
          if message_display_font != 'DEFAULT_FONT' and message_display_font != 'FIXED_WIDTH_FONT':
            print 'Error: Value for message_display_font must be default_font or fixed_width_font. Got %s' % message_display_font
            sys.exit(9)
          i = i + 2
        else:
          print 'Error: %s is not a valid setting for groups' % sys.argv[i]
          sys.exit(10)
      gs = getGroupSettingsObject()
      try_count = 0
      wait_on_fail = .5
      while try_count < 10:
        try:
          results = gs.UpdateGroupSettings(group_email=group, allow_external_members=allow_external_members, allow_google_communication=allow_google_communication, allow_web_posting=allow_web_posting, archive_only=archive_only, custom_reply_to=custom_reply_to, default_message_deny_notification_text=default_message_deny_notification_text, description=description, is_archived=is_archived, max_message_bytes=max_message_bytes, members_can_post_as_the_group=members_can_post_as_the_group, message_display_font=message_display_font, message_moderation_level=message_moderation_level, name=name, primary_language=primary_language, reply_to=reply_to, send_message_deny_notification=send_message_deny_notification, show_in_group_directory=show_in_group_directory, who_can_invite=who_can_invite, who_can_join=who_can_join, who_can_post_message=who_can_post_message, who_can_view_group=who_can_view_group, who_can_view_membership=who_can_view_membership, include_in_global_address_list=include_in_global_address_list, spam_moderation_level=spam_moderation_level)
          break
        except gdata.service.RequestError, e:
          if e[0]['status'] == 503 and e[0]['reason'] == 'Service Unavailable':
            try_count = try_count + 1
            group_name = group[:group.find('@')]
            group_domain = group[group.find('@')+1:]
            print 'Working around Google backend error. Opening group and sleeping %s sec(s)...\n' % str(wait_on_fail)
            try:
              url = 'https://groups.google.com/a/%s/group/%s' % (group_domain, group_name)
              b = urllib2.urlopen(url)
              b.read(100)
              b.close()
            except urllib2.HTTPError:
              pass
            time.sleep(wait_on_fail)
            wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
            continue
          print 'Error: %s - %s' % (e[0]['reason'], e[0]['body'])
          sys.exit(e[0]['status'])
        except gdata.apps.service.AppsForYourDomainException, e:
          terminating_error = checkErrorCode(e)
          if not terminating_error:
            try_count = try_count + 1
            if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
            time.sleep(wait_on_fail)
            wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
            continue
          else:
            sys.stderr.write('Error: %s\n' % terminating_error)
            sys.exit(e.error_code)
      if try_count == 10:
        sys.stderr.write('Giving up\n')
        sys.exit(e.error_code)

def doUpdateNickName():
  alias_email = sys.argv[3]
  if sys.argv[4].lower() != 'user':
    showUsage()
    sys.exit(2)
  user_email = sys.argv[5]
  multi = getMultiDomainObject()
  try_count = 0
  wait_on_fail = .5
  while try_count < 10:
    try:
      multi.DeleteAlias(alias_email=alias_email)
      break
    except gdata.apps.service.AppsForYourDomainException, e:
      terminating_error = checkErrorCode(e)
      if not terminating_error:
        try_count = try_count + 1
        if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
        time.sleep(wait_on_fail)
        wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
        continue
      else:
        sys.stderr.write('Error: %s\n' % terminating_error)
        sys.exit(e.error_code)
  if try_count == 10:
    sys.stderr.write('Giving up\n')
    sys.exit(e.error_code)
  try_count = 0
  wait_on_fail = .5
  while try_count < 10:
    try:
      multi.CreateAlias(user_email=user_email, alias_email=alias_email)
      break
    except gdata.apps.service.AppsForYourDomainException, e:
      terminating_error = checkErrorCode(e)
      if not terminating_error:
        try_count = try_count + 1
        if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
        time.sleep(wait_on_fail)
        wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
        continue
      else:
        sys.stderr.write('Error: %s\n' % terminating_error)
        sys.exit(e.error_code)
  if try_count == 10:
    sys.stderr.write('Giving up\n')
    sys.exit(e.error_code)

def doUpdateResourceCalendar():
  id = sys.argv[3]
  common_name = None
  description = None
  type = None
  i = 4
  while i < len(sys.argv):
    if sys.argv[i].lower() == 'name':
      common_name = sys.argv[i+1]
      i = i + 2
    elif sys.argv[i].lower() == 'description':
      description = sys.argv[i+1]
      i = i + 2
    elif sys.argv[i].lower() == 'type':
      type = sys.argv[i+1]
      i = i + 2
  rescal = getResCalObject()
  try_count = 0
  wait_on_fail = .5
  while try_count < 10:
    try:
      rescal.UpdateResourceCalendar(id=id, common_name=common_name, description=description, type=type)
      break
    except gdata.apps.service.AppsForYourDomainException, e:
      terminating_error = checkErrorCode(e)
      if not terminating_error:
        try_count = try_count + 1
        if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
        time.sleep(wait_on_fail)
        wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
        continue
      else:
        sys.stderr.write('Error: %s\n' % terminating_error)
        sys.exit(e.error_code)
  if try_count == 10:
    sys.stderr.write('Giving up\n')
    sys.exit(e.error_code)

def doUpdateOrg():
  name = sys.argv[3]
  new_name = None
  description = None
  parent_org_unit_path = None
  block_inheritance = None
  users_to_move = []
  org = getOrgObject()
  users = []
  i = 4
  if sys.argv[4].lower() == 'add':
    users = sys.argv[5].split(' ')
    i = 6
  elif sys.argv[4].lower() == 'fileadd' or sys.argv[4].lower() == 'addfile':
    users = []
    filename = sys.argv[5]
    usernames = csv.reader(open(filename, 'rb'))
    for row in usernames:
      users.append(row.pop())
    i = 6
  elif sys.argv[4].lower() == 'groupadd'or sys.argv[4].lower() == 'addgroup':
    groupsObj = getGroupsObject()
    group = sys.argv[5]
    members = groupsObj.RetrieveAllMembers(group)
    for member in members:
      users.append(member['memberId'])
    i = 6
  elif sys.argv[4].lower() == 'addnotingroup':
    print 'Retrieving all users in Google Apps Organization (may take some time)'
    allorgusersresults = org.RetrieveAllOrganizationUsers()
    print 'Retrieved %s users' % len(allorgusersresults)
    for auser in allorgusersresults:
      users.append(auser['orgUserEmail'])
    group = sys.argv[5]
    print 'Retrieving all members of %s group (may take some time)' % group
    groupsObj = getGroupsObject()
    members = groupsObj.RetrieveAllMembers(group)
    for member in members:
      try:
        users.remove(member['memberId'])
      except ValueError:
        continue
    i = 6
  totalusers = len(users)
  currentrange = 1
  while len(users) > 25:
    while len(users_to_move) < 25:
      users_to_move.append(users.pop())
    print "Adding users %s to %s out of %s total to org %s" % (currentrange, currentrange+24, totalusers, name)
    try_count = 0
    wait_on_fail = .5
    while try_count < 10:
      try:
        org.UpdateOrganizationUnit(old_name=name, users_to_move=users_to_move)
        break
      except gdata.apps.service.AppsForYourDomainException, e:
        if e.error_code == 1301 and (e.invalidInput[-19:] == ',orgUnitUsersToMove' or e.invalidInput[:19] == 'orgUnitUsersToMove,'):
          invalid_user = e.invalidInput[:e.invalidInput.find(',')]
          if invalid_user == 'orgUnitUsersToMove':
            invalid_user = e.invalidInput[e.invalidInput.find(',')+1:]
          print 'Error: %s not valid, skipping' % invalid_user
          users_to_move.remove(invalid_user)
          continue
        terminating_error = checkErrorCode(e)
        if not terminating_error:
          try_count = try_count + 1
          if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
          time.sleep(wait_on_fail)
          wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
          continue
        else:
          sys.stderr.write('Error: %s\n' % terminating_error)
          sys.exit(e.error_code)
    if try_count == 10:
      sys.stderr.write('Giving up\n')
      sys.exit(e.error_code)
    currentrange = currentrange + 25
    users_to_move = []
    continue
  while len(users) > 0:
    users_to_move.append(users.pop())
  if len(users_to_move) < 1:
    users_to_move = None
  else:
    print 'Adding users %s to %s and making other updates to org %s' % (currentrange, totalusers, name)
  while i < len(sys.argv):
    if sys.argv[i].lower() == 'name':
      new_name = sys.argv[i+1]
      i = i + 2
    elif sys.argv[i].lower() == 'description':
      description = sys.argv[i+1]
      i = i + 2
    elif sys.argv[i].lower() == 'parent':
      parent_org_unit_path = sys.argv[i+1]
      i = i + 2
    elif sys.argv[i].lower() == 'noinherit':
      block_inheritance = True
      i = i + 1
    elif sys.argv[i].lower() == 'inherit':
      block_inheritance = False
      i = i + 1
  try_count = 0
  wait_on_fail = .5
  while try_count < 10:
    try:
      org.UpdateOrganizationUnit(old_name=name, new_name=new_name, description=description, parent_org_unit_path=parent_org_unit_path, block_inheritance=block_inheritance, users_to_move=users_to_move)
      break
    except gdata.apps.service.AppsForYourDomainException, e:
      if e.error_code == 1301 and (e.invalidInput[-19:] == ',orgUnitUsersToMove' or e.invalidInput[:19] == 'orgUnitUsersToMove,'):
        invalid_user = e.invalidInput[:e.invalidInput.find(',')]
        if invalid_user == 'orgUnitUsersToMove':
          invalid_user = e.invalidInput[e.invalidInput.find(',')+1:]
        print 'Error: %s not valid, skipping' % invalid_user
        users_to_move.remove(invalid_user)
        continue
      terminating_error = checkErrorCode(e)
      if not terminating_error:
        try_count = try_count + 1
        if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
        time.sleep(wait_on_fail)
        wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
        continue
      else:
        sys.stderr.write('Error: %s\n' % terminating_error)
        sys.exit(e.error_code)
  if try_count == 10:
    sys.stderr.write('Giving up\n')
    sys.exit(e.error_code)

def doWhatIs():
  email = sys.argv[2]
  multi = getMultiDomainObject()
  if email.find('@') == -1:
    email = '%s@%s' % (email, multi.domain)
  try_count = 0
  wait_on_fail = .5
  while try_count < 10:
    try:
      user = multi.RetrieveAlias(email)
      sys.stderr.write('%s is an alias\n\n' % email)
      doGetNickNameInfo(alias_email=email)
      return
    except gdata.apps.service.AppsForYourDomainException, e:
      terminating_error = checkErrorCode(e)
      if not terminating_error:
        try_count = try_count + 1
        if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
        time.sleep(wait_on_fail)
        wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
        continue
      elif e.error_code == 1301:
        sys.stderr.write('%s is not an alias...\n' % email)
        break
      else:
        sys.stderr.write('Error: %s\n' % terminating_error)
        sys.exit(e.error_code)
  if try_count == 10:
    sys.stderr.write('Giving up\n')
    sys.exit(e.error_code)
  try_count = 0
  wait_on_fail = .5
  while try_count < 10:
    try:
      user = multi.RetrieveUser(email)
      sys.stderr.write('%s is a user\n\n' % email)
      doGetUserInfo(user_email=email)
      return
    except gdata.apps.service.AppsForYourDomainException, e:
      terminating_error = checkErrorCode(e)
      if not terminating_error:
        try_count = try_count + 1
        if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
        time.sleep(wait_on_fail)
        wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
        continue
      elif e.error_code == 1301:
        sys.stderr.write('%s is not a user...\n' % email)
        break
      else:
        sys.stderr.write('Error: %s\n' % terminating_error)
        sys.exit(e.error_code)
  if try_count == 10:
    sys.stderr.write('Giving up\n')
    sys.exit(e.error_code)
  groupObj = getGroupsObject()
  try_count = 0
  wait_on_fail = .5
  while try_count < 10:
    try:
      user = groupObj.RetrieveGroup(email)
      sys.stderr.write('%s is a group\n\n' % email)
      doGetGroupInfo(group_name=email)
      return
    except gdata.apps.service.AppsForYourDomainException, e:
      terminating_error = checkErrorCode(e)
      if not terminating_error:
        try_count = try_count + 1
        if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
        time.sleep(wait_on_fail)
        wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
        continue
      elif e.error_code == 1301:
        sys.stderr.write('%s is not a group either. Email address doesn\'t seem to exist!\n' % email)
        return
      else:
        sys.stderr.write('Error: %s\n' % terminating_error)
        sys.exit(e.error_code)
  if try_count == 10:
    sys.stderr.write('Giving up\n')
    sys.exit(e.error_code)
  try_count = 0
  wait_on_fail = .5
  while try_count < 10:
    try:
      user = multi.RetrieveAlias(email)
      sys.stderr.write('%s is an alias\n\n' % email)
      doGetNickNameInfo(alias_email=email)
      return
    except gdata.apps.service.AppsForYourDomainException, e:
      terminating_error = checkErrorCode(e)
      if not terminating_error:
        try_count = try_count + 1
        if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
        time.sleep(wait_on_fail)
        wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
        continue
      elif e.error_code == 1301:
        sys.stderr.write('Not an alias...\n')
        break
      else:
        sys.stderr.write('Error: %s\n' % terminating_error)
        sys.exit(e.error_code)
  if try_count == 10:
    sys.stderr.write('Giving up\n')
    sys.exit(e.error_code)

def doGetUserInfo(user_email=None):
  if user_email == None:
    user_email = sys.argv[3]
  getAliases = getGroups = getOrg = True
  i = 4
  while i < len(sys.argv):
    if sys.argv[i].lower() == 'noaliases':
      getAliases = False
      i = i + 1
    elif sys.argv[i].lower() == 'nogroups':
      getGroups = False
      i = i + 1
    elif sys.argv[i].lower() == 'noorg':
      getOrg = False
      i = i + 1
  multi = getMultiDomainObject()
  try_count = 0
  wait_on_fail = .5
  while try_count < 10:
    try:
      user = multi.RetrieveUser(user_email)
      break
    except gdata.apps.service.AppsForYourDomainException, e:
      terminating_error = checkErrorCode(e)
      if not terminating_error:
        try_count = try_count + 1
        if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
        time.sleep(wait_on_fail)
        wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
        continue
      else:
        sys.stderr.write('Error: %s\n' % terminating_error)
        sys.exit(e.error_code)
  if try_count == 10:
    sys.stderr.write('Giving up\n')
    sys.exit(e.error_code)
  print 'User: %s' % user['userEmail']
  print 'First Name: %s' % user['firstName']
  print 'Last Name: %s' % user['lastName']
  print 'Is an admin: %s' % user['isAdmin']
  print 'Has agreed to terms: %s' % user['agreedToTerms']
  print 'IP Whitelisted: %s' % user['ipWhitelisted']
  print 'Account Suspended: %s' % user['isSuspended']
  print 'Must Change Password: %s' % user['isChangePasswordAtNextLogin']
  if getOrg:
    orgObj = getOrgObject()
    try_count = 0
    wait_on_fail = .5
    while try_count < 10:
      try:
        user_org = orgObj.RetrieveUserOrganization(user_email)
        break
      except gdata.apps.service.AppsForYourDomainException, e:
        terminating_error = checkErrorCode(e)
        if not terminating_error:
          try_count = try_count + 1
          if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
          time.sleep(wait_on_fail)
          wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
          continue
        else:
          sys.stderr.write('Error: %s\n' % terminating_error)
          sys.exit(e.error_code)
    if try_count == 10:
      sys.stderr.write('Giving up\n')
      sys.exit(e.error_code)
    print 'Organization: %s' % user_org['orgUnitPath']
  if getAliases:
    print 'Email Aliases (Nicknames):'
    try_count = 0
    wait_on_fail = .5
    while try_count < 10:
      try:
        nicknames = multi.GetUserAliases(user_email)
        break
      except gdata.apps.service.AppsForYourDomainException, e:
        terminating_error = checkErrorCode(e)
        if not terminating_error:
          try_count = try_count + 1
          if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
          time.sleep(wait_on_fail)
          wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
          continue
        else:
          sys.stderr.write('Error: %s\n' % terminating_error)
          sys.exit(e.error_code)
    if try_count == 10:
      sys.stderr.write('Giving up\n')
      sys.exit(e.error_code)
    for nick in nicknames:
      print '  ' + nick['aliasEmail']
  if getGroups:
    groupObj = getGroupsObject()
    groupObj.domain = multi.domain
    try_count = 0
    wait_on_fail = .5
    while try_count < 10:
      try:
        groups = groupObj.RetrieveGroups(user_email)
        break
      except gdata.apps.service.AppsForYourDomainException, e:
        terminating_error = checkErrorCode(e)
        if not terminating_error:
          try_count = try_count + 1
          if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
          time.sleep(wait_on_fail)
          wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
          continue
        else:
          sys.stderr.write('Error: %s\n' % terminating_error)
          sys.exit(e.error_code)
    if try_count == 10:
      sys.stderr.write('Giving up\n')
      sys.exit(e.error_code)
    print 'Groups:'
    for group in groups:
      if group['directMember'] == 'true':
        directIndirect = 'direct'
      else:
        directIndirect = 'indirect'
      print '  ' + group['groupName'] + ' <' + group['groupId'] + '> (' + directIndirect + ' member)'
   
def doGetGroupInfo(group_name=None):
  if group_name == None:
    group_name = sys.argv[3]
  show_group_settings = False
  try:
    if sys.argv[4].lower() == 'settings':
      show_group_settings = True
  except IndexError:
    pass
  if not show_group_settings:
    groupObj = getGroupsObject()
    if group_name.find('@') == -1:
      group_name = group_name+'@'+domain
    try_count = 0
    wait_on_fail = .5
    while try_count < 10:
      try:
        group = groupObj.RetrieveGroup(group_name)
        break
      except gdata.apps.service.AppsForYourDomainException, e:
        terminating_error = checkErrorCode(e)
        if not terminating_error:
          try_count = try_count + 1
          if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
          time.sleep(wait_on_fail)
          wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
          continue
        else:
          sys.stderr.write('Error: %s\n' % terminating_error)
          sys.exit(e.error_code)
    if try_count == 10:
      sys.stderr.write('Giving up\n')
      sys.exit(e.error_code)
    print 'Group Name: ',group['groupName']
    try:
      print 'Email Permission: ',group['emailPermission']
    except KeyError:
      print 'Email Permission: Unknown'
    print 'Group ID: ',group['groupId']
    print 'Description: ',group['description']
    try_count = 0
    wait_on_fail = .5
    while try_count < 10:
      try:
        owners = groupObj.RetrieveAllOwners(group_name, suspended_users=True)
        break
      except gdata.apps.service.AppsForYourDomainException, e:
        terminating_error = checkErrorCode(e)
        if not terminating_error:
          try_count = try_count + 1
          if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
          time.sleep(wait_on_fail)
          wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
          continue
        else:
          sys.stderr.write('Error: %s\n' % terminating_error)
          sys.exit(e.error_code)
    if try_count == 10:
      sys.stderr.write('Giving up\n')
      sys.exit(e.error_code)
    owner_list = []
    for owner in owners:
      owner_list.append(owner['email'])
    try_count = 0
    wait_on_fail = .5
    while try_count < 10:
      try:
        members = groupObj.RetrieveAllMembers(group_name, suspended_users=True)
        break
      except gdata.apps.service.AppsForYourDomainException, e:
        terminating_error = checkErrorCode(e)
        if not terminating_error:
          try_count = try_count + 1
          if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
          time.sleep(wait_on_fail)
          wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
          continue
        else:
          sys.stderr.write('Error: %s\n' % terminating_error)
          sys.exit(e.error_code)
    if try_count == 10:
      sys.stderr.write('Giving up\n')
      sys.exit(e.error_code)
    users = []
    for member in members:
      users.append(member)
    for user in users:
      if user['memberId'] in owner_list:
        print 'Owner: %s  Type: %s  Direct Member: %s' % (user['memberId'], user['memberType'], user['directMember'])
        owner_list.remove(user['memberId'])
      else:
        print 'Member: %s  Type: %s  Direct Member: %s' % (user['memberId'], user['memberType'], user['directMember'])
    # remaining owners are owners but not members
    for non_member_owner in owner_list:
      print 'Non-member owner: %s' % non_member_owner
  else: # show group settings
    gs = getGroupSettingsObject()
    if group_name.find('@') == -1:
      group_name = group_name+'@'+gs.domain
    try_count = 0
    wait_on_fail = .5
    while try_count < 10:
      try:
        settings = gs.RetrieveGroupSettings(group_name)
        break
      except gdata.service.RequestError, e:
        if e[0]['status'] == 503 and e[0]['reason'] == 'Service Unavailable':
          try_count = try_count + 1
          group_username = group_name[:group_name.find('@')]
          group_domain = group_name[group_name.find('@')+1:]
          sys.stderr.write('Working around Google backend error. Opening group and sleeping %s sec(s)...\n' % str(wait_on_fail))
          try:
            url = 'https://groups.google.com/a/%s/group/%s' % (group_domain, group_username)
            b = urllib2.urlopen(url)
            b.read(100)
            b.close()
          except urllib2.HTTPError:
            pass
          time.sleep(wait_on_fail)
          wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
          continue
        sys.stderr.write('Error: %s - %s' % (e[0]['reason'], e[0]['body']))
        sys.exit(e[0]['status'])
      except gdata.apps.service.AppsForYourDomainException, e:
        terminating_error = checkErrorCode(e)
        if not terminating_error:
          try_count = try_count + 1
          if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
          time.sleep(wait_on_fail)
          wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
          continue
        else:
          sys.stderr.write('Error: %s\n' % terminating_error)
          sys.exit(e.error_code)
    if try_count == 10:
      sys.stderr.write('Giving up\n')
      sys.exit(e.error_code)
    print ''
    print 'Group Settings:'
    for setting in settings:
      setting_key = re.sub(r'([A-Z])', r'_\1', setting.keys()[0]).lower()
      setting_value = setting.values()[0]
      if setting_value == None:
        setting_value = ''
      setting_value = setting_value
      print ' %s: %s' % (setting_key, setting_value)

def doGetNickNameInfo(alias_email=None):
  if alias_email == None:
    alias_email = sys.argv[3]
  multi = getMultiDomainObject()
  try_count = 0
  wait_on_fail = .5
  while try_count < 10:
    try:
      result = multi.RetrieveAlias(alias_email=alias_email)
      break
    except gdata.apps.service.AppsForYourDomainException, e:
      terminating_error = checkErrorCode(e)
      if not terminating_error:
        try_count = try_count + 1
        if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
        time.sleep(wait_on_fail)
        wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
        continue
      else:
        sys.stderr.write('Error: %s\n' % terminating_error)
        sys.exit(e.error_code)
  if try_count == 10:
    sys.stderr.write('Giving up\n')
    sys.exit(e.error_code)
  print ' Alias Email: '+result['aliasEmail']
  print ' User Email: '+result['userEmail']

def doGetResourceCalendarInfo():
  id = sys.argv[3]
  rescal = getResCalObject()
  try_count = 0
  wait_on_fail = .5
  while try_count < 10:
    try:
      result = rescal.RetrieveResourceCalendar(id)
      break
    except gdata.apps.service.AppsForYourDomainException, e:
      terminating_error = checkErrorCode(e)
      if not terminating_error:
        try_count = try_count + 1
        if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
        time.sleep(wait_on_fail)
        wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
        continue
      else:
        sys.stderr.write('Error: %s\n' % terminating_error)
        sys.exit(e.error_code)
  if try_count == 10:
    sys.stderr.write('Giving up\n')
    sys.exit(e.error_code)
  print ' Resource ID: '+result['resourceId']
  print ' Common Name: '+result['resourceCommonName']
  print ' Email: '+result['resourceEmail']
  try:
    print ' Type: '+result['resourceType']
  except KeyError:
    print ' Type: '
  try:
    print ' Description: '+result['resourceDescription']
  except KeyError:
    print ' Description: '

def doGetOrgInfo():
  name = sys.argv[3]
  org = getOrgObject()
  try_count = 0
  wait_on_fail = .5
  while try_count < 10:
    try:
      result = org.RetrieveOrganizationUnit(name)
      break
    except gdata.apps.service.AppsForYourDomainException, e:
      terminating_error = checkErrorCode(e)
      if not terminating_error:
        try_count = try_count + 1
        if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
        time.sleep(wait_on_fail)
        wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
        continue
      else:
        sys.stderr.write('Error: %s\n' % terminating_error)
        sys.exit(e.error_code)
  if try_count == 10:
    sys.stderr.write('Giving up\n')
    sys.exit(e.error_code)
  print 'Organization Unit: '+result['name']
  if result['description'] != None:
    print 'Description: '+result['description']
  else:
    print 'Description: '
  if result['parentOrgUnitPath'] != None:
    print 'Parent Org: '+result['parentOrgUnitPath']
  else:
    print 'Parent Org: /'
  print 'Block Inheritance: '+result['blockInheritance']
  result2 = org.RetrieveAllOrganizationUnitUsers(name)
  print 'Users: '
  for user in result2:
    print ' '+user['orgUserEmail']

def doUpdateDomain():
  adminObj = getAdminSettingsObject()
  command = sys.argv[3].lower()
  if command == 'language':
    language = sys.argv[4]
    try_count = 0
    wait_on_fail = .5
    while try_count < 10:
      try:
        adminObj.UpdateDefaultLanguage(language)
        break
      except gdata.apps.service.AppsForYourDomainException, e:
        terminating_error = checkErrorCode(e)
        if not terminating_error:
          try_count = try_count + 1
          if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
          time.sleep(wait_on_fail)
          wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
          continue
        else:
          sys.stderr.write('Error: %s\n' % terminating_error)
          sys.exit(e.error_code)
    if try_count == 10:
      sys.stderr.write('Giving up\n')
      sys.exit(e.error_code)
  elif command == 'name':
    name = sys.argv[4]
    try_count = 0
    wait_on_fail = .5
    while try_count < 10:
      try:
        adminObj.UpdateOrganizationName(name)
        break
      except gdata.apps.service.AppsForYourDomainException, e:
        terminating_error = checkErrorCode(e)
        if not terminating_error:
          try_count = try_count + 1
          if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
          time.sleep(wait_on_fail)
          wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
          continue
        else:
          sys.stderr.write('Error: %s\n' % terminating_error)
          sys.exit(e.error_code)
    if try_count == 10:
      sys.stderr.write('Giving up\n')
      sys.exit(e.error_code)
  elif command == 'admin_secondary_email':
    admin_secondary_email = sys.argv[4]
    try_count = 0
    wait_on_fail = .5
    while try_count < 10:
      try:
        adminObj.UpdateAdminSecondaryEmail(admin_secondary_email)
        break
      except gdata.apps.service.AppsForYourDomainException, e:
        terminating_error = checkErrorCode(e)
        if not terminating_error:
          try_count = try_count + 1
          if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
          time.sleep(wait_on_fail)
          wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
          continue
        else:
          sys.stderr.write('Error: %s\n' % terminating_error)
          sys.exit(e.error_code)
    if try_count == 10:
      sys.stderr.write('Giving up\n')
      sys.exit(e.error_code)
  elif command == 'logo':
    logo_file = sys.argv[4]
    try:
      fp = open(logo_file, 'rb')
      logo_image = fp.read()
      fp.close()
    except IOError:
      print 'Error: can\'t open file %s' % logo_file
      sys.exit(11)
    try_count = 0
    wait_on_fail = .5
    while try_count < 10:
      try:
        adminObj.UpdateDomainLogo(logo_image)
        break
      except gdata.apps.service.AppsForYourDomainException, e:
        terminating_error = checkErrorCode(e)
        if not terminating_error:
          try_count = try_count + 1
          if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
          time.sleep(wait_on_fail)
          wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
          continue
        else:
          sys.stderr.write('Error: %s\n' % terminating_error)
          sys.exit(e.error_code)
    if try_count == 10:
      sys.stderr.write('Giving up\n')
      sys.exit(e.error_code)
  elif command == 'cname_verify':
    try_count = 0
    wait_on_fail = .5
    while try_count < 10:
      try:
        result = adminObj.UpdateCNAMEVerificationStatus()
        break
      except gdata.apps.service.AppsForYourDomainException, e:
        terminating_error = checkErrorCode(e)
        if not terminating_error:
          try_count = try_count + 1
          if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
          time.sleep(wait_on_fail)
          wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
          continue
        else:
          if e[0]['status'] == 400:
            print 'Record Name: Error - Google disabled this function.'
            print 'Verification Method: Error - Google disabled this function.'
            print 'Verified: Error - Google disabled this functino.'
            break
          sys.stderr.write('Error: %s\n' % terminating_error)
          sys.exit(e.error_code)
    if try_count == 10:
      sys.stderr.write('Giving up\n')
      sys.exit(e.error_code)
    try:
      print 'Record Name: %s' % result['recordName']
      print 'Verification Method: %s' % result['verificationMethod']
      print 'Verified: %s' % result['verified']
    except UnboundLocalError:
      pass
  elif command == 'mx_verify':
    try_count = 0
    wait_on_fail = .5
    while try_count < 10:
      try:
        result = adminObj.UpdateMXVerificationStatus()
        break
      except gdata.apps.service.AppsForYourDomainException, e:
        terminating_error = checkErrorCode(e)
        if not terminating_error:
          try_count = try_count + 1
          if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
          time.sleep(wait_on_fail)
          wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
          continue
        else:
          sys.stderr.write('Error: %s\n' % terminating_error)
          sys.exit(e.error_code)
    if try_count == 10:
      sys.stderr.write('Giving up\n')
      sys.exit(e.error_code)
    print 'Verification Method: %s' % result['verificationMethod']
    print 'Verified: %s' % result['verified']
  elif command == 'sso_settings':
    enableSSO = samlSignonUri = samlLogoutUri = changePasswordUri = ssoWhitelist = useDomainSpecificIssuer = None
    i = 4
    while i < len(sys.argv):
      if sys.argv[i].lower() == 'enabled':
        if sys.argv[i+1].lower() == 'true':
          enableSSO = True
        elif sys.argv[i+1].lower() == 'false':
          enableSSO = False
        else:
          print 'Error: value for enabled must be true or false, got %s' % sys.argv[i+1]
          exit(9)
        i = i + 2
      elif sys.argv[i].lower() == 'sign_on_uri':
        samlSignonUri = sys.argv[i+1]
        i = i + 2
      elif sys.argv[i].lower() == 'sign_out_uri':
        samlLogoutUri = sys.argv[i+1]
        i = i + 2
      elif sys.argv[i].lower() == 'password_uri':
        changePasswordUri = sys.argv[i+1]
        i = i + 2
      elif sys.argv[i].lower() == 'whitelist':
        ssoWhitelist = sys.argv[i+1]
        i = i + 2
      elif sys.argv[i].lower() == 'use_domain_specific_issuer':
        if sys.argv[i+1].lower() == 'true':
          useDomainSpecificIssuer = True
        elif sys.argv[i+1].lower() == 'false':
          useDomainSpecificIssuer = False
        else:
          print 'Error: value for use_domain_specific_issuer must be true or false, got %s' % sys.argv[i+1]
          sys.exit(9)
        i = i + 2 
      else:
        print 'Error: unknown option for "gam update domain sso_settings...": %s' % sys.argv[i]
        sys.exit(9)
    try_count = 0
    wait_on_fail = .5
    while try_count < 10:
      try:
        adminObj.UpdateSSOSettings(enableSSO=enableSSO, samlSignonUri=samlSignonUri, samlLogoutUri=samlLogoutUri, changePasswordUri=changePasswordUri, ssoWhitelist=ssoWhitelist, useDomainSpecificIssuer=useDomainSpecificIssuer)
        break
      except gdata.apps.service.AppsForYourDomainException, e:
        terminating_error = checkErrorCode(e)
        if not terminating_error:
          try_count = try_count + 1
          if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
          time.sleep(wait_on_fail)
          wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
          continue
        else:
          sys.stderr.write('Error: %s\n' % terminating_error)
          sys.exit(e.error_code)
    if try_count == 10:
      sys.stderr.write('Giving up\n')
      sys.exit(e.error_code)
  elif command == 'sso_key':
    key_file = sys.argv[4]
    try:
      fp = open(key_file, 'rb')
      key_data = fp.read()
      fp.close()
    except IOError:
      print 'Error: can\'t open file %s' % logo_file
      sys.exit(11)
    try_count = 0
    wait_on_fail = .5
    while try_count < 10:
      try:
        adminObj.UpdateSSOKey(key_data)
        break
      except gdata.apps.service.AppsForYourDomainException, e:
        terminating_error = checkErrorCode(e)
        if not terminating_error:
          try_count = try_count + 1
          if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
          time.sleep(wait_on_fail)
          wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
          continue
        else:
          sys.stderr.write('Error: %s\n' % terminating_error)
          sys.exit(e.error_code)
    if try_count == 10:
      sys.stderr.write('Giving up\n')
      sys.exit(e.error_code)
  elif command == 'user_migrations':
    value = sys.argv[4].lower()
    if value != 'true' and value != 'false':
      print 'Error: value for user_migrations must be true or false, got %s' % sys.argv[4]
      sys.exit(9)
    try_count = 0
    wait_on_fail = .5
    while try_count < 10:
      try:
        result = adminObj.UpdateUserMigrationStatus(value)
        break
      except gdata.apps.service.AppsForYourDomainException, e:
        terminating_error = checkErrorCode(e)
        if not terminating_error:
          try_count = try_count + 1
          if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
          time.sleep(wait_on_fail)
          wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
          continue
        else:
          sys.stderr.write('Error: %s\n' % terminating_error)
          sys.exit(e.error_code)
    if try_count == 10:
      sys.stderr.write('Giving up\n')
      sys.exit(e.error_code)
  elif command == 'outbound_gateway':
    gateway = sys.argv[4]
    mode = sys.argv[6].upper()
    try_count = 0
    wait_on_fail = .5
    while try_count < 10:
      try:
        result = adminObj.UpdateOutboundGatewaySettings(gateway, mode)
        break
      except gdata.apps.service.AppsForYourDomainException, e:
        terminating_error = checkErrorCode(e)
        if not terminating_error:
          try_count = try_count + 1
          if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
          time.sleep(wait_on_fail)
          wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
          continue
        else:
          sys.stderr.write('Error: %s\n' % terminating_error)
          sys.exit(e.error_code)
      except TypeError, e:
        if gateway == "":
          break
        else:
          print e
          exit(3)
    if try_count == 10:
      sys.stderr.write('Giving up\n')
      sys.exit(e.error_code)
  elif command == 'email_route':
    i = 4
    while i < len(sys.argv):
      if sys.argv[i].lower() == 'destination':
        destination = sys.argv[i+1]
        i = i + 2
      elif sys.argv[i].lower() == 'rewrite_to':
        rewrite_to = sys.argv[i+1].lower()
        if rewrite_to == 'true':
          rewrite_to = True
        elif rewrite_to == 'false':
          rewrite_to = False
        else: 
          print 'Error: value for rewrite_to must be true or false, got %s' % sys.argv[i+1]
          sys.exit(9)
        i = i + 2
      elif sys.argv[i].lower() == 'enabled':
        enabled = sys.argv[i+1].lower()
        if enabled == 'true':
          enabled = True
        elif enabled == 'false':
          enabled = False
        else:
          print 'Error: value for enabled must be true or false, got %s' % sys.argv[i+1]
          sys.exit(9)
        i = i + 2
      elif sys.argv[i].lower() == 'bounce_notifications':
        bounce_notifications = sys.argv[i+1].lower()
        if bounce_notifications == 'true':
          bounce_notifications = True
        elif bounce_notifications == 'false':
          bounce_notifications = False
        else:
          print 'Error: value for bounce_notifications must be true or false, got %s' % sys.argv[i+1]
          sys.exit(9)
        i = i + 2
      elif sys.argv[i].lower() == 'account_handling':
        account_handling = sys.argv[i+1].lower()
        if account_handling == 'all_accounts':
          account_handling = 'allAccounts'
        elif account_handling == 'provisioned_accounts':
          account_handling = 'provisionedAccounts'
        elif account_handling == 'unknown_accounts':
          account_handling = 'unknownAccounts'
        else:
          print 'Error: value for account_handling must be all_accounts, provisioned_account or unknown_accounts. Got %s' % sys.argv[i+1]
          sys.exit(9)
        i = i + 2
      else:
        print 'Error: invalid setting for "gam update domain email_route..."'
        sys.exit(10)
    try_count = 0
    wait_on_fail = .5
    while try_count < 10:
      try:
        response = adminObj.AddEmailRoute(routeDestination=destination, routeRewriteTo=rewrite_to, routeEnabled=enabled, bounceNotifications=bounce_notifications, accountHandling=account_handling)
        break
      except gdata.apps.service.AppsForYourDomainException, e:
        terminating_error = checkErrorCode(e)
        if not terminating_error:
          try_count = try_count + 1
          if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
          time.sleep(wait_on_fail)
          wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
          continue
        else:
          sys.stderr.write('Error: %s\n' % terminating_error)
          sys.exit(e.error_code)
    if try_count == 10:
      sys.stderr.write('Giving up\n')
      sys.exit(e.error_code)
  else:
    print 'Error: that is not a valid "gam update domain" command'

def doGetDomainInfo():
  adminObj = getAdminSettingsObject()
  if len(sys.argv) > 4 and sys.argv[3].lower() == 'logo':
    target_file = sys.argv[4]
    logo_image = adminObj.GetDomainLogo()
    try:
      fp = open(target_file, 'wb')
      fp.write(logo_image)
      fp.close()
    except IOError:
      print 'Error: can\'t open file %s for writing' % target_file
      sys.exit(11)
    sys.exit(0)
  print 'Google Apps Domain: ', adminObj.domain
  try_count = 0
  wait_on_fail = .5
  while try_count < 10:
    try:
      default_language = adminObj.GetDefaultLanguage()
      break
    except gdata.apps.service.AppsForYourDomainException, e:
      terminating_error = checkErrorCode(e)
      if not terminating_error:
        try_count = try_count + 1
        if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
        time.sleep(wait_on_fail)
        wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
        continue
      else:
        sys.stderr.write('Error: %s\n' % terminating_error)
        sys.exit(e.error_code)
  if try_count == 10:
    sys.stderr.write('Giving up\n')
    sys.exit(e.error_code)
  print 'Default Language: %s' % default_language
  try_count = 0
  wait_on_fail = .5
  while try_count < 10:
    try:
      org_name = adminObj.GetOrganizationName()
      break
    except gdata.apps.service.AppsForYourDomainException, e:
      terminating_error = checkErrorCode(e)
      if not terminating_error:
        try_count = try_count + 1
        if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
        time.sleep(wait_on_fail)
        wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
        continue
      else:
        sys.stderr.write('Error: %s\n' % terminating_error)
        sys.exit(e.error_code)
  if try_count == 10:
    sys.stderr.write('Giving up\n')
    sys.exit(e.error_code)
  print 'Organization Name: %s' % org_name
  try_count = 0
  wait_on_fail = .5
  while try_count < 10:
    try:
      max_users = adminObj.GetMaximumNumberOfUsers()
      break
    except gdata.apps.service.AppsForYourDomainException, e:
      terminating_error = checkErrorCode(e)
      if not terminating_error:
        try_count = try_count + 1
        if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
        time.sleep(wait_on_fail)
        wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
        continue
      else:
        sys.stderr.write('Error: %s\n' % terminating_error)
        sys.exit(e.error_code)
  if try_count == 10:
    sys.stderr.write('Giving up\n')
    sys.exit(e.error_code)
  print 'Maximum Users: %s' % max_users
  try_count = 0
  wait_on_fail = .5
  while try_count < 10:
    try:
      current_users = adminObj.GetCurrentNumberOfUsers()
      break
    except gdata.apps.service.AppsForYourDomainException, e:
      terminating_error = checkErrorCode(e)
      if not terminating_error:
        try_count = try_count + 1
        if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
        time.sleep(wait_on_fail)
        wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
        continue
      else:
        sys.stderr.write('Error: %s\n' % terminating_error)
        sys.exit(e.error_code)
  if try_count == 10:
    sys.stderr.write('Giving up\n')
    sys.exit(e.error_code)
  print 'Current Users: %s' % current_users
  try_count = 0
  wait_on_fail = .5
  while try_count < 10:
    try:
      is_dom_verified = adminObj.IsDomainVerified()
      break
    except gdata.apps.service.AppsForYourDomainException, e:
      terminating_error = checkErrorCode(e)
      if not terminating_error:
        try_count = try_count + 1
        if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
        time.sleep(wait_on_fail)
        wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
        continue
      else:
        sys.stderr.write('Error: %s\n' % terminating_error)
        sys.exit(e.error_code)
  if try_count == 10:
    sys.stderr.write('Giving up\n')
    sys.exit(e.error_code)
  print 'Domain is Verified: %s' % is_dom_verified
  try_count = 0
  wait_on_fail = .5
  while try_count < 10:
    try:
      support_pin = adminObj.GetSupportPIN()
      break
    except gdata.apps.service.AppsForYourDomainException, e:
      terminating_error = checkErrorCode(e)
      if not terminating_error:
        try_count = try_count + 1
        if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
        time.sleep(wait_on_fail)
        wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
        continue
      else:
        sys.stderr.write('Error: %s\n' % terminating_error)
        sys.exit(e.error_code)
  if try_count == 10:
    sys.stderr.write('Giving up\n')
    sys.exit(e.error_code)
  print 'Support PIN: %s' % support_pin
  try_count = 0
  wait_on_fail = .5
  while try_count < 10:
    try:
      domain_edition = adminObj.GetEdition()
      break
    except gdata.apps.service.AppsForYourDomainException, e:
      terminating_error = checkErrorCode(e)
      if not terminating_error:
        try_count = try_count + 1
        if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
        time.sleep(wait_on_fail)
        wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
        continue
      else:
        sys.stderr.write('Error: %s\n' % terminating_error)
        sys.exit(e.error_code)
  if try_count == 10:
    sys.stderr.write('Giving up\n')
    sys.exit(e.error_code)
  print 'Domain Edition: %s' % domain_edition
  try_count = 0
  wait_on_fail = .5
  while try_count < 10:
    try:
      customer_pin = adminObj.GetCustomerPIN()
      break
    except gdata.apps.service.AppsForYourDomainException, e:
      terminating_error = checkErrorCode(e)
      if not terminating_error:
        try_count = try_count + 1
        if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
        time.sleep(wait_on_fail)
        wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
        continue
      else:
        sys.stderr.write('Error: %s\n' % terminating_error)
        sys.exit(e.error_code)
  if try_count == 10:
    sys.stderr.write('Giving up\n')
    sys.exit(e.error_code)
  print 'Customer PIN: %s' % customer_pin
  try_count = 0
  wait_on_fail = .5
  while try_count < 10:
    try:
      creation_time = adminObj.GetCreationTime()
      break
    except gdata.apps.service.AppsForYourDomainException, e:
      terminating_error = checkErrorCode(e)
      if not terminating_error:
        try_count = try_count + 1
        if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
        time.sleep(wait_on_fail)
        wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
        continue
      else:
        sys.stderr.write('Error: %s\n' % terminating_error)
        sys.exit(e.error_code)
  if try_count == 10:
    sys.stderr.write('Giving up\n')
    sys.exit(e.error_code)
  print 'Domain Creation Time: %s' % creation_time 
  org = getOrgObject()
  try_count = 0
  wait_on_fail = .5
  while try_count < 10:
    try:
      customer_id = org.RetrieveCustomerId()['customerId']
      break
    except gdata.apps.service.AppsForYourDomainException, e:
      terminating_error = checkErrorCode(e)
      if not terminating_error:
        try_count = try_count + 1
        if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
        time.sleep(wait_on_fail)
        wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
        continue
      else:
        sys.stderr.write('Error: %s\n' % terminating_error)
        sys.exit(e.error_code)
  if try_count == 10:
    sys.stderr.write('Giving up\n')
    sys.exit(e.error_code)
  print 'Customer ID: %s' % customer_id
  try_count = 0
  wait_on_fail = .5
  while try_count < 10:
    try:
      country_code = adminObj.GetCountryCode()
      break
    except gdata.apps.service.AppsForYourDomainException, e:
      terminating_error = checkErrorCode(e)
      if not terminating_error:
        try_count = try_count + 1
        if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
        time.sleep(wait_on_fail)
        wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
        continue
      else:
        sys.stderr.write('Error: %s\n' % terminating_error)
        sys.exit(e.error_code)
  if try_count == 10:
    sys.stderr.write('Giving up\n')
    sys.exit(e.error_code)
  print 'Domain Country Code: %s' % country_code
  try_count = 0
  wait_on_fail = .5
  while try_count < 10:
    try:
      admin_sec_email = adminObj.GetAdminSecondaryEmail()
      break
    except gdata.apps.service.AppsForYourDomainException, e:
      terminating_error = checkErrorCode(e)
      if not terminating_error:
        try_count = try_count + 1
        if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
        time.sleep(wait_on_fail)
        wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
        continue
      else:
        sys.stderr.write('Error: %s\n' % terminating_error)
        sys.exit(e.error_code)
  if try_count == 10:
    sys.stderr.write('Giving up\n')
    sys.exit(e.error_code)
  print 'Admin Secondary Email: %s' % admin_sec_email
  try_count = 0
  wait_on_fail = .5
  while try_count < 10:
    try:
      cnameverificationstatus = adminObj.GetCNAMEVerificationStatus()
      break
    except gdata.apps.service.AppsForYourDomainException, e:
      terminating_error = checkErrorCode(e)
      if not terminating_error:
        try_count = try_count + 1
        if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
        time.sleep(wait_on_fail)
        wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
        continue
      else:
        if e[0]['status'] == 400:
          print 'CNAME Verification Record Name: Error - Google disabled this function.'
          print 'CNAME Verification Verified: Error - Google disabled this function.'
          print 'CNAME Verification Method: Error - Google disabled this functino.'
          break
        sys.stderr.write('Error: %s\n' % terminating_error)
        sys.exit(e.error_code)
  if try_count == 10:
    sys.stderr.write('Giving up\n')
    sys.exit(e.error_code)
  try:
    print 'CNAME Verification Record Name: %s' % cnameverificationstatus['recordName']
    print 'CNAME Verification Verified: %s' % cnameverificationstatus['verified']
    print 'CNAME Verification Method: %s' %cnameverificationstatus['verificationMethod']
  except UnboundLocalError:
    pass
  try_count = 0
  wait_on_fail = .5
  while try_count < 10:
    try:
      mxverificationstatus = adminObj.GetMXVerificationStatus()
      break
    except gdata.apps.service.AppsForYourDomainException, e:
      terminating_error = checkErrorCode(e)
      if not terminating_error:
        try_count = try_count + 1
        if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
        time.sleep(wait_on_fail)
        wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
        continue
      else:
        sys.stderr.write('Error: %s\n' % terminating_error)
        sys.exit(e.error_code)
  if try_count == 10:
    sys.stderr.write('Giving up\n')
    sys.exit(e.error_code)
  print 'MX Verification Verified: ', mxverificationstatus['verified']
  print 'MX Verification Method: ', mxverificationstatus['verificationMethod']
  try_count = 0
  wait_on_fail = .5
  while try_count < 10:
    try:
      ssosettings = adminObj.GetSSOSettings()
      break
    except gdata.apps.service.AppsForYourDomainException, e:
      terminating_error = checkErrorCode(e)
      if not terminating_error:
        try_count = try_count + 1
        if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
        time.sleep(wait_on_fail)
        wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
        continue
      else:
        sys.stderr.write('Error: %s\n' % terminating_error)
        sys.exit(e.error_code)
  if try_count == 10:
    sys.stderr.write('Giving up\n')
    sys.exit(e.error_code)
  print 'SSO Enabled: ', ssosettings['enableSSO']
  print 'SSO Signon Page: ', ssosettings['samlSignonUri']
  print 'SSO Logout Page: ', ssosettings['samlLogoutUri']
  print 'SSO Password Page: ', ssosettings['changePasswordUri']
  print 'SSO Whitelist IPs: ', ssosettings['ssoWhitelist']
  print 'SSO Use Domain Specific Issuer: ', ssosettings['useDomainSpecificIssuer']
  try_count = 0
  wait_on_fail = .5
  while try_count < 10:
    try:
      ssokey = adminObj.GetSSOKey()
      break
    except gdata.apps.service.AppsForYourDomainException, e:
      terminating_error = checkErrorCode(e)
      if not terminating_error:
        try_count = try_count + 1
        if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
        time.sleep(wait_on_fail)
        wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
        continue
      elif terminating_error == '1408 - Invalid SSO Signing Key': # This always gets returned if SSO is disabled
        ssokey = {}
        break
      else:
        sys.stderr.write('Error: %s\n' % terminating_error)
        sys.exit(e.error_code)
  if try_count == 10:
    sys.stderr.write('Giving up\n')
    sys.exit(e.error_code)
  try:
    algorithm = str(ssokey['algorithm'])
    print 'SSO Key Algorithm: ' + algorithm
  except KeyError:
    pass
  try:
    format = str(ssokey['format'])
    print 'SSO Key Format: ' + format
  except KeyError:
    pass
  try:
    modulus = str(ssokey['modulus'])
    print 'SSO Key Modulus: ' + modulus
  except KeyError:
    pass
  try:
    exponent = str(ssokey['exponent'])
    print 'SSO Key Exponent: ' + exponent
  except KeyError:
    pass
  try:
    yValue = str(ssokey['yValue'])
    print 'SSO Key yValue: ' + yValue
  except KeyError:
    pass
  try:
    signingKey = str(ssokey['signingKey'])
    print 'Full SSO Key: ' + signingKey
  except KeyError:
    pass
  try_count = 0
  wait_on_fail = .5
  while try_count < 10:
    try:
      migration_status = adminObj.IsUserMigrationEnabled()
      break
    except gdata.apps.service.AppsForYourDomainException, e:
      terminating_error = checkErrorCode(e)
      if not terminating_error:
        try_count = try_count + 1
        if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
        time.sleep(wait_on_fail)
        wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
        continue
      else:
        sys.stderr.write('Error: %s\n' % terminating_error)
        sys.exit(e.error_code)
  if try_count == 10:
    sys.stderr.write('Giving up\n')
    sys.exit(e.error_code)
  print 'User Migration Enabled: ', str(migration_status)
  try_count = 0
  wait_on_fail = .5
  while try_count < 10:
    try:
      outbound_gateway_settings = {'smartHost': '', 'smtpMode': ''} # Initialize blank in case we get an 1801 Error
      outbound_gateway_settings = adminObj.GetOutboundGatewaySettings()
      break
    except gdata.apps.service.AppsForYourDomainException, e:
      terminating_error = checkErrorCode(e)
      if not terminating_error:
        try_count = try_count + 1
        if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
        time.sleep(wait_on_fail)
        wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
        continue
      elif e.error_code == 1801:
        break
      else:
        sys.stderr.write('Error: %s\n' % terminating_error)
        sys.exit(e.error_code)
  if try_count == 10:
    sys.stderr.write('Giving up\n')
    sys.exit(e.error_code)
  try:
    print 'Outbound Gateway Smart Host: ', outbound_gateway_settings['smartHost']
  except KeyError:
    print '' 
  try:
    print 'Outbound Gateway SMTP Mode: ', outbound_gateway_settings['smtpMode']
  except KeyError:
    print ''

def doDeleteUser():
  user_email = sys.argv[3]
  multi = getMultiDomainObject()
  if user_email.find('@') == -1:
    user_email = '%s@%s' % (user_email, multi.domain)
  do_rename = False
  try:
    if sys.argv[4].lower() == 'norename':
      do_rename = False
    elif sys.argv[4].lower() == 'dorename':
      do_rename = True
  except IndexError:
    pass
  print "Deleting account for %s" % (user_email)
  #Rename the user to a random string, this allows the user to be recreated
  #immediately instead of waiting the usual 5 days
  user_to_delete = user_email
  if do_rename:
    timestamp = time.strftime("%Y%m%d%H%M%S")
    user_name = user_email[:user_email.find('@')]
    user_domain = user_email[user_email.find('@')+1:]
    renameduser = user_name[:43]+'-'+timestamp+'-'    # include max 43 chars of username so there's room for datestamp and some randomness
    randomstring = ''.join(random.sample('abcdefghijklmnopqrstuvwxyz0123456789', 25))
    renameduser = renameduser+randomstring
    renameduser = renameduser[:64]
    renameduser_email = '%s@%s' % (renameduser, user_domain)
    try_count = 0
    wait_on_fail = .5
    while try_count < 10:
      try:
        rename_result = multi.RenameUser(old_email=user_email, new_email=renameduser_email)
        break
      except gdata.apps.service.AppsForYourDomainException, e:
        terminating_error = checkErrorCode(e)
        if not terminating_error:
          try_count = try_count + 1
          if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
          time.sleep(wait_on_fail)
          wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
          continue
        else:
          sys.stderr.write('Error: %s\n' % terminating_error)
          sys.exit(e.error_code)
    if try_count == 10:
      sys.stderr.write('Giving up\n')
      sys.exit(e.error_code)
    print 'Renamed %s to %s' % (user_email, renameduser_email)
    user_to_delete = renameduser_email
  try_count = 0
  wait_on_fail = .5
  while try_count < 10:
    try:
      multi.DeleteUser(user_to_delete)
      break
    except gdata.apps.service.AppsForYourDomainException, e:
      terminating_error = checkErrorCode(e)
      if not terminating_error:
        try_count = try_count + 1
        if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
        time.sleep(wait_on_fail)
        wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
        continue
      else:
        sys.stderr.write('Error: %s\n' % terminating_error)
        sys.exit(e.error_code)
  if try_count == 10:
    sys.stderr.write('Giving up\n')
    sys.exit(e.error_code)
  print 'Deleted user %s' % (user_to_delete)

def doDeleteGroup():
  group = sys.argv[3]
  groupObj = getGroupsObject()
  print "Deleting group %s" % group
  try_count = 0
  wait_on_fail = .5
  while try_count < 10:
    try:
      groupObj.DeleteGroup(group)
      break
    except gdata.apps.service.AppsForYourDomainException, e:
      terminating_error = checkErrorCode(e)
      if not terminating_error:
        try_count = try_count + 1
        if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
        time.sleep(wait_on_fail)
        wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
        continue
      else:
        sys.stderr.write('Error: %s\n' % terminating_error)
        sys.exit(e.error_code)
  if try_count == 10:
    sys.stderr.write('Giving up\n')
    sys.exit(e.error_code)

def doDeleteNickName(alias_email=None):
  if alias_email == None:
    alias_email = sys.argv[3]
  multi = getMultiDomainObject()
  print "Deleting alias %s" % alias_email
  try_count = 0
  wait_on_fail = .5
  while try_count < 10:
    try:
      multi.DeleteAlias(alias_email=alias_email)
      break
    except gdata.apps.service.AppsForYourDomainException, e:
      terminating_error = checkErrorCode(e)
      if not terminating_error:
        try_count = try_count + 1
        if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
        time.sleep(wait_on_fail)
        wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
        continue
      else:
        sys.stderr.write('Error: %s\n' % terminating_error)
        sys.exit(e.error_code)
  if try_count == 10:
    sys.stderr.write('Giving up\n')
    sys.exit(e.error_code)

def doDeleteResourceCalendar():
  res_id = sys.argv[3]
  rescal = getResCalObject()
  print "Deleting resource calendar %s" % res_id
  try_count = 0
  wait_on_fail = .5
  while try_count < 10:
    try:
      rescal.DeleteResourceCalendar(res_id)
      break
    except gdata.apps.service.AppsForYourDomainException, e:
      terminating_error = checkErrorCode(e)
      if not terminating_error:
        try_count = try_count + 1
        if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
        time.sleep(wait_on_fail)
        wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
        continue
      else:
        sys.stderr.write('Error: %s\n' % terminating_error)
        sys.exit(e.error_code)
  if try_count == 10:
    sys.stderr.write('Giving up\n')
    sys.exit(e.error_code)

def doDeleteOrg():
  name = sys.argv[3]
  org = getOrgObject()
  print "Deleting organization %s" % name
  try_count = 0
  wait_on_fail = .5
  while try_count < 10:
    try:
      org.DeleteOrganizationUnit(name)
      break
    except gdata.apps.service.AppsForYourDomainException, e:
      terminating_error = checkErrorCode(e)
      if not terminating_error:
        try_count = try_count + 1
        if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
        time.sleep(wait_on_fail)
        wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
        continue
      else:
        sys.stderr.write('Error: %s\n' % terminating_error)
        sys.exit(e.error_code)
  if try_count == 10:
    sys.stderr.write('Giving up\n')
    sys.exit(e.error_code)

def doPrintPostini():
  if os.path.isfile(getGamPath()+'postini-format.txt'):
    postini_format_file = open(getGamPath()+'postini-format.txt', 'rb')
    user_template = postini_format_file.readline()[0:-1]
    alias_template = postini_format_file.readline()[0:-1]
    group_template = postini_format_file.readline()
  else:
    user_template = 'adduser %user%'
    alias_template = 'addalias %user%, %alias%'
    group_template = 'addalias %list_owner%, %group%'
  try:
    list_owner = sys.argv[3]
  except IndexError:
    print 'You must include an email address that will own all group addresses'
    sys.exit(3)
  org = getOrgObject()
  sys.stderr.write("Getting all users in the %s organization (may take some time on a large Google Apps account)..." % org.domain)
  try_count = 0
  wait_on_fail = .5
  while try_count < 10:
    try:
      users = org.RetrieveAllOrganizationUsers()
      break
    except gdata.apps.service.AppsForYourDomainException, e:
      terminating_error = checkErrorCode(e)
      if not terminating_error:
        try_count = try_count + 1
        if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
        time.sleep(wait_on_fail)
        wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
        continue
      else:
        sys.stderr.write('Error: %s\n' % terminating_error)
        sys.exit(e.error_code)
  if try_count == 10:
    sys.stderr.write('Giving up\n')
    sys.exit(e.error_code)
  sys.stderr.write("done.\r\n")
  multi = getMultiDomainObject()
  sys.stderr.write("Getting all email aliases in the organization...")
  try_count = 0
  wait_on_fail = .5
  while try_count < 10:
    try:
      aliases = multi.RetrieveAllAliases()
      break
    except gdata.apps.service.AppsForYourDomainException, e:
      terminating_error = checkErrorCode(e)
      if not terminating_error:
        try_count = try_count + 1
        if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
        time.sleep(wait_on_fail)
        wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
        continue
      else:
        sys.stderr.write('Error: %s\n' % terminating_error)
        sys.exit(e.error_code)
  if try_count == 10:
    sys.stderr.write('Giving up\n')
    sys.exit(e.error_code)
  sys.stderr.write("done.\r\n")
  groupsObj = getGroupsObject()
  sys.stderr.write("Getting all groups in the organization...")
  try_count = 0
  wait_on_fail = .5
  while try_count < 10:
    try:
      groups = groupsObj.RetrieveAllGroups()
      break
    except gdata.apps.service.AppsForYourDomainException, e:
      terminating_error = checkErrorCode(e)
      if not terminating_error:
        try_count = try_count + 1
        if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
        time.sleep(wait_on_fail)
        wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
        continue
      else:
        sys.stderr.write('Error: %s\n' % terminating_error)
        sys.exit(e.error_code)
  if try_count == 10:
    sys.stderr.write('Giving up\n')
    sys.exit(e.error_code)
  sys.stderr.write("done.\r\n")
  print "# Begin Users"
  print ""
  for user in users:
    if user['orgUserEmail'][:2] == '.@' or user['orgUserEmail'][:11] == 'gcc_websvc@' or user['orgUserEmail'][-16:] == '@gtempaccount.com':  # not real users, skip em
        continue
    if user['orgUnitPath'] is None:
      user['orgUnitPath'] == ''
    print user_template.replace('%user%', str(user['orgUserEmail'])).replace('%ou%', str(user['orgUnitPath']))
  print ""
  print "# Begin Aliases"
  print ""
  for alias in aliases:
    print alias_template.replace('%user%', str(alias['userEmail'])).replace('%alias%', str(alias['aliasEmail']))
  print ""
  print "# Begin Groups"
  print ""
  for group in groups:
    print group_template.replace('%group%', str(group['groupId'])).replace('%name%', str(group['groupName'])).replace('%description%', str(group['description'])).replace('%list_owner%', list_owner)

def doPrintUsers():
  org = getOrgObject()
  i = 3
  getUserFeed = getNickFeed = getGroupFeed = False
  firstname = lastname = username = ou = suspended = changepassword = agreed2terms = admin = nicknames = groups = False
  user_attributes = []
  # the titles list ensures the CSV output has its parameters in the specified order. 
  # Python's dicts can be listed in any order, and the order often changes between the
  # header (user_attributes[0]) and the actual data rows.
  titles = ['Email']
  user_attributes.append({'Email': 'Email'})
  while i < len(sys.argv):
    if sys.argv[i].lower() == 'firstname':
      getUserFeed = True
      firstname = True
      user_attributes[0].update(Firstname='Firstname')
      titles.append('Firstname')
      i = i + 1
    elif sys.argv[i].lower() == 'lastname':
      getUserFeed = True
      lastname = True
      user_attributes[0].update(Lastname='Lastname')
      titles.append('Lastname')
      i = i + 1
    elif sys.argv[i].lower() == 'username':
      username = True
      user_attributes[0].update(Username='Username')
      titles.append('Username')
      i = i + 1
    elif sys.argv[i].lower() == 'ou':
      ou = True
      user_attributes[0].update(OU='OU')
      titles.append('OU')
      i = i + 1
    elif sys.argv[i].lower() == 'suspended':
      getUserFeed = True
      suspended = True
      user_attributes[0].update(Suspended='Suspended')
      titles.append('Suspended')
      i = i + 1
    elif sys.argv[i].lower() == 'changepassword':
      getUserFeed = True
      changepassword = True
      user_attributes[0].update(ChangePassword='ChangePassword')
      titles.append('ChangePassword')
      i = i + 1
    elif sys.argv[i].lower() == 'agreed2terms':
      getUserFeed = True
      agreed2terms = True
      user_attributes[0].update(AgreedToTerms='AgreedToTerms')
      titles.append('AgreedToTerms')
      i = i + 1
    elif sys.argv[i].lower() == 'admin':
      getUserFeed = True
      admin = True
      user_attributes[0].update(Admin='Admin')
      titles.append('Admin')
      i = i + 1
    elif sys.argv[i].lower() == 'nicknames' or sys.argv[i].lower() == 'aliases':
      getNickFeed = True
      nicknames = True
      user_attributes[0].update(Aliases='Aliases')
      titles.append('Aliases')
      i = i + 1
    elif sys.argv[i].lower() == 'groups':
      getGroupFeed = True
      groups = True
      user_attributes[0].update(Groups='Groups')
      titles.append('Groups')
      i = i + 1
    else:
      showUsage()
      exit(5)
  sys.stderr.write("Getting all users in the %s organization (may take some time on a large Google Apps account)... " % org.domain)
  try_count = 0
  wait_on_fail = .5
  while try_count < 10:
    try:
      all_users = org.RetrieveAllOrganizationUsers()
      break
    except gdata.apps.service.AppsForYourDomainException, e:
      terminating_error = checkErrorCode(e)
      if not terminating_error:
        try_count = try_count + 1
        if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
        time.sleep(wait_on_fail)
        wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
        continue
      else:
        sys.stderr.write('Error: %s\n' % terminating_error)
        sys.exit(e.error_code)
  if try_count == 10:
    sys.stderr.write('Giving up\n')
    sys.exit(e.error_code)
  sys.stderr.write("done.\r\n")
  for user in all_users:
    email = user['orgUserEmail'].lower()
    domain = email[email.find('@')+1:]
    if domain == 'gtempaccount.com':
      continue
    if email[:2] == '.@' or email[:11] == 'gcc_websvc@' or email[:27] == 'secure-data-connector-user@':  # not real users, skip em
      continue
    user_attributes.append({'Email': email})
    location = 0
    try:
      location = user_attributes.index({'Email': email})
      if username:
          user_attributes[location].update(Username=email[:email.find('@')])
      if ou:
          user_ou = user['orgUnitPath']
          if user_ou == None:
            user_ou = ''
          user_attributes[location].update(OU=user_ou)
    except ValueError:
      raise
    del(email, domain)
  del(all_users)
  total_users = len(user_attributes) - 1
  multi = getMultiDomainObject()
  if getUserFeed:
    sys.stderr.write("Getting details for all users... (may take some time on a large Google Apps account)... ")
    try_count = 0
    wait_on_fail = .5
    while try_count < 10:
      try:
        all_users = multi.RetrieveAllUsers()
        break
      except gdata.apps.service.AppsForYourDomainException, e:
        terminating_error = checkErrorCode(e)
        if not terminating_error:
          try_count = try_count + 1
          if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
          time.sleep(wait_on_fail)
          wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
          continue
        else:
          sys.stderr.write('Error: %s\n' % terminating_error)
          sys.exit(e.error_code)
      except socket.error, e:
        sys.stderr.write('Network Error, retrying\n')
        continue
    if try_count == 10:
      sys.stderr.write('Giving up\n')
      sys.exit(e.error_code)
    sys.stderr.write("done.\n")
    for user in all_users:
      email = user['userEmail'].lower()
      try:
        location = 0
        gotLocation = False
        while not gotLocation and location < len(user_attributes):
          location = location + 1
          try:
            if user_attributes[location]['Email'] == email:
              gotLocation = True
          except IndexError:
            continue
        if firstname:
          userfirstname = user['firstName']
          if userfirstname == None:
            userfirstname = ''
          try:
            user_attributes[location].update(Firstname=userfirstname)
          except IndexError:
            continue
        if lastname:
          userlastname = user['lastName']
          if userlastname == None:
            userlastname = ''
          try:
            user_attributes[location].update(Lastname=userlastname)
          except IndexError:
            continue
        if suspended:
          try:
            user_attributes[location].update(Suspended=user['isSuspended'])
          except IndexError:
            continue
        if agreed2terms:
          try:
            user_attributes[location].update(AgreedToTerms=user['agreedToTerms'])
          except IndexError:
            continue
        if changepassword:
          try:
            user_attributes[location].update(ChangePassword=user['isChangePasswordAtNextLogin'])
          except IndexError:
            continue
        if admin:
          try:
            user_attributes[location].update(Admin=user['isAdmin'])
          except IndexError:
            continue
      except ValueError:
        pass
      del (email)
  try:
    del(all_users)
  except UnboundLocalError:
    pass
  if getNickFeed:
    for user in user_attributes[1:]:
      user['Aliases'] = ''
    sys.stderr.write("Getting all email aliases in the organization... ")
    try_count = 0
    wait_on_fail = .5
    while try_count < 10:
      try:
        aliases = multi.RetrieveAllAliases()
        break
      except gdata.apps.service.AppsForYourDomainException, e:
        terminating_error = checkErrorCode(e)
        if not terminating_error:
          try_count = try_count + 1
          if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
          time.sleep(wait_on_fail)
          wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
          continue
        else:
          sys.stderr.write('Error: %s\n' % terminating_error)
          sys.exit(e.error_code)
    if try_count == 10:
      sys.stderr.write('Giving up\n')
      sys.exit(e.error_code)
    sys.stderr.write("done.\r\n")
    for alias in aliases:
      user_email = alias['userEmail'].lower()
      alias_email = alias['aliasEmail'].lower()
      try:
        location = 0
        gotLocation = False
        while not gotLocation and location < len(user_attributes):
          location = location + 1
          if user_attributes[location]['Email'] == user_email:
            gotLocation = True
        user_attributes[location]['Aliases'] += '%s ' % alias_email
      except IndexError:
        continue
    for user in user_attributes[1:]:
      if user['Aliases'][-1:] == ' ':
        user['Aliases'] = user['Aliases'][:-1]
  try:
    del(aliases)
  except UnboundLocalError:
    pass
  if getGroupFeed:
    groupsObj = getGroupsObject()
    user_count = 1
    for user in user_attributes[1:]:
      sys.stderr.write("Getting Group Membership for %s (%s/%s)\r\n" % (user['Email'], user_count, total_users))
      username = user['Email'][:user['Email'].find('@')]
      groups = []
      try_count = 0
      wait_on_fail = .5
      while try_count < 10:
        try:
          groups = groupsObj.RetrieveGroups(user['Email'])
          break
        except gdata.apps.service.AppsForYourDomainException, e:
          terminating_error = checkErrorCode(e)
          if not terminating_error:
            try_count = try_count + 1
            if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
            time.sleep(wait_on_fail)
            wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
            continue
          else:
            sys.stderr.write('Error: %s\n' % terminating_error)
            sys.exit(e.error_code)
      if try_count == 10:
        sys.stderr.write('Giving up\n')
        sys.exit(e.error_code)
      grouplist = ''
      for groupname in groups:
        grouplist += groupname['groupId']+' '
      if grouplist[-1:] == ' ':
        grouplist = grouplist[:-1]
      user.update(Groups=grouplist)
      user_count = user_count + 1
      del (username, groups, grouplist)
  csv.register_dialect('nixstdout', lineterminator='\n')
  writer = csv.DictWriter(sys.stdout, fieldnames=titles, dialect='nixstdout', quoting=csv.QUOTE_MINIMAL)
  writer.writerows(user_attributes)      

def doPrintGroups():
  i = 3
  printname = printdesc = printperm = usedomain = nousermanagedgroups = onlyusermanagedgroups = members = owners = settings = False
  group_attributes = []
  group_attributes.append({'GroupID': 'GroupID'})
  titles = ['GroupID']
  while i < len(sys.argv):
    if sys.argv[i].lower() == 'name':
      printname = True
      group_attributes[0].update(Name='Name')
      titles.append('Name')
      i = i + 1
    elif sys.argv[i].lower() == 'description':
      group_attributes[0].update(Description='Description')
      titles.append('Description')
      printdesc = True
      i = i + 1
    elif sys.argv[i].lower() == 'permission':
      group_attributes[0].update(Permission='Permission')
      titles.append('Permission')
      printperm = True
      i = i + 1
    elif sys.argv[i].lower() == 'nousermanagedgroups':
      nousermanagedgroups = True
      i = i + 1
    elif sys.argv[i].lower() == 'onlyusermanagedgroups':
      onlyusermanagedgroups = True
      i = i + 1
    elif sys.argv[i].lower() == 'members':
      group_attributes[0].update(Members='Members')
      titles.append('Members')
      members = True
      i = i + 1
    elif sys.argv[i].lower() == 'owners':
      group_attributes[0].update(Owners='Owners')
      titles.append('Owners')
      owners = True
      i = i + 1
    elif sys.argv[i].lower() == 'settings':
      group_attributes[0].update(who_Can_Join='who_Can_Join')
      titles.append('who_Can_Join')
      group_attributes[0].update(who_Can_View_Membership='who_Can_View_Membership')
      titles.append('who_Can_View_Membership')
      group_attributes[0].update(who_Can_View_Group='who_Can_View_Group')
      titles.append('who_Can_View_Group')
      group_attributes[0].update(who_Can_Invite='who_Can_Invite')
      titles.append('who_Can_Invite')
      group_attributes[0].update(allow_External_Members='allow_External_Members')
      titles.append('allow_External_Members')
      group_attributes[0].update(who_Can_Post_Message='who_Can_Post_Message')
      titles.append('who_Can_Post_Message')
      group_attributes[0].update(allow_Web_Posting='allow_Web_Posting')
      titles.append('allow_Web_Posting')
      group_attributes[0].update(max_Message_Bytes='max_Message_Bytes')
      titles.append('max_Message_Bytes')
      group_attributes[0].update(is_Archived='is_Archived')
      titles.append('is_Archived')
      group_attributes[0].update(archive_Only='archive_Only')
      titles.append('archive_Only')
      group_attributes[0].update(message_Moderation_Level='message_Moderation_Level')
      titles.append('message_Moderation_Level')
      group_attributes[0].update(primary_Language='primary_Language')
      titles.append('primary_Language')
      group_attributes[0].update(reply_To='reply_To')
      titles.append('reply_To')
      group_attributes[0].update(custom_Reply_To='custom_Reply_To')
      titles.append('custom_Reply_To')
      group_attributes[0].update(send_Message_Deny_Notification='send_Message_Deny_Notification')
      titles.append('send_Message_Deny_Notification')
      group_attributes[0].update(default_Message_Deny_Notification_Text='default_Message_Deny_Notification_Text')
      titles.append('default_Message_Deny_Notification_Text')
      group_attributes[0].update(show_In_Group_Directory='show_In_Group_Directory')
      titles.append('show_In_Group_Directory')
      group_attributes[0].update(allow_Google_Communication='allow_Google_Communication')
      titles.append('allow_Google_Communication')
      group_attributes[0].update(members_Can_Post_As_The_Group='members_Can_Post_As_The_Group')
      titles.append('members_Can_Post_As_The_Group')
      group_attributes[0].update(message_Display_Font='message_Display_Font')
      titles.append('message_Display_Font')
      group_attributes[0].update(include_In_Global_Address_List='include_In_Global_Address_List')
      titles.append('include_In_Global_Address_List')
      group_attributes[0].update(spam_Moderation_Level='spam_Moderation_Level')
      titles.append('spam_Moderation_Level')
      settings = True
      i = i + 1
    else:
      showUsage()
      exit(7)
  groupsObj = getGroupsObject()
  sys.stderr.write("Retrieving All Groups for domain %s (may take some time on large domain)..." % groupsObj.domain)
  if not onlyusermanagedgroups:
    try_count = 0
    wait_on_fail = .5
    while try_count < 10:
      try:
        all_groups = groupsObj.RetrieveAllGroups(nousermanagedgroups)
        break
      except gdata.apps.service.AppsForYourDomainException, e:
        terminating_error = checkErrorCode(e)
        if not terminating_error:
          try_count = try_count + 1
          if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
          time.sleep(wait_on_fail)
          wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
          continue
        else:
          sys.stderr.write('Error: %s\n' % terminating_error)
          sys.exit(e.error_code)
    if try_count == 10:
      sys.stderr.write('Giving up\n')
      sys.exit(e.error_code)
  else:
    try_count = 0
    wait_on_fail = .5
    while try_count < 10:
      try:
        admin_and_user_groups = groupsObj.RetrieveAllGroups(False)
        break
      except gdata.apps.service.AppsForYourDomainException, e:
        terminating_error = checkErrorCode(e)
        if not terminating_error:
          try_count = try_count + 1
          if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
          time.sleep(wait_on_fail)
          wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
          continue
        else:
          sys.stderr.write('Error: %s\n' % terminating_error)
          sys.exit(e.error_code)
    if try_count == 10:
      sys.stderr.write('Giving up\n')
      sys.exit(e.error_code)
    try_count = 0
    wait_on_fail = .5
    while try_count < 10:
      try:
        admin_groups = groupsObj.RetrieveAllGroups(True)
        break
      except gdata.apps.service.AppsForYourDomainException, e:
        terminating_error = checkErrorCode(e)
        if not terminating_error:
          try_count = try_count + 1
          if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
          time.sleep(wait_on_fail)
          wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
          continue
        else:
          sys.stderr.write('Error: %s\n' % terminating_error)
          sys.exit(e.error_code)
    if try_count == 10:
      sys.stderr.write('Giving up\n')
      sys.exit(e.error_code)
    all_groups = []
    for this_group in admin_and_user_groups:
      this_group_is_admin_created = False
      for that_group in admin_groups:
        if this_group['groupId'] == that_group['groupId']:
          this_group_is_admin_created = True
          break
      if not this_group_is_admin_created:
        all_groups.append(this_group)
  total_groups = len(all_groups)
  count = 0
  for group_vals in all_groups:
    count = count + 1
    group = {}
    group.update({'GroupID': group_vals['groupId']})
    if printname:
      name = group_vals['groupName']
      if name == None:
        name = ''
      group.update({'Name': name})
    if printdesc:
      description = group_vals['description']
      if description == None:
        description = ''
      group.update({'Description': description})
    if printperm:
      try:
        group.update({'Permission': group_vals['emailPermission']})
      except KeyError:
        group.update({'Permission': 'Unknown'})
    if members:
      all_members = ''
      sys.stderr.write("Retrieving Membership for group %s (%s of %s)...\r\n" % (group_vals['groupId'], count, total_groups))
      try_count = 0
      wait_on_fail = .5
      while try_count < 10:
        try:
          group_members = groupsObj.RetrieveAllMembers(group_vals['groupId'], suspended_users=True)
          break
        except gdata.apps.service.AppsForYourDomainException, e:
          terminating_error = checkErrorCode(e)
          if not terminating_error:
            try_count = try_count + 1
            if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
            time.sleep(wait_on_fail)
            wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
            continue
          else:
            sys.stderr.write('Error: %s\n' % terminating_error)
            sys.exit(e.error_code)
      if try_count == 10:
        sys.stderr.write('Giving up\n')
        sys.exit(e.error_code)
      for member in group_members:
        all_members += '%s ' % member['memberId']
      if all_members[-1:] == ' ':
        all_members = all_members[:-1]
      group.update({'Members': all_members})
    if owners:
      all_owners = ''
      sys.stderr.write("Retrieving Ownership for group %s (%s of %s)...\r\n" % (group_vals['groupId'], count, total_groups))
      try_count = 0
      wait_on_fail = .5
      while try_count < 10:
        try:
          group_owners = groupsObj.RetrieveAllOwners(group_vals['groupId'], suspended_users=True)
          break
        except gdata.apps.service.AppsForYourDomainException, e:
          terminating_error = checkErrorCode(e)
          if not terminating_error:
            try_count = try_count + 1
            if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
            time.sleep(wait_on_fail)
            wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
            continue
          else:
            sys.stderr.write('Error: %s\n' % terminating_error)
            sys.exit(e.error_code)
      if try_count == 10:
        sys.stderr.write('Giving up\n')
        sys.exit(e.error_code)
      for owner in group_owners:
        all_owners += '%s ' % owner['email']
      if all_owners[-1:] == ' ':
        all_owners = all_owners[:-1]
      group.update({'Owners': all_owners})
    if settings:
      sys.stderr.write("Retrieving Settings for group %s (%s of %s)...\r\n" % (group_vals['groupId'], count, total_groups))
      gs = getGroupSettingsObject()
      try_count = 0
      wait_on_fail = .5
      while try_count < 10:
        try:
          settings = gs.RetrieveGroupSettings(group_vals['groupId'])
          break
        except gdata.service.RequestError, e:
          if e[0]['status'] == 503 and e[0]['reason'] == 'Service Unavailable':
            try_count = try_count + 1
            group_name = group_vals['groupId'][:group_vals['groupId'].find('@')]
            group_domain = group_vals['groupId'][group_vals['groupId'].find('@')+1:]
            sys.stderr.write('Working around Google backend error. Opening group and sleeping %s sec(s)...\n' % str(wait_on_fail))
            try:
              url = 'https://groups.google.com/a/%s/group/%s' % (group_domain, group_name)
              b = urllib2.urlopen(url)
              b.read(100)
              b.close()
            except urllib2.HTTPError:
              pass
            time.sleep(wait_on_fail)
            wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
            continue
          print 'Error: %s - %s' % (e[0]['reason'], e[0]['body'])
          sys.exit(e[0]['status'])
        except gdata.apps.service.AppsForYourDomainException, e:
          terminating_error = checkErrorCode(e)
          if not terminating_error:
            try_count = try_count + 1
            if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
            time.sleep(wait_on_fail)
            wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
            continue
          else:
            sys.stderr.write('Error: %s\n' % terminating_error)
            sys.exit(e.error_code)
      if try_count == 10:
        sys.stderr.write('Giving up\n')
        sys.exit(e.error_code)
      for setting in settings:
        setting_key = re.sub(r'([A-Z])', r'_\1', setting.keys()[0])
        if setting_key == 'email' or setting_key == 'name' or setting_key == 'description':
          continue
        setting_value = setting.values()[0]
        if setting_value == None:
          setting_value = ''
        group.update({setting_key: setting_value})
    group_attributes.append(group)
  csv.register_dialect('nixstdout', lineterminator='\n')
  writer = csv.DictWriter(sys.stdout, fieldnames=titles, dialect='nixstdout', quoting=csv.QUOTE_MINIMAL, extrasaction='ignore')
  writer.writerows(group_attributes)

def doPrintOrgs():
  i = 3
  printname = printdesc = printparent = printinherit = False
  org_attributes = []
  org_attributes.append({'Path': 'Path'})
  titles = ['Path']
  while i < len(sys.argv):
    if sys.argv[i].lower() == 'name':
      printname = True
      org_attributes[0].update(Name='Name')
      titles.append('Name')
      i = i + 1
    elif sys.argv[i].lower() == 'description':
      printdesc = True
      org_attributes[0].update(Description='Description')
      titles.append('Description')
      i = i + 1
    elif sys.argv[i].lower() == 'parent':
      printparent = True
      org_attributes[0].update(Parent='Parent')
      titles.append('Parent')
      i = i + 1
    elif sys.argv[i].lower() == 'inherit':
      printinherit = True
      org_attributes[0].update(InheritanceBlocked='InheritanceBlocked')
      titles.append('InheritanceBlocked')
      i = i + 1
    else:
      showUsage()
      exit(8)
  org = getOrgObject()
  sys.stderr.write("Retrieving All Organizational Units for your account (may take some time on large domain)...")
  try_count = 0
  wait_on_fail = .5
  while try_count < 10:
    try:
      orgs = org.RetrieveAllOrganizationUnits()
      break
    except gdata.apps.service.AppsForYourDomainException, e:
      terminating_error = checkErrorCode(e)
      if not terminating_error:
        try_count = try_count + 1
        if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
        time.sleep(wait_on_fail)
        wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
        continue
      else:
        sys.stderr.write('Error: %s\n' % terminating_error)
        sys.exit(e.error_code)
  if try_count == 10:
    sys.stderr.write('Giving up\n')
    sys.exit(e.error_code)
  for org_vals in orgs:
    orgUnit = {}
    orgUnit.update({'Path': org_vals['orgUnitPath']})
    if printname:
      name = org_vals['name']
      if name == None:
        name = ''
      orgUnit.update({'Name': name})
    if printdesc:
      desc = org_vals['description']
      if desc == None:
        desc = ''
      orgUnit.update({'Description': desc})
    if printparent:
      parent = org_vals['parentOrgUnitPath']
      if parent == None:
        parent = ''
      orgUnit.update({'Parent': parent})
    if printinherit:
      orgUnit.update({'InheritanceBlocked': org_vals['blockInheritance']})
    org_attributes.append(orgUnit)
  csv.register_dialect('nixstdout', lineterminator='\n')
  writer = csv.DictWriter(sys.stdout, fieldnames=titles, dialect='nixstdout', quoting=csv.QUOTE_MINIMAL)
  writer.writerows(org_attributes)

def doPrintNicknames():
  multi = getMultiDomainObject()
  sys.stderr.write("Retrieving All Aliases for %s organization (may take some time on large domain)...\r\n\r\n" % multi.domain)
  alias_attributes = []
  alias_attributes.append({'Alias': 'Alias'})
  alias_attributes[0].update(User='User')
  titles = ['Alias', 'User']
  try_count = 0
  wait_on_fail = .5
  while try_count < 10:
    try:
      nicknames = multi.RetrieveAllAliases()
      break
    except gdata.apps.service.AppsForYourDomainException, e:
      terminating_error = checkErrorCode(e)
      if not terminating_error:
        try_count = try_count + 1
        if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
        time.sleep(wait_on_fail)
        wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
        continue
      else:
        sys.stderr.write('Error: %s\n' % terminating_error)
        sys.exit(e.error_code)
  if try_count == 10:
    sys.stderr.write('Giving up\n')
    sys.exit(e.error_code)
  for nickname in nicknames:
    alias_attributes.append({'Alias': nickname['aliasEmail'], 'User': nickname['userEmail']})
  csv.register_dialect('nixstdout', lineterminator='\n')
  writer = csv.DictWriter(sys.stdout, fieldnames=titles, dialect='nixstdout', quoting=csv.QUOTE_MINIMAL)
  writer.writerows(alias_attributes)

def doPrintResources():
  i = 3
  res_attributes = []
  res_attributes.append({'Name': 'Name'})
  titles = ['Name']
  printid = printdesc = printemail = False
  while i < len(sys.argv):
    if sys.argv[i].lower() == 'id':
      printid = True
      res_attributes[0].update(ID='ID')
      titles.append('ID')
      i = i + 1
    elif sys.argv[i].lower() == 'description':
      printdesc = True
      res_attributes[0].update(Description='Description')
      titles.append('Description')
      i = i + 1
    elif sys.argv[i].lower() == 'email':
      printemail = True
      res_attributes[0].update(Email='Email')
      titles.append('Email')
      i = i + 1
    else:
      showUsage()
      sys.exit(2)
  resObj = getResCalObject()
  sys.stderr.write("Retrieving All Resource Calendars for your account (may take some time on a large domain)")
  try_count = 0
  wait_on_fail = .5
  while try_count < 10:
    try:
      resources = resObj.RetrieveAllResourceCalendars()
      break
    except gdata.apps.service.AppsForYourDomainException, e:
      terminating_error = checkErrorCode(e)
      if not terminating_error:
        try_count = try_count + 1
        if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
        time.sleep(wait_on_fail)
        wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
        continue
      else:
        sys.stderr.write('Error: %s\n' % terminating_error)
        sys.exit(e.error_code)
  if try_count == 10:
    sys.stderr.write('Giving up\n')
    sys.exit(e.error_code)
  for resource in resources:
    resUnit = {}
    resUnit.update({'Name': resource['resourceCommonName']})
    if printid:
      resUnit.update({'ID': resource['resourceId']})
    if printdesc:
      try:
        desc = resource['resourceDescription']
      except KeyError:
        desc = ''
      resUnit.update({'Description': desc})
    if printemail:
      resUnit.update({'Email': resource['resourceEmail']})
    res_attributes.append(resUnit)
  csv.register_dialect('nixstdout', lineterminator='\n')
  writer = csv.DictWriter(sys.stdout, fieldnames=titles, dialect='nixstdout', quoting=csv.QUOTE_MINIMAL)
  writer.writerows(res_attributes)

def hasAgreed2TOS(user_email):
  multi = getMultiDomainObject()
  if user_email.find('@') == -1:
    user_email = '%s@%s' % (user_name, multi.domain)
  try_count = 0
  wait_on_fail = .5
  hard_fail = False
  while try_count < 10:
    try:
      userInfo = multi.RetrieveUser(user_email)
      break
    except gdata.apps.service.AppsForYourDomainException, e:
      terminating_error = checkErrorCode(e)
      if not terminating_error:
        try_count = try_count + 1
        if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
        time.sleep(wait_on_fail)
        wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
        continue
      else:
        sys.stderr.write('Error: %s\n' % terminating_error)
        hard_fail = True
        break
  if try_count == 10 or hard_fail:
    sys.stderr.write('Giving up\n')
    return True
  if userInfo['agreedToTerms'] == 'true':
    return True
  return False

def doCreateMonitor():
  source_user = sys.argv[4].lower()
  destination_user = sys.argv[5].lower()
  #end_date defaults to 30 days in the future...
  end_date = (datetime.datetime.now() + datetime.timedelta(days=30)).strftime("%Y-%m-%d %H:%M")
  begin_date = None
  incoming_headers_only = outgoing_headers_only = drafts_headers_only = chats_headers_only = False
  drafts = chats = True
  i = 6
  while i < len(sys.argv):
    if sys.argv[i].lower() == 'end':
      end_date = sys.argv[i+1]
      i = i + 2
    elif sys.argv[i].lower() == 'begin':
      begin_date = sys.argv[i+1]
      i = i + 2
    elif sys.argv[i].lower() == 'incoming_headers':
      incoming_headers_only = True
      i = i + 1
    elif sys.argv[i].lower() == 'outgoing_headers':
      outgoing_headers_only = True
      i = i + 1
    elif sys.argv[i].lower() == 'nochats':
      chats = False
      i = i + 1
    elif sys.argv[i].lower() == 'nodrafts':
      drafts = False
      i = i + 1
    elif sys.argv[i].lower() == 'chat_headers':
      chats_headers_only = True
      i = i + 1
    elif sys.argv[i].lower() == 'draft_headers':
      drafts_headers_only = True
      i = i + 1
    else:
      showUsage()
      sys.exit(2)
  audit = getAuditObject()
  if source_user.find('@') > 0:
    audit.domain = source_user[source_user.find('@')+1:]
    source_user = source_user[:source_user.find('@')]
  try_count = 0
  wait_on_fail = .5
  while try_count < 10:
    try:
      results = audit.createEmailMonitor(source_user=source_user, destination_user=destination_user, end_date=end_date, begin_date=begin_date,
                           incoming_headers_only=incoming_headers_only, outgoing_headers_only=outgoing_headers_only,
                           drafts=drafts, drafts_headers_only=drafts_headers_only, chats=chats, chats_headers_only=chats_headers_only)
      break
    except gdata.apps.service.AppsForYourDomainException, e:
      terminating_error = checkErrorCode(e)
      if not terminating_error:
        try_count = try_count + 1
        if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
        time.sleep(wait_on_fail)
        wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
        continue
      else:
        sys.stderr.write('Error: %s\n' % terminating_error)
        sys.exit(e.error_code)
  if try_count == 10:
    sys.stderr.write('Giving up\n')
    sys.exit(e.error_code)

def doShowMonitors():
  user = sys.argv[4].lower()
  audit = getAuditObject()
  if user.find('@') > 0:
    audit.domain = user[user.find('@')+1:]
    user = user[:user.find('@')]
  try_count = 0
  wait_on_fail = .5
  while try_count < 10:
    try:
      results = audit.getEmailMonitors(user)
      break
    except gdata.apps.service.AppsForYourDomainException, e:
      terminating_error = checkErrorCode(e)
      if not terminating_error:
        try_count = try_count + 1
        if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
        time.sleep(wait_on_fail)
        wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
        continue
      else:
        sys.stderr.write('Error: %s\n' % terminating_error)
        sys.exit(e.error_code)
  if try_count == 10:
    sys.stderr.write('Giving up\n')
    sys.exit(e.error_code)
  print sys.argv[4].lower()+' has the following monitors:'
  print ''
  for monitor in results:
    print ' Destination: '+monitor['destUserName']
    try:
      print '  Begin: '+monitor['beginDate']
    except KeyError:
      print '  Begin: immediately'
    print '  End: '+monitor['endDate']
    print '  Monitor Incoming: '+monitor['outgoingEmailMonitorLevel']
    print '  Monitor Outgoing: '+monitor['incomingEmailMonitorLevel']
    print '  Monitor Chats: '+monitor['chatMonitorLevel']
    print '  Monitor Drafts: '+monitor['draftMonitorLevel']
    print ''

def doDeleteMonitor():
  source_user = sys.argv[4].lower()
  destination_user = sys.argv[5].lower()
  audit = getAuditObject()
  if source_user.find('@') > 0:
    audit.domain = source_user[source_user.find('@')+1:]
    source_user = source_user[:source_user.find('@')]
  try_count = 0
  wait_on_fail = .5
  while try_count < 10:
    try:
      results = audit.deleteEmailMonitor(source_user=source_user, destination_user=destination_user)
      break
    except gdata.apps.service.AppsForYourDomainException, e:
      terminating_error = checkErrorCode(e)
      if not terminating_error:
        try_count = try_count + 1
        if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
        time.sleep(wait_on_fail)
        wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
        continue
      else:
        sys.stderr.write('Error: %s\n' % terminating_error)
        sys.exit(e.error_code)
  if try_count == 10:
    sys.stderr.write('Giving up\n')
    sys.exit(e.error_code)

def doRequestActivity():
  user = sys.argv[4].lower()
  audit = getAuditObject()
  if user.find('@') > 0:
    audit.domain = user[user.find('@')+1:]
    user = user[:user.find('@')]
  try_count = 0
  wait_on_fail = .5
  while try_count < 10:
    try:
      results = audit.createAccountInformationRequest(user)
      break
    except gdata.apps.service.AppsForYourDomainException, e:
      terminating_error = checkErrorCode(e)
      if not terminating_error:
        try_count = try_count + 1
        if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
        time.sleep(wait_on_fail)
        wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
        continue
      else:
        sys.stderr.write('Error: %s\n' % terminating_error)
        sys.exit(e.error_code)
  if try_count == 10:
    sys.stderr.write('Giving up\n')
    sys.exit(e.error_code)
  print 'Request successfully submitted:'
  print ' Request ID: '+results['requestId']
  print ' User: '+results['userEmailAddress']
  print ' Status: '+results['status']
  print ' Request Date: '+results['requestDate']
  print ' Requested By: '+results['adminEmailAddress']

def doStatusActivityRequests():
  audit = getAuditObject()
  try:
    user = sys.argv[4].lower()
    if user.find('@') > 0:
      audit.domain = user[user.find('@')+1:]
      user = user[:user.find('@')]
    request_id = sys.argv[5].lower()
    try_count = 0
    wait_on_fail = .5
    while try_count < 10:
      try:
        results = audit.getAccountInformationRequestStatus(user, request_id)
        break
      except gdata.apps.service.AppsForYourDomainException, e:
        terminating_error = checkErrorCode(e)
        if not terminating_error:
          try_count = try_count + 1
          if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
          time.sleep(wait_on_fail)
          wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
          continue
        else:
          sys.stderr.write('Error: %s\n' % terminating_error)
          sys.exit(e.error_code)
    if try_count == 10:
      sys.stderr.write('Giving up\n')
      sys.exit(e.error_code)
    print ''
    print '  Request ID: '+results['requestId']
    print '  User: '+results['userEmailAddress']
    print '  Status: '+results['status']
    print '  Request Date: '+results['requestDate']
    print '  Requested By: '+results['adminEmailAddress']
    try:
      print '  Number Of Files: '+results['numberOfFiles']
      for i in range(int(results['numberOfFiles'])):
        print '  Url%s: %s' % (i, results['fileUrl%s' % i])
    except KeyError:
      pass
    print ''
  except IndexError:
    try_count = 0
    wait_on_fail = .5
    while try_count < 10:
      try:
        results = audit.getAllAccountInformationRequestsStatus()
        break
      except gdata.apps.service.AppsForYourDomainException, e:
        terminating_error = checkErrorCode(e)
        if not terminating_error:
          try_count = try_count + 1
          if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
          time.sleep(wait_on_fail)
          wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
          continue
        else:
          sys.stderr.write('Error: %s\n' % terminating_error)
          sys.exit(e.error_code)
    if try_count == 10:
      sys.stderr.write('Giving up\n')
      sys.exit(e.error_code)
    print 'Current Activity Requests:'
    print ''
    for request in results:
      print ' Request ID: '+request['requestId']
      print '  User: '+request['userEmailAddress']
      print '  Status: '+request['status']
      print '  Request Date: '+request['requestDate']
      print '  Requested By: '+request['adminEmailAddress']
      print ''

def doDownloadActivityRequest():
  user = sys.argv[4].lower()
  request_id = sys.argv[5].lower()
  audit = getAuditObject()
  if user.find('@') > 0:
    audit.domain = user[user.find('@')+1:]
    user = user[:user.find('@')]
  try_count = 0
  wait_on_fail = .5
  while try_count < 10:
    try:
      results = audit.getAccountInformationRequestStatus(user, request_id)
      break
    except gdata.apps.service.AppsForYourDomainException, e:
      terminating_error = checkErrorCode(e)
      if not terminating_error:
        try_count = try_count + 1
        if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
        time.sleep(wait_on_fail)
        wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
        continue
      else:
        sys.stderr.write('Error: %s\n' % terminating_error)
        sys.exit(e.error_code)
  if try_count == 10:
    sys.stderr.write('Giving up\n')
    sys.exit(e.error_code)
  if results['status'] != 'COMPLETED':
    print 'Request needs to be completed before downloading, current status is: '+results['status']
    sys.exit(4)
  try:
    if int(results['numberOfFiles']) < 1:
      print 'ERROR: Request completed but no results were returned, try requesting again'
      sys.exit(4)
  except KeyError:
    print 'ERROR: Request completed but no files were returned, try requesting again'
    sys.exit(4)
  for i in range(0, int(results['numberOfFiles'])):
    url = results['fileUrl'+str(i)]
    filename = 'activity-'+user+'-'+request_id+'-'+str(i)+'.txt.gpg'
    print 'Downloading '+filename+' ('+str(i+1)+' of '+results['numberOfFiles']+')'
    geturl(url, filename)

def doRequestExport():
  begin_date = end_date = search_query = None
  headers_only = include_deleted = False
  user = sys.argv[4].lower()
  i = 5
  while i < len(sys.argv):
    if sys.argv[i].lower() == 'begin':
      begin_date = sys.argv[i+1]
      i = i + 2
    elif sys.argv[i].lower() == 'end':
      end_date = sys.argv[i+1]
      i = i + 2
    elif sys.argv[i].lower() == 'search':
      search_query = sys.argv[i+1]
      i = i + 2
    elif sys.argv[i].lower() == 'headersonly':
      headers_only = True
      i = i + 1
    elif sys.argv[i].lower() == 'includedeleted':
      include_deleted = True
      i = i + 1
    else:
      showUsage()
      sys.exit(2)
  audit = getAuditObject()
  if user.find('@') > 0:
    audit.domain = user[user.find('@')+1:]
    user = user[:user.find('@')]
  try_count = 0
  wait_on_fail = .5
  while try_count < 10:
    try:
      results = audit.createMailboxExportRequest(user=user, begin_date=begin_date, end_date=end_date, include_deleted=include_deleted,
                                             search_query=search_query, headers_only=headers_only)
      break
    except gdata.apps.service.AppsForYourDomainException, e:
      terminating_error = checkErrorCode(e)
      if not terminating_error:
        try_count = try_count + 1
        if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
        time.sleep(wait_on_fail)
        wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
        continue
      else:
        sys.stderr.write('Error: %s\n' % terminating_error)
        sys.exit(e.error_code)
  if try_count == 10:
    sys.stderr.write('Giving up\n')
    sys.exit(e.error_code)
  print 'Export request successfully submitted:'
  print ' Request ID: '+results['requestId']
  print ' User: '+results['userEmailAddress']
  print ' Status: '+results['status']
  print ' Request Date: '+results['requestDate']
  print ' Requested By: '+results['adminEmailAddress']
  print ' Include Deleted: '+results['includeDeleted']
  print ' Requested Parts: '+results['packageContent']
  try:
    print ' Begin: '+results['beginDate']
  except KeyError:
    print ' Begin: account creation date'
  try:
    print ' End: '+results['endDate']
  except KeyError:
    print ' End: export request date'

def doDeleteExport():
  audit = getAuditObject()
  user = sys.argv[4].lower()
  if user.find('@') > 0:
    audit.domain = user[user.find('@')+1:]
    user = user[:user.find('@')]
  request_id = sys.argv[5].lower()
  try_count = 0
  wait_on_fail = .5
  while try_count < 10:
    try:
      results = audit.deleteMailboxExportRequest(user=user, request_id=request_id)
      break
    except gdata.apps.service.AppsForYourDomainException, e:
      terminating_error = checkErrorCode(e)
      if not terminating_error:
        try_count = try_count + 1
        if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
        time.sleep(wait_on_fail)
        wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
        continue
      else:
        sys.stderr.write('Error: %s\n' % terminating_error)
        sys.exit(e.error_code)
  if try_count == 10:
    sys.stderr.write('Giving up\n')
    sys.exit(e.error_code)

def doDeleteActivityRequest():
  audit = getAuditObject()
  user = sys.argv[4].lower()
  if user.find('@') > 0:
    audit.domain = user[user.find('@')+1:]
    user = user[:user.find('@')]
  request_id = sys.argv[5].lower()
  try_count = 0
  wait_on_fail = .5
  while try_count < 10:
    try:
      results = audit.deleteAccountInformationRequest(user=user, request_id=request_id)
      break
    except gdata.apps.service.AppsForYourDomainException, e:
      terminating_error = checkErrorCode(e)
      if not terminating_error:
        try_count = try_count + 1
        if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
        time.sleep(wait_on_fail)
        wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
        continue
      else:
        sys.stderr.write('Error: %s\n' % terminating_error)
        sys.exit(e.error_code)
  if try_count == 10:
    sys.stderr.write('Giving up\n')
    sys.exit(e.error_code)

def doStatusExportRequests():
  audit = getAuditObject()
  try:
    user = sys.argv[4].lower()
    if user.find('@') > 0:
      audit.domain = user[user.find('@')+1:]
      user = user[:user.find('@')]
    request_id = sys.argv[5].lower()
    try_count = 0
    wait_on_fail = .5
    while try_count < 10:
      try:
        results = audit.getMailboxExportRequestStatus(user, request_id)
        break
      except gdata.apps.service.AppsForYourDomainException, e:
        terminating_error = checkErrorCode(e)
        if not terminating_error:
          try_count = try_count + 1
          if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
          time.sleep(wait_on_fail)
          wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
          continue
        else:
          sys.stderr.write('Error: %s\n' % terminating_error)
          sys.exit(e.error_code)
    if try_count == 10:
      sys.stderr.write('Giving up\n')
      sys.exit(e.error_code)
    print ''
    print '  Request ID: '+results['requestId']
    print '  User: '+results['userEmailAddress']
    print '  Status: '+results['status']
    print '  Request Date: '+results['requestDate']
    print '  Requested By: '+results['adminEmailAddress']
    print '  Requested Parts: '+results['packageContent']
    try:
      print '  Request Filter: '+results['searchQuery']
    except KeyError:
      print '  Request Filter: None'
    print '  Include Deleted: '+results['includeDeleted']
    try:
      print '  Number Of Files: '+results['numberOfFiles']
      for i in range(int(results['numberOfFiles'])):
        print '  Url%s: %s' % (i, results['fileUrl%s' % i])
    except KeyError:
      pass
  except IndexError:
    try_count = 0
    wait_on_fail = .5
    while try_count < 10:
      try:
        results = audit.getAllMailboxExportRequestsStatus()
        break
      except gdata.apps.service.AppsForYourDomainException, e:
        terminating_error = checkErrorCode(e)
        if not terminating_error:
          try_count = try_count + 1
          if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
          time.sleep(wait_on_fail)
          wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
          continue
        else:
          sys.stderr.write('Error: %s\n' % terminating_error)
          sys.exit(e.error_code)
    if try_count == 10:
      sys.stderr.write('Giving up\n')
      sys.exit(e.error_code)
    print 'Current Export Requests:'
    print ''
    for request in results:
      print ' Request ID: '+request['requestId']
      print '  User: '+request['userEmailAddress']
      print '  Status: '+request['status']
      print '  Request Date: '+request['requestDate']
      print '  Requested By: '+request['adminEmailAddress']
      print '  Requested Parts: '+request['packageContent']
      try:
        print '  Request Filter: '+request['searchQuery']
      except KeyError:
        print '  Request Filter: None'
      print '  Include Deleted: '+request['includeDeleted']
      try:
        print '  Number Of Files: '+request['numberOfFiles']
      except KeyError:
        pass
      print ''
    
def doDownloadExportRequest():
  user = sys.argv[4].lower()
  request_id = sys.argv[5].lower()
  audit = getAuditObject()
  if user.find('@') > 0:
    audit.domain = user[user.find('@')+1:]
    user = user[:user.find('@')]
  try_count = 0
  wait_on_fail = .5
  while try_count < 10:
    try:
      results = audit.getMailboxExportRequestStatus(user, request_id)
      break
    except gdata.apps.service.AppsForYourDomainException, e:
      terminating_error = checkErrorCode(e)
      if not terminating_error:
        try_count = try_count + 1
        if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
        time.sleep(wait_on_fail)
        wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
        continue
      else:
        sys.stderr.write('Error: %s\n' % terminating_error)
        sys.exit(e.error_code)
  if try_count == 10:
    sys.stderr.write('Giving up\n')
    sys.exit(e.error_code)
  if results['status'] != 'COMPLETED':
    print 'Request needs to be completed before downloading, current status is: '+results['status']
    sys.exit(4)
  try:
    if int(results['numberOfFiles']) < 1:
      print 'ERROR: Request completed but no results were returned, try requesting again'
      sys.exit(4)
  except KeyError:
    print 'ERROR: Request completed but no files were returned, try requesting again'
    sys.exit(4)
  for i in range(0, int(results['numberOfFiles'])):
    url = results['fileUrl'+str(i)]
    filename = 'export-'+user+'-'+request_id+'-'+str(i)+'.mbox.gpg'
    #don't download existing files. This does not check validity of existing local
    #file so partial/corrupt downloads will need to be deleted manually.
    if os.path.isfile(filename):
      continue
    print 'Downloading '+filename+' ('+str(i+1)+' of '+results['numberOfFiles']+')'
    geturl(url, filename)

def doUploadAuditKey():
  auditkey = sys.stdin.read()
  audit = getAuditObject()
  try_count = 0
  wait_on_fail = .5
  while try_count < 10:
    try:
      results = audit.updatePGPKey(auditkey)
      break
    except gdata.apps.service.AppsForYourDomainException, e:
      terminating_error = checkErrorCode(e)
      if not terminating_error:
        try_count = try_count + 1
        if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
        time.sleep(wait_on_fail)
        wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
        continue
      else:
        sys.stderr.write('Error: %s\n' % terminating_error)
        sys.exit(e.error_code)
  if try_count == 10:
    sys.stderr.write('Giving up\n')
    sys.exit(e.error_code)

def getUsersToModify():
  entity = sys.argv[1].lower()
  if entity == 'user':
    users = [sys.argv[2].lower(),]
  elif entity == 'group':
    groupsObj = getGroupsObject()
    group = sys.argv[2].lower()
    sys.stderr.write("Getting all members of %s (may take some time for large groups)..." % group)
    try_count = 0
    wait_on_fail = .5
    while try_count < 10:
      try:
        members = groupsObj.RetrieveAllMembers(group)
        break
      except gdata.apps.service.AppsForYourDomainException, e:
        terminating_error = checkErrorCode(e)
        if not terminating_error:
          try_count = try_count + 1
          if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
          time.sleep(wait_on_fail)
          wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
          continue
        else:
          sys.stderr.write('Error: %s\n' % terminating_error)
          sys.exit(e.error_code)
    if try_count == 10:
      sys.stderr.write('Giving up\n')
      sys.exit(e.error_code)
    print "done.\r\n"
    users = []
    for member in members:
      users.append(member['memberId'][0:member['memberId'].find('@')])
  elif entity == 'ou':
    orgObj = getOrgObject()
    ou = sys.argv[2]
    sys.stderr.write("Getting all users of %s Organizational Unit (May take some time for large OUs)..." % ou)
    try_count = 0
    wait_on_fail = .5
    while try_count < 10:
      try:
        members = orgObj.RetrieveAllOrganizationUnitUsers(ou)
        break
      except gdata.apps.service.AppsForYourDomainException, e:
        terminating_error = checkErrorCode(e)
        if not terminating_error:
          try_count = try_count + 1
          if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
          time.sleep(wait_on_fail)
          wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
          continue
        else:
          sys.stderr.write('Error: %s\n' % terminating_error)
          sys.exit(e.error_code)
    if try_count == 10:
      sys.stderr.write('Giving up\n')
      sys.exit(e.error_code)
    print "done.\r\n"
    users = []
    for member in members:
      users.append(member['orgUserEmail'])
  elif entity == 'all':
    orgObj = getOrgObject()
    users = []
    sys.stderr.write("Getting all users in the Google Apps %s organization (may take some time on a large domain)..." % orgObj.domain)
    try_count = 0
    wait_on_fail = .5
    while try_count < 10:
      try:
        members = orgObj.RetrieveAllOrganizationUsers()
        break
      except gdata.apps.service.AppsForYourDomainException, e:
        terminating_error = checkErrorCode(e)
        if not terminating_error:
          try_count = try_count + 1
          if try_count > 5: sys.stderr.write('Temporary error %s. Retry %s in %s seconds\n' % (str(e.error_code), try_count, str(wait_on_fail)))
          time.sleep(wait_on_fail)
          wait_on_fail = wait_on_fail * 2 if wait_on_fail < 32 else 60
          continue
        else:
          sys.stderr.write('Error: %s\n' % terminating_error)
          sys.exit(e.error_code)
    if try_count == 10:
      sys.stderr.write('Giving up\n')
      sys.exit(e.error_code)
    for member in members:
      if member['orgUserEmail'][:2] == '.@' or member['orgUserEmail'][:11] == 'gcc_websvc@' or member['orgUserEmail'][:27] == 'secure-data-connector-user@' or member['orgUserEmail'][-16:] == '@gtempaccount.com':  # not real users, skip em
        continue
      users.append(member['orgUserEmail'])
    sys.stderr.write("done.\r\n")
  else:
    showUsage()
    sys.exit(2)
  return users

def OAuthInfo():
  selected_file = 'oauth.txt'
  try:
    selected_file = os.environ['OAUTHFILE']
  except KeyError:
    pass
  print "\nOAuth File: %s%s" % (getGamPath(), selected_file)
  if os.path.isfile(getGamPath()+selected_file):
    oauthfile = open(getGamPath()+selected_file, 'rb')
    domain = oauthfile.readline()[0:-1]
    try:
      token = pickle.load(oauthfile)
      oauthfile.close()
    except ImportError: # Deals with tokens created by windows on old GAM versions. Rewrites them with binary mode set
      oauthfile = open(getGamPath()+oauth_filename, 'r')
      domain = oauthfile.readline()[0:-1]
      token = pickle.load(oauthfile)
      oauthfile.close()
      f = open(getGamPath()+oauth_filename, 'wb')
      f.write('%s\n' % (domain,))
      pickle.dump(token, f)
      f.close()
    print 'Google Apps Domain: %s' % domain
    print "Client ID: %s\nSecret: %s" % (token.oauth_input_params._consumer.key, token.oauth_input_params._consumer.secret)
    print 'Scopes:'
    email_scope_present = False
    for scope in token.scopes:
      print '  %s' % scope
      if scope == 'https://www.googleapis.com/auth/userinfo.email':
        email_scope_present = True
    apps = getAppsObject()
    try:
      is_valid = apps.Post(' ', 'https://www.google.com/accounts/AuthSubTokenInfo', converter=str)
    except gdata.service.RequestError, e:
      print 'Error: %s' % e[0]['reason']
      exit(0)
    if email_scope_present:
      admin_email = apps.Get('https://www.googleapis.com/userinfo/email', converter=str)
      admin_email = admin_email[6:admin_email.find('&')]
      print 'Google Apps Admin: %s' % admin_email
    else:
      print 'Google Apps Admin: Not authorized to check (recreate GAM OAuth token to correct)'
  else:
    print 'Error: That OAuth file doesn\'t exist!'

def doDeleteOAuth():
  sys.stderr.write('This OAuth token will self-destruct in 3...')
  time.sleep(1)
  sys.stderr.write('2...')
  time.sleep(1)
  sys.stderr.write('1...')
  time.sleep(1)
  sys.stderr.write('boom!\n')
  selected_file = 'oauth.txt'
  try:
    selected_file = os.environ['OAUTHFILE']
  except KeyError:
    pass
  if os.path.isfile(getGamPath()+selected_file):
    multi = getMultiDomainObject()
    os.remove(getGamPath()+selected_file)
    try:
      revoke_result = multi.Get('https://www.google.com/accounts/AuthSubRevokeToken', converter=str)
    except gdata.service.RequestError, e:
      print 'Error: %s' % e[0]['reason']
      sys.exit(e[0]['status'])
    print revoke_result
  else:
    print 'Error: The OAuth token %s does not exist' % (getGamPath()+selected_file)
    sys.exit(1)

def doRequestOAuth():
  if not os.path.isfile(getGamPath()+'nodito.txt'):
    print "\n\nGAM is made possible and maintained by the work of Dito. Who is Dito?\n\nDito is solely focused on moving organizations to Google's cloud.  After hundreds of successful deployments over the last 5 years, we have gained notoriety for our complete understanding of the platform, our change management & training ability, and our rock-star deployment engineers.  We are known worldwide as the Google Apps Experts.\n"
    visit_dito = raw_input("Want to learn more about Dito? Hit Y to visit our website (you can switch back to this window when you're done). Hit Enter to continue without visiting Dito: ")
    if visit_dito.lower() == 'y':
      webbrowser.open('http://www.ditoweb.com?s=gam')
  domain = raw_input("\nEnter your Primary Google Apps Domain (e.g. example.com): ")
  if os.path.isfile(getGamPath()+'key-and-secret.txt'):
    secret_file = open(getGamPath()+'key-and-secret.txt', 'rb')
    client_key = secret_file.readline()
    if client_key[-1:] == "\n" or client_key[-1:] == "\r":
      client_key = client_key[:-1]
    client_secret = secret_file.readline()
    if client_secret[-1:] == "\n" or client_secret[-1:] == "\r":
      client_secret = client_secret[:-1]
    secret_file.close()
    print "\nUsing Client Key and Secret from %s:\n\tClient Key: \"%s\"\n\tClient Secret: \"%s\"\n\nPress Enter to Continue...\n" % (getGamPath()+'key-and-secret.txt', client_key, client_secret)
    raw_input()
  else:
    print "\nIf you plan to use Group Settings commands, you\'ll need an Client ID and secret from the Google API console, see http://code.google.com/p/google-apps-manager/wiki/GettingAnOAuthConsoleKey for details. If you don\'t plan to use Group Settings commands you can just press enter here."
    client_key = raw_input("\nEnter your Client ID (e.g. XXXXXX.apps.googleusercontent.com or leave blank): ")
    if client_key == '':
      client_key = 'anonymous'
      client_secret = 'anonymous'
    else:
      client_secret = raw_input("\nEnter your Client Secret: ")
      save_secret = raw_input('Do you wish to save the Client Key and Secret to %s for future use? (y/N): ' % (getGamPath()+'key-and-secret.txt'))
      if save_secret.lower() == 'y':
        secret_file = open(getGamPath()+'key-and-secret.txt', 'wb')
        secret_file.write('%s\n%s' % (client_key, client_secret))
        secret_file.close()
  fetch_params = {'xoauth_displayname':'Google Apps Manager'}
  selected_scopes = ['*', '*', '*', '*', '*', '*', '*', '*', '*', '*', '*', '*', '*']
  menu = '''Select the authorized scopes for this OAuth token and set the token name:

[%s] 0)  Group Provisioning
[%s] 1)  Email Alias Provisioning
[%s] 2)  Organizational Unit Provisioning
[%s] 3)  User Provisioning
[%s] 4)  User Email Settings
[%s] 5)  Calendar Resources
[%s] 6)  Audit Monitors, Activity and Mailbox Exports
[%s] 7)  Admin Settings
[%s] 8)  Admin Auditing
[%s] 9)  Group Settings API
[%s] 10) Profiles API (Hide / Unhide from contact sharing)
[%s] 11) Calendar Data API
[%s] 12) Reporting API

     13) Select all scopes
     14) Unselect all scopes
     15) Set OAuth token name (currently: %s)
     16) Continue
'''
  os.system(['clear','cls'][os.name == 'nt'])
  while True:
    selection = raw_input(menu % (selected_scopes[0], selected_scopes[1], selected_scopes[2], selected_scopes[3], selected_scopes[4], selected_scopes[5], selected_scopes[6], selected_scopes[7], selected_scopes[8], selected_scopes[9], selected_scopes[10], selected_scopes[11], selected_scopes[12], fetch_params['xoauth_displayname']))
    try:
      if int(selection) > -1 and int(selection) < 13:
        if selected_scopes[int(selection)] == ' ':
          selected_scopes[int(selection)] = '*'
        else:
          selected_scopes[int(selection)] = ' '
      elif selection == '13':
        for i in range(0, len(selected_scopes)):
          selected_scopes[i] = '*'
      elif selection == '14':
        for i in range(0, len(selected_scopes)):
           selected_scopes[i] = ' '
      elif selection == '15':
        fetch_params['xoauth_displayname'] = raw_input('Enter the name for your OAuth token: ')
      elif selection == '16':
        at_least_one = False
        for i in range(0, len(selected_scopes)):
          if selected_scopes[i] == '*':
            at_least_one = True
        if at_least_one:
          break
        else:
          os.system(['clear','cls'][os.name == 'nt'])
          print "You must select at least one scope!\n"
          continue
      else:
        os.system(['clear','cls'][os.name == 'nt'])
        print 'Not a valid selection.'
        continue
      os.system(['clear','cls'][os.name == 'nt'])
    except ValueError:
      os.system(['clear','cls'][os.name == 'nt'])
      print 'Not a valid selection.'
      continue

  possible_scopes = ['https://apps-apis.google.com/a/feeds/groups/',                      # Groups Provisioning API
                     'https://apps-apis.google.com/a/feeds/alias/',                       # Nickname Provisioning API
                     'https://apps-apis.google.com/a/feeds/policies/',                    # Organization Provisioning API
                     'https://apps-apis.google.com/a/feeds/user/',                        # Users Provisioning API
                     'https://apps-apis.google.com/a/feeds/emailsettings/2.0/',           # Email Settings API
                     'https://apps-apis.google.com/a/feeds/calendar/resource/',           # Calendar Resource API
                     'https://apps-apis.google.com/a/feeds/compliance/audit/',            # Audit API
                     'https://apps-apis.google.com/a/feeds/domain/',                      # Admin Settings API
                     'https://www.googleapis.com/auth/apps/reporting/audit.readonly',     # Admin Audit API
                     'https://www.googleapis.com/auth/apps.groups.settings',              # Group Settings API
                     'https://www.google.com/m8/feeds',                                   # Contacts / Profiles API
                     'https://www.google.com/calendar/feeds/',                            # Calendar Data API
                     'https://www.google.com/hosted/services/v1.0/reports/ReportingData'] # Reporting API
  scopes = ['https://www.googleapis.com/auth/userinfo.email',] # Email Display Scope, always included
  for i in range(0, len(selected_scopes)):
    if selected_scopes[i] == '*':
      scopes.append(possible_scopes[i])
      if possible_scopes[i] == 'https://www.google.com/calendar/feeds/':
        scopes.append('https://www.googleapis.com/auth/calendar') # Get the new Calendar API scope also
  apps = gdata.apps.service.AppsService(domain=domain)
  apps = commonAppsObjInit(apps)
  apps.SetOAuthInputParameters(gdata.auth.OAuthSignatureMethod.HMAC_SHA1, consumer_key=client_key, consumer_secret=client_secret)
  try:
    request_token = apps.FetchOAuthRequestToken(scopes=scopes, extra_parameters=fetch_params)
  except gdata.service.FetchingOAuthRequestTokenFailed, e:
    if str(e).find('Timestamp') != -1:
      print "In order to use OAuth, your system time needs to be correct.\nPlease fix your time and try again."
      sys.exit(5)
    else:
      print "Error: %s" % e
      sys.exit(6)
  url_params = {'hd': domain}
  url = apps.GenerateOAuthAuthorizationURL(request_token=request_token, extra_params=url_params)
  raw_input("\nNow GAM will open a web page in order for you to grant %s access. Make sure you are logged in as an Administrator of your Google Apps domain before granting access. Press the Enter key to open your browser." % fetch_params['xoauth_displayname'])
  try:
    webbrowser.open(str(url))
  except Exception, e:
    pass
  raw_input("\n\nYou should now see a web page asking you to grant %s\n"
            'access. If the page didn\'t open, you can manually\n'
            'go to\n\n%s\n\nto grant access.\n'
            '\n'
            'Once you\'ve granted access, press the Enter key.' % (fetch_params['xoauth_displayname'], url))
  try:
    final_token = apps.UpgradeToOAuthAccessToken(request_token)
  except gdata.service.TokenUpgradeFailed:
    print 'Failed to upgrade the token. Did you grant GAM access in your browser?'
    exit(4)
  oauth_filename = 'oauth.txt'
  try:
    oauth_filename = os.environ['OAUTHFILE']
  except KeyError:
    pass
  f = open(getGamPath()+oauth_filename, 'wb')
  f.write('%s\n' % (domain,))
  pickle.dump(final_token, f)
  f.close()



def main():
	try:
	  # perform update check
	  doGAMCheckForUpdates()
	  if sys.argv[1].lower() == 'version':
	    doGAMVersion()
	    exit(0)
	  if sys.argv[1].lower() == 'create':
	    if sys.argv[2].lower() == 'user':
	      doCreateUser()
	    elif sys.argv[2].lower() == 'group':
	      doCreateGroup()
	    elif sys.argv[2].lower() == 'nickname' or sys.argv[2].lower() == 'alias':
	      doCreateNickName()
	    elif sys.argv[2].lower() == 'org':
	      doCreateOrg()
	    elif sys.argv[2].lower() == 'resource':
	      doCreateResource()
	    sys.exit(0)
	  elif sys.argv[1].lower() == 'update':
	    if sys.argv[2].lower() == 'user':
	      doUpdateUser()
	    elif sys.argv[2].lower() == 'group':
	      doUpdateGroup()
	    elif sys.argv[2].lower() == 'nickname' or sys.argv[2].lower() == 'alias':
	      doUpdateNickName()
	    elif sys.argv[2].lower() == 'org':
	      doUpdateOrg()
	    elif sys.argv[2].lower() == 'resource':
	      doUpdateResourceCalendar()
	    elif sys.argv[2].lower() == 'domain':
	      doUpdateDomain()
	    else:
	      showUsage()
	      print 'Error: invalid argument to "gam update..."'
	      sys.exit(2)
	    sys.exit(0)
	  elif sys.argv[1].lower() == 'info':
	    if sys.argv[2].lower() == 'user':
	      doGetUserInfo()
	    elif sys.argv[2].lower() == 'group':
	      doGetGroupInfo()
	    elif sys.argv[2].lower() == 'nickname' or sys.argv[2].lower() == 'alias':
	      doGetNickNameInfo()
	    elif sys.argv[2].lower() == 'domain':
	      doGetDomainInfo()
	    elif sys.argv[2].lower() == 'org':
	      doGetOrgInfo()
	    elif sys.argv[2].lower() == 'resource':
	      doGetResourceCalendarInfo()
	    sys.exit(0)
	  elif sys.argv[1].lower() == 'delete':
	    if sys.argv[2].lower() == 'user':
	      doDeleteUser()
	    elif sys.argv[2].lower() == 'group':
	      doDeleteGroup()
	    elif sys.argv[2].lower() == 'nickname' or sys.argv[2].lower() == 'alias':
	      doDeleteNickName()
	    elif sys.argv[2].lower() == 'org':
	      doDeleteOrg()
	    elif sys.argv[2].lower() == 'resource':
	      doDeleteResourceCalendar()
	    sys.exit(0)
	  elif sys.argv[1].lower() == 'audit':
	    if sys.argv[2].lower() == 'monitor':
	      if sys.argv[3].lower() == 'create':
		doCreateMonitor()
	      elif sys.argv[3].lower() == 'list':
		doShowMonitors()
	      elif sys.argv[3].lower() == 'delete':
		doDeleteMonitor()
	    elif sys.argv[2].lower() == 'activity':
	      if sys.argv[3].lower() == 'request':
		doRequestActivity()
	      elif sys.argv[3].lower() == 'status':
		doStatusActivityRequests()
	      elif sys.argv[3].lower() == 'download':
		doDownloadActivityRequest()
	      elif sys.argv[3].lower() == 'delete':
		doDeleteActivityRequest()
	    elif sys.argv[2].lower() == 'export':
	      if sys.argv[3].lower() == 'status':
		doStatusExportRequests()
	      elif sys.argv[3].lower() == 'download':
		doDownloadExportRequest()
	      elif sys.argv[3].lower() == 'request':
		doRequestExport()
	      elif sys.argv[3].lower() == 'delete':
		doDeleteExport()
	    elif sys.argv[2].lower() == 'uploadkey':
	      doUploadAuditKey()
	    elif sys.argv[2].lower() == 'admin':
	      doAdminAudit()
	    sys.exit(0)
	  elif sys.argv[1].lower() == 'print':
	    if sys.argv[2].lower() == 'users':
	      doPrintUsers()
	    elif sys.argv[2].lower() == 'nicknames' or sys.argv[2].lower() == 'aliases':
	      doPrintNicknames()
	    elif sys.argv[2].lower() == 'groups':
	      doPrintGroups()
	    elif sys.argv[2].lower() == 'orgs' or sys.argv[2].lower() == 'ous':
	      doPrintOrgs()
	    elif sys.argv[2].lower() == 'resources':
	      doPrintResources()
	    elif sys.argv[2].lower() == 'postini':
	      doPrintPostini()
	    sys.exit(0)
	  elif sys.argv[1].lower() == 'oauth':
	    if sys.argv[2].lower() == 'request' or sys.argv[2].lower() == 'create':
	      doRequestOAuth()
	    elif sys.argv[2].lower() == 'info':
	      OAuthInfo()
	    elif sys.argv[2].lower() == 'delete' or sys.argv[2].lower() == 'revoke':
	      doDeleteOAuth()
	    elif sys.argv[2].lower() == 'select':
	      doOAuthSelect()
	    sys.exit(0)
	  elif sys.argv[1].lower() == 'calendar':
	    if sys.argv[3].lower() == 'showacl':
	      doCalendarShowACL()
	    elif sys.argv[3].lower() == 'add':
	      doCalendarAddACL()
	    elif sys.argv[3].lower() == 'del' or sys.argv[3].lower() == 'delete':
	      doCalendarDelACL()
	    elif sys.argv[3].lower() == 'update':
	      doCalendarUpdateACL()
	    elif sys.argv[3].lower() == 'wipe':
	      doCalendarWipeData()
	    sys.exit(0)
	  elif sys.argv[1].lower() == 'report':
	    showReport()
	    sys.exit(0)
	  elif sys.argv[1].lower() == 'whatis':
	    doWhatIs()
	    sys.exit(0)
	  users = getUsersToModify()
	  command = sys.argv[3].lower()
	  if command == 'print':
	    for user in users:
	      print user
	  elif command == 'show':
	    readWhat = sys.argv[4].lower()
	    if readWhat == 'labels' or readWhat == 'label':
	      showLabels(users)
	    elif readWhat == 'profile':
	      showProfile(users)
	    elif readWhat == 'calendars':
	      showCalendars(users)
	    elif readWhat == 'calsettings':
	      showCalSettings(users)
	    elif readWhat == 'sendas':
	      showSendAs(users)
	    elif readWhat == 'sig' or readWhat == 'signature':
	      getSignature(users)
	    elif readWhat == 'forward':
	      getForward(users)
	    elif readWhat == 'pop' or readWhat == 'pop3':
	      getPop(users)
	    elif readWhat == 'imap' or readWhat == 'imap4':
	      getImap(users)
	    elif readWhat == 'vacation':
	      getVacation(users)
	    elif readWhat == 'delegate' or readWhat == 'delegates':
	      getDelegates(users)
	  elif command == 'delete' or command == 'del':
	    delWhat = sys.argv[4].lower()
	    if delWhat == 'delegate':
	      deleteDelegate(users)
	    elif delWhat == 'calendar':
	      deleteCalendar(users)
	    elif delWhat == 'label':
	      doDeleteLabel(users)
	    elif delWhat == 'photo':
	      deletePhoto(users)
	  elif command == 'add':
	    addWhat = sys.argv[4].lower()
	    if addWhat == 'calendar':
	      addCalendar(users)
	  elif command == 'update':
	    if sys.argv[4].lower() == 'calendar':
	      updateCalendar(users)
	    elif sys.argv[4].lower() == 'photo':
	      doPhoto(users)
	  elif command == 'get':
	    if sys.argv[4].lower() == 'photo':
	      getPhoto(users)
	  elif command == 'profile':
	    doProfile(users)
	  elif command == 'imap':
	    doImap(users)
	  elif command == 'pop' or command == 'pop3':
	    doPop(users)
	  elif command == 'sendas':
	    doSendAs(users)
	  elif command == 'language':
	    doLanguage(users)
	  elif command == 'utf' or command == 'utf8' or command == 'utf-8' or command == 'unicode':
	    doUTF(users)
	  elif command == 'pagesize':
	    doPageSize(users)
	  elif command == 'shortcuts':
	    doShortCuts(users)
	  elif command == 'arrows':
	    doArrows(users)
	  elif command == 'snippets':
	    doSnippets(users)
	  elif command == 'label':
	    doLabel(users)
	  elif command == 'filter':
	    doFilter(users)
	  elif command == 'forward':
	    doForward(users)
	  elif command == 'sig' or command == 'signature':
	    doSignature(users)
	  elif command == 'vacation':
	    doVacation(users)
	  elif command == 'webclips':
	    doWebClips(users)
	  elif command == 'delegate' or command == 'delegates':
	    doDelegates(users)
	  else:
	    showUsage()
	    sys.exit(2)
	except IndexError:
	  showUsage()
	  sys.exit(2)
	except KeyboardInterrupt:
	  sys.exit(50)
	except socket.error, e:
	  print '\nError: %s' % e
	  sys.exit(3)
if __name__ == "__main__":
	main()
