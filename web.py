#!/usr/bin/env python
"""
web.py - Web Facilities
Author: Sean B. Palmer, inamidst.com
About: http://inamidst.com/phenny/
"""

import urllib

class Grab(urllib.URLopener): 
   def __init__(self, *args): 
      self.version = 'Mozilla/5.0 (Phenny)'
      urllib.URLopener.__init__(self, *args)
   def http_error_default(self, url, fp, errcode, errmsg, headers): 
      return urllib.addinfourl(fp, [headers, errcode], "http:" + url)
urllib._urlopener = Grab()

def get(uri): 
   if not uri.startswith('http'): 
      return
   u = urllib.urlopen(uri)
   bytes = u.read()
   u.close()
   return bytes

def head(uri): 
   if not uri.startswith('http'): 
      return
   u = urllib.urlopen(uri)
   info = u.info()
   u.close()
   return info

def post(uri, query): 
   if not uri.startswith('http'): 
      return
   data = urllib.urlencode(query)
   u = urllib.urlopen(uri, data)
   bytes = u.read()
   u.close()
   return bytes

if __name__=="__main__": 
   main()
