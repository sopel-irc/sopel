#!/usr/bin/env python
"""
unostats.py -- Jenni's uno stat generator
Copyright 2011, Michael Yanovich, yanovich.net
Licensed under the Eiffel Forum License 2.

More info:
 * Jenni: https://github.com/myano/jenni/
 * Phenny: http://inamidst.com/phenny/
"""

def rankings (ranktype):
    from copy import copy
    prescores = [ ]
    try:
        f = open ("unoscores.txt", 'r')
        for l in f:
            t = l.replace ('\n', '').split (' ')
            if len (t) < 4: continue
            prescores.append (copy (t))
            if len (t) == 4: t.append (0)
        f.close ()
    except: pass
    #prescores = sorted (prescores, lambda x, y: cmp ((y[1] != '0') and (float (y[3]) / int (y[1])) or 0, (x[1] != '0') and (float (x[3]) / int (x[1])) or 0))
    prescores = sorted ( prescores, lambda x, y: cmp ( (y[1] != '0') and ( ( float(y[3]) / int(y[1]) ) / ( 1.01 - ( float(y[2]) / int(y[1]) ) ) ) or 0, (x[1] != '0') and ( ( float(x[3]) / int(x[1]) ) / ( 1.01 - ( float(x[2]) / int(x[1]) ) ) ) or 0 ) )

    return prescores

def showstats (jenni, input):
    STRINGS = { 'SCORE_ROW' : '\x0300,01#%s %s (%s points, %s games, %s won, %.2f points per game, %.2f percent wins, %.2f A)' }
    text = input.group().split()
    prescores = rankings(text)
    i = 1
    c = text[1]

    if c.isdigit():
        c = int(c)
        for z in prescores[:c]:
            jenni.msg(input.nick, STRINGS['SCORE_ROW'] % (i, z[0], z[3], z[1], z[2], float(z[3])/float(z[1]), float(z[2])/float(z[1])*100, ( float(z[3]) / int(z[1]) ) / ( 1.01 - ( float(z[2]) / int(z[1]) ) )))
            # float(z[3]) / ( (1.01 - ( float(z[2]) / int(z[1] ) ) ) * int(z[1]) )
            # ( float(z[3]) / int(z[1]) ) / ( 1.01 - ( float(z[2]) / int(z[1]) ) )
            i += 1
    else:
        j = 1
        t = str(c)
        jenni.say(t)
        for y in prescores:
            if y[0] == t:
                jenni.msg(input.nick, STRINGS['SCORE_ROW'] % (j, y[0], y[3], y[1], y[2], float(y[3])/float(y[1]), float(y[2])/float(y[1])*100, ( float(y[3]) / int(y[1]) ) / ( 1.01 - ( float(y[2]) / int(y[1]) ) )))
            j += 1

showstats.commands = ['unostats2']
