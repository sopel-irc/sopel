#!/usr/bin/env python
"""
weather.py - Phenny Weather Module
Copyright 2008, Sean B. Palmer, inamidst.com
Licensed under the Eiffel Forum License 2.

http://inamidst.com/phenny/
"""

import re, urllib
import web
from tools import deprecated

r_from = re.compile(r'(?i)([+-]\d+):00 from')

r_json = re.compile(r'^[,:{}\[\]0-9.\-+Eaeflnr-u \n\r\t]+$')
r_string = re.compile(r'("(\\.|[^"\\])*")')
env = {'__builtins__': None, 'null': None, 
       'true': True, 'false': False}

def json(text): 
   """Evaluate JSON text safely (we hope)."""
   if r_json.match(r_string.sub('', text)): 
      text = r_string.sub(lambda m: 'u' + m.group(1), text)
      return eval(text.strip(' \t\r\n'), env, {})
   raise ValueError('Input must be serialised JSON.')

def location(name): 
   name = urllib.quote(name.encode('utf-8'))
   uri = 'http://ws.geonames.org/searchJSON?q=%s&maxRows=1' % name
   for i in xrange(10): 
      u = urllib.urlopen(uri)
      if u is not None: break
   bytes = u.read()
   u.close()

   results = json(bytes)
   try: name = results['geonames'][0]['name']
   except IndexError: 
      return '?', '?', '0', '0'
   countryName = results['geonames'][0]['countryName']
   lat = results['geonames'][0]['lat']
   lng = results['geonames'][0]['lng']
   return name, countryName, lat, lng

class GrumbleError(object): 
   pass

def local(icao, hour, minute): 
   uri = ('http://www.flightstats.com/' + 
          'go/Airport/airportDetails.do?airportCode=%s')
   try: bytes = web.get(uri % icao)
   except AttributeError: 
      raise GrumbleError('A WEBSITE HAS GONE DOWN WTF STUPID WEB')
   m = r_from.search(bytes)
   if m: 
      offset = m.group(1)
      lhour = int(hour) + int(offset)
      lhour = lhour % 24
      return (str(lhour) + ':' + str(minute) + ', ' + str(hour) + 
              str(minute) + 'Z')
      # return (str(lhour) + ':' + str(minute) + ' (' + str(hour) + 
      #         ':' + str(minute) + 'Z)')
   return str(hour) + ':' + str(minute) + 'Z'

def code(phenny, search): 
   from icao import data
   
   if search.upper() in [loc[0] for loc in data]:
      return search.upper()
   else:
      name, country, latitude, longitude = location(search)
      if name == '?': return False
      sumOfSquares = (99999999999999999999999999999, 'ICAO')
      for icao_code, lat, lon in data: 
         latDiff = abs(latitude - lat)
         lonDiff = abs(longitude - lon)
         diff = (latDiff * latDiff) + (lonDiff * lonDiff)
         if diff < sumOfSquares[0]: 
            sumOfSquares = (diff, icao_code)
      return sumOfSquares[1]

@deprecated
def f_weather(self, origin, match, args): 
   """.weather <ICAO> - Show the weather at airport with the code <ICAO>."""
   if origin.sender == '#talis': 
      if args[0].startswith('.weather '): return

   icao_code = match.group(2)
   if not icao_code: 
      return self.msg(origin.sender, 'Try .weather London, for example?')

   icao_code = code(self, icao_code)

   if not icao_code: 
      self.msg(origin.sender, 'No ICAO code found, sorry')
      return

   uri = 'http://weather.noaa.gov/pub/data/observations/metar/stations/%s.TXT'
   try: bytes = web.get(uri % icao_code)
   except AttributeError: 
      raise GrumbleError('OH CRAP NOAA HAS GONE DOWN THE WEB IS BROKEN')
   if 'Not Found' in bytes: 
      self.msg(origin.sender, icao_code+': no such ICAO code, or no NOAA data')
      return

   metar = bytes.splitlines().pop()
   metar = metar.split(' ')

   if len(metar[0]) == 4: 
      metar = metar[1:]

   if metar[0].endswith('Z'): 
      time = metar[0]
      metar = metar[1:]
   else: time = None

   if metar[0] == 'AUTO': 
      metar = metar[1:]
   if metar[0] == 'VCU': 
      self.msg(origin.sender, icao_code + ': no data provided')
      return

   if metar[0].endswith('KT'): 
      wind = metar[0]
      metar = metar[1:]
   else: wind = None

   if ('V' in metar[0]) and (metar[0] != 'CAVOK'): 
      vari = metar[0]
      metar = metar[1:]
   else: vari = None

   if ((len(metar[0]) == 4) or 
       metar[0].endswith('SM')): 
      visibility = metar[0]
      metar = metar[1:]
   else: visibility = None

   while metar[0].startswith('R') and (metar[0].endswith('L') 
                                    or 'L/' in metar[0]): 
      metar = metar[1:]

   if len(metar[0]) == 6 and (metar[0].endswith('N') or 
                              metar[0].endswith('E') or 
                              metar[0].endswith('S') or 
                              metar[0].endswith('W')): 
      metar = metar[1:] # 7000SE?

   cond = []
   while (((len(metar[0]) < 5) or 
          metar[0].startswith('+') or 
          metar[0].startswith('-')) and (not (metar[0].startswith('VV') or
          metar[0].startswith('SKC') or metar[0].startswith('CLR') or 
          metar[0].startswith('FEW') or metar[0].startswith('SCT') or 
          metar[0].startswith('BKN') or metar[0].startswith('OVC')))): 
      cond.append(metar[0])
      metar = metar[1:]

   while '/P' in metar[0]: 
      metar = metar[1:]

   if not metar: 
      self.msg(origin.sender, icao_code + ': no data provided')
      return

   cover = []
   while (metar[0].startswith('VV') or metar[0].startswith('SKC') or
          metar[0].startswith('CLR') or metar[0].startswith('FEW') or
          metar[0].startswith('SCT') or metar[0].startswith('BKN') or
          metar[0].startswith('OVC')): 
      cover.append(metar[0])
      metar = metar[1:]
      if not metar: 
         self.msg(origin.sender, icao_code + ': no data provided')
         return

   if metar[0] == 'CAVOK': 
      cover.append('CLR')
      metar = metar[1:]

   if metar[0] == 'PRFG': 
      cover.append('CLR') # @@?
      metar = metar[1:]

   if metar[0] == 'NSC': 
      cover.append('CLR')
      metar = metar[1:]

   if ('/' in metar[0]) or (len(metar[0]) == 5 and metar[0][2] == '.'): 
      temp = metar[0]
      metar = metar[1:]
   else: temp = None

   if metar[0].startswith('QFE'): 
      metar = metar[1:]

   if metar[0].startswith('Q') or metar[0].startswith('A'): 
      pressure = metar[0]
      metar = metar[1:]
   else: pressure = None

   if time: 
      hour = time[2:4]
      minute = time[4:6]
      time = local(icao_code, hour, minute)
   else: time = '(time unknown)'

   if wind: 
      speed = int(wind[3:5])
      if speed < 1: 
         description = 'Calm'
      elif speed < 4: 
         description = 'Light air'
      elif speed < 7: 
         description = 'Light breeze'
      elif speed < 11: 
         description = 'Gentle breeze'
      elif speed < 16: 
         description = 'Moderate breeze'
      elif speed < 22: 
         description = 'Fresh breeze'
      elif speed < 28: 
         description = 'Strong breeze'
      elif speed < 34: 
         description = 'Near gale'
      elif speed < 41: 
         description = 'Gale'
      elif speed < 48: 
         description = 'Strong gale'
      elif speed < 56: 
         description = 'Storm'
      elif speed < 64: 
         description = 'Violent storm'
      else: description = 'Hurricane'

      degrees = wind[0:3]
      if degrees == 'VRB': 
         degrees = u'\u21BB'.encode('utf-8')
      elif (degrees <= 22.5) or (degrees > 337.5): 
         degrees = u'\u2191'.encode('utf-8')
      elif (degrees > 22.5) and (degrees <= 67.5): 
         degrees = u'\u2197'.encode('utf-8')
      elif (degrees > 67.5) and (degrees <= 112.5): 
         degrees = u'\u2192'.encode('utf-8')
      elif (degrees > 112.5) and (degrees <= 157.5): 
         degrees = u'\u2198'.encode('utf-8')
      elif (degrees > 157.5) and (degrees <= 202.5): 
         degrees = u'\u2193'.encode('utf-8')
      elif (degrees > 202.5) and (degrees <= 247.5): 
         degrees = u'\u2199'.encode('utf-8')
      elif (degrees > 247.5) and (degrees <= 292.5): 
         degrees = u'\u2190'.encode('utf-8')
      elif (degrees > 292.5) and (degrees <= 337.5): 
         degrees = u'\u2196'.encode('utf-8')

      if not icao_code.startswith('EN') and not icao_code.startswith('ED'): 
         wind = '%s %skt (%s)' % (description, speed, degrees)
      elif icao_code.startswith('ED'): 
         kmh = int(round(speed * 1.852, 0))
         wind = '%s %skm/h (%skt) (%s)' % (description, kmh, speed, degrees)
      elif icao_code.startswith('EN'): 
         ms = int(round(speed * 0.514444444, 0))
         wind = '%s %sm/s (%skt) (%s)' % (description, ms, speed, degrees)
   else: wind = '(wind unknown)'

   if visibility: 
      visibility = visibility + 'm'
   else: visibility = '(visibility unknown)'

   if cover: 
      level = None
      for c in cover: 
         if c.startswith('OVC') or c.startswith('VV'): 
            if (level is None) or (level < 8): 
               level = 8
         elif c.startswith('BKN'): 
            if (level is None) or (level < 5): 
               level = 5
         elif c.startswith('SCT'): 
            if (level is None) or (level < 3): 
               level = 3
         elif c.startswith('FEW'): 
            if (level is None) or (level < 1): 
               level = 1
         elif c.startswith('SKC') or c.startswith('CLR'): 
            if level is None: 
               level = 0

      if level == 8: 
         cover = u'Overcast \u2601'.encode('utf-8')
      elif level == 5: 
         cover = 'Cloudy'
      elif level == 3: 
         cover = 'Scattered'
      elif (level == 1) or (level == 0): 
         cover = u'Clear \u263C'.encode('utf-8')
      else: cover = 'Cover Unknown'
   else: cover = 'Cover Unknown'

   if temp: 
      if '/' in temp: 
         temp = temp.split('/')[0]
      else: temp = temp.split('.')[0]
      if temp.startswith('M'): 
         temp = '-' + temp[1:]
      try: temp = int(temp)
      except ValueError: temp = '?'
   else: temp = '?'

   if pressure: 
      if pressure.startswith('Q'): 
         pressure = pressure.lstrip('Q')
         if pressure != 'NIL': 
            pressure = str(int(pressure)) + 'mb'
         else: pressure = '?mb'
      elif pressure.startswith('A'): 
         pressure = pressure.lstrip('A')
         if pressure != 'NIL': 
            inches = pressure[:2] + '.' + pressure[2:]
            mb = int(float(inches) * 33.7685)
            pressure = '%sin (%smb)' % (inches, mb)
         else: pressure = '?mb'

         if isinstance(temp, int): 
            f = round((temp * 1.8) + 32, 2)
            temp = u'%s\u2109 (%s\u2103)'.encode('utf-8') % (f, temp)
   else: pressure = '?mb'
   if isinstance(temp, int): 
      temp = u'%s\u2103'.encode('utf-8') % temp

   if cond: 
      conds = cond
      cond = ''

      intensities = {
         '-': 'Light', 
         '+': 'Heavy'
      }

      descriptors = {
         'MI': 'Shallow', 
         'PR': 'Partial', 
         'BC': 'Patches', 
         'DR': 'Drifting', 
         'BL': 'Blowing', 
         'SH': 'Showers of', 
         'TS': 'Thundery', 
         'FZ': 'Freezing', 
         'VC': 'In the vicinity:'
      }

      phenomena = {
         'DZ': 'Drizzle', 
         'RA': 'Rain', 
         'SN': 'Snow', 
         'SG': 'Snow Grains', 
         'IC': 'Ice Crystals', 
         'PL': 'Ice Pellets', 
         'GR': 'Hail', 
         'GS': 'Small Hail', 
         'UP': 'Unknown Precipitation', 
         'BR': 'Mist', 
         'FG': 'Fog', 
         'FU': 'Smoke', 
         'VA': 'Volcanic Ash', 
         'DU': 'Dust', 
         'SA': 'Sand', 
         'HZ': 'Haze', 
         'PY': 'Spray', 
         'PO': 'Whirls', 
         'SQ': 'Squalls', 
         'FC': 'Tornado', 
         'SS': 'Sandstorm', 
         'DS': 'Duststorm', 
         # ? Cf. http://swhack.com/logs/2007-10-05#T07-58-56
         'TS': 'Thunderstorm', 
         'SH': 'Showers'
      }

      for c in conds: 
         if c.endswith('//'): 
            if cond: cond += ', '
            cond += 'Some Precipitation'
         elif len(c) == 5: 
            intensity = intensities[c[0]]
            descriptor = descriptors[c[1:3]]
            phenomenon = phenomena.get(c[3:], c[3:])
            if cond: cond += ', '
            cond += intensity + ' ' + descriptor + ' ' + phenomenon
         elif len(c) == 4: 
            descriptor = descriptors.get(c[:2], c[:2])
            phenomenon = phenomena.get(c[2:], c[2:])
            if cond: cond += ', '
            cond += descriptor + ' ' + phenomenon
         elif len(c) == 3: 
            intensity = intensities.get(c[0], c[0])
            phenomenon = phenomena.get(c[1:], c[1:])
            if cond: cond += ', '
            cond += intensity + ' ' + phenomenon
         elif len(c) == 2: 
            phenomenon = phenomena.get(c, c)
            if cond: cond += ', '
            cond += phenomenon

   # if not cond: 
   #    format = u'%s at %s: %s, %s, %s, %s'
   #    args = (icao, time, cover, temp, pressure, wind)
   # else: 
   #    format = u'%s at %s: %s, %s, %s, %s, %s'
   #    args = (icao, time, cover, temp, pressure, cond, wind)

   if not cond: 
      format = u'%s, %s, %s, %s - %s %s'
      args = (cover, temp, pressure, wind, str(icao_code), time)
   else: 
      format = u'%s, %s, %s, %s, %s - %s, %s'
      args = (cover, temp, pressure, cond, wind, str(icao_code), time)

   self.msg(origin.sender, format.encode('utf-8') % args)
f_weather.rule = (['weather'], r'(.*)')

if __name__ == '__main__': 
   print __doc__.strip()
