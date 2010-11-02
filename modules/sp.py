#!/usr/bin/env python
"""
sp.py - South Park Module
Author: Michael Yanovich
Phenny (about): http://inamidst.com/phenny/

Feature requested by AJoseph
"""

from BeautifulSoup import BeautifulSoup
import web, datetime, time, re

def sp (phenny, input):
    """ Displays how many days, hours, minutes, and seconds until the next *new* episode of South Park """
    html = web.get("http://www.imdb.com/title/tt0121955/episodes")
    soup = BeautifulSoup(html)
    b = soup.findAll(attrs={"class":"odd"})
    c = str(b[-1])
    soup2 = BeautifulSoup(c)
    find_date = re.compile(r'<a href="/tvgrid/.*/.*">')
    d = find_date.findall(c)
    date = d[0][17:27]
    timee = d[0][28:32]
    g = date.split('-')
    h = str(date) + " " + str(timee) 
    j = time.mktime(time.strptime(h, '%Y-%m-%d %H%M'))
    k = time.time() - j
    #phenny.say("date: " + date)
    #phenny.say("time: " + timee)
    p = datetime.datetime(int(g[0]), int(g[1]), int(g[2]), int(timee[:2]), int(timee[2:]))
    q = datetime.datetime.now() - p
    phenny.say("Next episode of South Park in " + str(q)[1:])
sp.commands = ['sp']

if __name__ == '__main__':
    print __doc__.strip()
