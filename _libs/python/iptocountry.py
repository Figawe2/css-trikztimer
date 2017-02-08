# IPToCountry by David Bowland
# ./addons/eventscripts/_libs/python/iptocountry.py
# Database provided by: http://Software77.net

"""
   * To use this library, you must first import it:

   import iptocountry


   * IPToCountry exposes the following functions:

   get_country(ip)
      - Returns full the country name, three-letter country abbreviation corresponding to IP
      ip = IP address to resolve to country name

   get_location_data(ip)
      - Returns a dictionary of location data corresponding to IP
         * Dictionary keys:
            ip_from      = Bottom long IP of location range
            ip_to        = Upper long IP of location range
            registry     = International registry agency through which the IP is registered
            assigned     = Unix time the IP was assigned
            country_2    = Two-character international country code
            country_3    = Three-character international country code (preferred because more unique)
            country_long = Country name
      ip = IP address to resolve to location data

   update_data(url=None)
      - Syncs server database with internet data--VERY SLOW
      - Returns True if update was sucessful otherwise returns False
      url = URL to download IPToCountry database

   get_last_update()
      - Returns the time of the last database update (in Unix time)

   update_from_file(path=None)
      - Updates the database from IpToCountry.csv that has been extracted, see the library link below to download the database
      - Returns True if data was successfully updated otherwise return False
      path = Absolute path to file (including IpToCountry.csv)


   * The following instance of CountryResolve is publicly exposed:

   service


   * The database for this library is provided by http://Software77.net. For more information, please see:

   http://software77.net/geo-ip/

   * NO CLAIMS ARE MADE REGARDING THE ACCURACY OF THIS DATABASE. Please use this library with that in mind.
"""

from __future__ import with_statement

__all__ = ['get_country', 'get_location_data', 'update_data', 'get_last_update', 'update_from_file', 'service']

import os
import sys
import traceback
import urllib
import zipfile

from contextlib import closing
from StringIO import StringIO


try:
   import psyco
   psyco.full()

   # Source server running EventScripts
   import es
   dbgmsg   = es.dbgmsg
   lib_path = es.getAddonPath('_libs') + '/python/'

   import installlib
   # Designate the database file for cleanup by installlib
   if installlib.infomanager.hasInstallInfo('iptocountry'):
      installinfo = installlib.infomanager.getInstallInfo('iptocountry')
      installinfo.addFile(lib_path + 'iptocountry.db')
      installlib.infomanager.saveInstallInfo('iptocountry', installinfo)

except ImportError:
   # IDLE
   def dbgmsg(x, msg): print msg
   lib_path = os.getcwd() + '/'


class CountryResolve(object):
   base_path  = lib_path
   default_db = 'http://software77.net/geo-ip?DL=2'

   def __init__(self, url=None):
      """ Loads database for later query """
      self.ip_data = []

      # Loads database
      if self.get_last_update():
         self._load_data()

      else:
         dbgmsg(0, 'No IPToCountry database found! Downloading database.')
         if not self.update_data(url):
            raise IOError, 'Could not download IPToCountry database!'
         self._load_data()

   def get_location_data(self, ip):
      """
      Returns a dictionary of location data corresponding to IP
      Dictionary keys:
         ip_from      = Bottom long IP of location range
         ip_to        = Upper long IP of location range
         registry     = International registry agency through which the IP is registered
         assigned     = Unix time the IP was assigned
         country_2    = Two-character international country code
         country_3    = Three-character international country code (preferred because more unique)
         country_long = Country name
      More information can be found here: http://software77.net/geo-ip/
      """
      if not self.ip_data:
         # No database to query
         return {}

      # Formats the IP, without port, to a list
      ip = ip.split(':', 1)[0]
      ip_list = map(int, ip.split('.'))

      # Validates the address for conversion to long format
      if len(ip_list) != 4:
         raise ValueError, 'Invalid IP address "%s"' % ip

      # Converts the IP to long IP format
      long_ip = ip_list[3] + (ip_list[2] << 8) + (ip_list[1] << 16) + (ip_list[0] << 24)

      # Finds the IP in the database
      for data in self.ip_data:
         if long_ip <= data['ip_to']:
            return data

      # No data found
      return {}

   def get_country(self, ip):
      """ Returns full country name and three-letter country abbreviation corresponding to IP """
      data = self.get_location_data(ip)

      if data:
         # Country data found
         return data['country_long'], data['country_3']

      else:
         # Country unknown
         return 'Unknown', 'Unknown'

   def update_data(self, url=None):
      """
      Syncs server database with internet data--VERY SLOW
      Returns True if update is sucessful, otherwise returns False
      """
      if not url:
         url = self.default_db

      # The database is not yet updated
      return_val = False

      # Download database
      raw_zip = self._download_database(url)

      # If download was sucessful, parse the databse
      if raw_zip:
         return_val = self._parse_zip(raw_zip)

         # Close the downloaded zip file
         raw_zip.close()

      # Update complete
      return return_val

   def get_last_update(self):
      """ Returns the time of the last database update (in Unix time) """
      path = self.base_path + 'iptocountry.db'
      return os.stat(path).st_mtime if os.path.isfile(path) else 0

   def update_from_file(path=None):
      """ Updates the database from an existing file (without download) """
      if path is None:
         path = self.base_path + 'IpToCountry.csv'
      return_val = False

      try:
         with open(path) as f:
            if self.__parse_database(f):
               self._load_data()
               return_val = True

      except:
         self.__show_exception(sys.exc_info())

      return return_val

   def _load_data(self):
      """
      Internal use recommended: This function is SLOW
      Loads the IP data into memory
      """
      self.ip_data = []
      dbpath = self.base_path + 'iptocountry.db'

      with open(dbpath) as data_db:
         # Reads the contents of the database to a dictionary
         for line in data_db.readlines():
            data = line.strip().split(',')
            self.ip_data.append({
             'ip_from': float(data[0]),
             'ip_to': float(data[1]),
             'registry': data[2],
             'assigned': float(data[3]),
             'country_2': data[4],
             'country_3': data[5].strip(),
             'country_long': data[6]})

   def _download_database(self, url):
      try:
         with closing(urllib.urlopen(url)) as u:
            return StringIO(u.read())
      except IOError:
         self.__show_exception(sys.exc_info())
      return None

   def _parse_zip(self, raw_zip):
      try:
         zip = zipfile.ZipFile(raw_zip)

         filelist = map(lambda x: x.filename, zip.filelist)
         db_file  = 'IpToCountry.csv' if 'IpToCountry.csv' in filelist else filelist[0]

         with closing(StringIO(zip.read(db_file))) as raw_database:
            return_val = self.___parse_database(raw_database)

         if return_val:
            self._load_data()

      except:
         self.__show_exception(sys.exc_info())
         return_val = False

      return return_val

   def ___parse_database(self, raw_database):
      """
      Internal use highly recommended
      Converts raw internet data into plain-text format
      """
      database = []

      for line in raw_database.readlines():
         if line.startswith('#'): continue

         if line.count(',') >= 6:
            database.append(line.strip().replace(r'"', '') + '\n')

      if not database: return False

      # Saves the parsed database
      with open(self.base_path + 'iptocountry.db', 'w') as new_db:
         # Sorts the database for quicker reference
         new_db.writelines(sorted(database, key=lambda x: float(x.split(',', 1)[0])))
         new_db.close()

      return True

   def __show_exception(self, exc_info):
      dbgmsg(1, 'IPToCountry update exception:')
      sys.excepthook(*exc_info)


# Public instance of CountryResolve
service = CountryResolve()


# Easy-reference functions to the public instance of CountryResolve
def get_country(*a, **kw):
   """ Returns full country name and three-letter country abbreviation of IP """
   return service.get_country(*a, **kw)


def get_location_data(*a, **kw):
   """ Returns a dictionary of location data of IP """
   return service.get_location_data(*a, **kw)


def get_last_update(*a, **kw):
   """ Returns the time of the last database update (in Unix time) """
   return service.get_last_update(*a, **kw)


def update_data(*a, **kw):
   """ Syncs server database with internet data--VERY SLOW """
   return service.update_data(*a, **kw)


def update_from_file(*a, **kw):
   """ Updates the database from an existing file (without download) """
   return service.update_from_file(*a, **kw)


""" Python program functionality """

if __name__ == '__main__':
   text = 'start'
   print 'Enter a blank line to exit\n'
   while text:
      text = raw_input('Enter IP address: ')
      if text:
         print 'Country: ', get_country(text), '\n'