#!/usr/bin/env python
"""
southpark.py - Jenni Southpark Module
Copyright 2011, Michael Yanovich (myano), Kenneth Sham (Kays)
Licensed under the Eiffel Forum License 2.

More info:
 * Jenni: https://github.com/myano/jenni/
 * Phenny: http://inamidst.com/phenny/
"""

from datetime import datetime, timedelta
import web, time, re

STRINGS = 'The next new episode of South Park will air on \x0300%s\x03, which is in: %s.'

HTMLEntities = {
    '&nbsp;'    : ' ',
    '&lt;'      : '<',
    '&gt;'      : '>',
    '&amp;'     : '&',
    '&quot;'    : '"',
    '&#39;'     : "'"
}

cache = {
    'TIMES'     : None,
    'NEW-EPI'   : None
}
cachets = {
    'TIMES'     : None,
    'NEW-EPI'   : None
}

months = {
    'January'   : 1,
    'February'  : 2,
    'March'     : 3,
    'April'     : 4,
    'May'       : 5,
    'June'      : 6,
    'July'      : 7,
    'August'    : 8,
    'September' : 9,
    'October'   : 10,
    'November'  : 11,
    'December'  : 12
}

cachetsreset = timedelta(hours=6)
maxtitlelen = 0
maxepilen = 0

def htmlDecode (html):
    for k, v in HTMLEntities.iteritems(): html = html.replace(k, v)
    return html

def southpark (jenni, input):
    global cache, cachets
    text = input.group().split()
    if len(text) > 1:
        if text[1] == 'cleartimes':
            cache['TIMES'] = None
            cachets['TIMES'] = None
            jenni.reply("Southpark times successfully cleared.")
            return
        elif text[1] == 'clearnewep':
            cache['NEW-EPI'] = None
            cachets['NEW-EPI'] = None
            jenni.reply("New episodes cleared from cache.")
        elif text[1] == 'times':
            southparktimes(jenni,input)
            return
    else:
        getNewShowDate(jenni)
southpark.commands = ['southpark']
southpark.priority = 'low'
southpark.rate = 30

def getNewShowDate (jenni):
    global cache, cachets
    tsnow = datetime.now()
    if cache['NEW-EPI'] is not None and cachets['NEW-EPI'] is not None and tsnow - cachets['NEW-EPI'] <= cachetsreset:
        gc = getcountdown(cache['NEW-EPI'])
        msg = STRINGS % (cache['NEW-EPI'], gc)
        jenni.say(msg)
        return

    today = time.localtime()
    src = web.get('http://en.wikipedia.org/wiki/List_of_South_Park_episodes')
    parts = src.split('Season 15 (2011)')
    cont = parts.pop()
    parts = cont.split('Shorts and unaired episodes')
    cont = parts[0]
    tds = cont.split('<td>')
    data = None
    for i in range(len(tds)):
        m = re.match('^[A-Z][a-z]{2,8} \d{1,2}, \d{4}', tds[i])
        if m is None:
            continue
        else:
            dt = time.strptime(m.group(), "%B %d, %Y")
            if dt < today:
                continue
            else:
                cache['NEW-EPI'] = m.group()
                cachets['NEW-EPI'] = tsnow
                rcd = getcountdown(m.group())
                msg = STRINGS % (m.group(), rcd)
                jenni.say(msg)
                break

def getcountdown (x):
    mon = x.split()[0]
    day = (x.split()[1][:-1])
    yr = int(x.split()[2])
    month = months[mon]
    diff = datetime(int(yr), int(month), int(day), 22, 00, 00) - datetime.today()
    weeks, days = divmod(diff.days, 7)
    minutes, seconds = divmod(diff.seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return "%s days, %s hours, %s minutes, and %s seconds" % (days, hours, minutes, seconds)

def southparktimes (jenni, input):
    global cache, cachets, maxtitlelen, maxepilen
    tsnow = datetime.now()
    if cache['TIMES'] is not None and cachets['TIMES'] is not None and tsnow - cachets['TIMES'] <= cachetsreset:
        printListings(jenni)
        return

    src = web.get('http://www.comedycentral.com/tv_schedule/index.jhtml?seriesId=11600&forever=please')
    parts = src.split('<div id="tv_schedule_content">')
    cont = parts[1]
    parts = cont.split('<div id="tv_schedule_bottom">')
    cont = parts[0]
    schedule = cont.split('<div class="schedDiv">')
    del schedule[0]

    info = []
    count = 5
    for s in schedule:
        s = s.replace('\n',' ')
        s = htmlDecode(s)

        ## gets the date
        sidx = s.index('<div class="schedDateText">')
        send = s.index('</div>', sidx)
        if sidx == -1 or send == -1: break

        m = re.search('>([^<]{2,})$', s[sidx:send])
        if m is None: break

        date = m.group(1).strip()
        sdate = time.strptime(date, '%A %b %d %Y')

        ## get episodes for the s-th date
        tepi = s.split('<td class="mtvn-cal-time"')
        del tepi[0]
        for t in tepi:

            ## gets the schedule time
            sidx = t.index('<nobr>')
            send = t.index('</nobr>', sidx)

            if sidx == -1 or send == -1: break

            stime = t[sidx+6:send].strip()

            ## gets the schedule episode name
            sidx = t.index('<b>', send)
            send = t.index('</b>', sidx)

            if sidx == -1 or send == -1: break

            stitle = t[sidx+3:send].strip()
            m = re.search('\(([^)]+)\)$', stitle)
            if m is None: break
            sepi = str(int(m.group(1)))
            if len(sepi) > maxepilen: maxepilen = len(sepi)
            stitle = stitle.replace(m.group(), '')
            lenstitle = len(stitle)
            if lenstitle > maxtitlelen: maxtitlelen = lenstitle

            ## gets the schedule episode desc
            sidx = send
            send = t.index('</span>', sidx)

            if send == -1: break

            m = re.search('>([^<]{2,})$', t[sidx:send])

            if m is None: break

            sdesc = m.group(1).strip()

            info.append([sdate, sepi, stitle, stime])

            count -= 1
            if count == 0: break
        if count == 0: break
    cache['TIMES'] = info
    cachets['TIMES'] = tsnow
    printListings(jenni)

def printListings (jenni):
    for i in cache['TIMES']:
        jenni.say('%s:   #%s - \x02%s\x02 %s (%s)   %s' % (time.strftime('%a %b %d', i[0]), i[1]+' '*(maxepilen-len(i[1])), i[2], ' '*(maxtitlelen-len(i[2])+5) , i[3], 'Comedy Central'))

if __name__ == '__main__':
    print __doc__.strip()
