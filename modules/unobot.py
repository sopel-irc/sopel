"""
Copyright 2010 Tamas Marki. All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are
permitted provided that the following conditions are met:

   1. Redistributions of source code must retain the above copyright notice, this list of
      conditions and the following disclaimer.

   2. Redistributions in binary form must reproduce the above copyright notice, this list
      of conditions and the following disclaimer in the documentation and/or other materials
      provided with the distribution.

THIS SOFTWARE IS PROVIDED BY TAMAS MARKI ``AS IS'' AND ANY EXPRESS OR IMPLIED
WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL TAMAS MARKI OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


[18:03] <Lako> .play w 3
[18:03] <unobot> TopMobil's turn. Top Card: [*]
[18:03] [Notice] -unobot- Your cards: [4][9][4][8][D2][D2]
[18:03] [Notice] -unobot- Next: hatcher (5 cards) - Lako (2 cards)
[18:03] <TopMobil> :O
[18:03] <Lako> :O
"""

import random
from datetime import datetime, timedelta

random.seed()

# Remember to change these 3 lines or nothing will work
CHANNEL = '##uno'
SCOREFILE = "/home/yanovich/phenny/unoscores.txt"
# Only the owner (starter of the game) can call .unostop to stop the game.
# But this calls for a way to allow others to stop it after the game has been idle for a while.
# After this set time, anyone can stop the game via .unostop
# Set the time ___in minutes___ here: (default is 5 mins)
INACTIVE_TIMEOUT = 5

STRINGS = {
    'ALREADY_STARTED' : '\x0300,01Game already started by %s! Type join to join!',
    'GAME_STARTED' : '\x0300,01IRC-UNO started by %s - Type join to join!',
    'GAME_STOPPED' : '\x0300,01Game stopped.',
    'CANT_STOP' : '\x0300,01%s is the game owner, you can\'t stop it! To force stop the game, please wait %s seconds.',
    'DEALING_IN' : '\x0300,01Dealing %s into the game as player #%s!',
    'JOINED' : '\x0300,01Dealing %s into the game as player #%s!',
    'ENOUGH' : '\x0300,01There are enough players, type .deal to start!',
    'NOT_STARTED' : '\x0300,01Game not started, type .uno to start!',
    'NOT_ENOUGH' : '\x0300,01Not enough players to deal yet.',    
    'NEEDS_TO_DEAL' : '\x0300,01%s needs to deal.',
    'ALREADY_DEALT' : '\x0300,01Already dealt.',
    'ON_TURN' : '\x0300,01It\'s %s\'s turn.',
    'DONT_HAVE' : '\x0300,01You don\'t have that card, %s',
    'DOESNT_PLAY' : '\x0300,01That card does not play, %s',
    'UNO' : '\x0300,01UNO! %s has ONE card left!',
    'WIN' : '\x0300,01We have a winner! %s!!!! This game took %s',
    'DRAWN_ALREADY' : '\x0300,01You\'ve already drawn, either .pass or .play!',
    'DRAWS' : '\x0300,01%s draws a card',
    'DRAWN_CARD' : '\x0300,01Drawn card: %s',
    'DRAW_FIRST' : '\x0300,01%s, you need to draw first!',
    'PASSED' : '\x0300,01%s passed!',
    'NO_SCORES' : '\x0300,01No scores yet',
    'TOP_CARD' : '\x0300,01%s\'s turn. Top Card: %s',
    'YOUR_CARDS' : '\x0300,01Your cards: %s',
    'NEXT_START' : '\x0300,01Next: ',
    'NEXT_PLAYER' : '\x0300,01%s (%s cards)',
    'D2' : '\x0300,01%s draws two and is skipped!',
    'CARDS' : '\x0300,01Cards: %s',
    'WD4' : '\x0300,01%s draws four and is skipped!',
    'SKIPPED' : '\x0300,01%s is skipped!',
    'REVERSED' : '\x0300,01Order reversed!',
    'GAINS' : '\x0300,01%s gains %s points!',
    'SCORE_ROW' : '\x0300,01#%s %s (%s points, %s games, %s won, %.2f points per game, %.2f percent wins)',
    'GAME_ALREADY_DEALT' : '\x0300,01Game has already been dealt, please wait until game is over or stopped.',
    'PLAYER_COLOR_ENABLED' : '\x0300,01Hand card colors \x0309,01enabled\x0300,01! Format: <COLOR>/[<CARD>].  Example: R/[D2] is a red Draw Two. Type \'.uno-help\' for more help.',
    'PLAYER_COLOR_DISABLED' : '\x0300,01Hand card colors \x0304,01disabled\x0300,01.',
    'DISABLED_PCE' : '\x0300,01Hand card colors is \x0304,01disabled\x0300,01 for %s. To enable, \'.pce-on\'',
    'ENABLED_PCE' : '\x0300,01Hand card colors is \x0309,01enabled\x0300,01 for %s. To disable, \'.pce-off\'',
    'PCE_CLEARED' : '\x0300,01All players\' hand card color setting is reset by %s.',
    'PLAYER_LEAVES' : '\x0300,01Player %s has left the game.',
    'OWNER_CHANGE' : '\x0300,01Owner %s has left the game. New owner is %s.',
}

class UnoBot:
    def __init__ (self):
        self.colored_card_nums = [ '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'R', 'S', 'D2' ]
        self.special_scores = { 'R' : 20, 'S' : 20, 'D2' : 20, 'W' : 50, 'WD4' : 50}
        self.colors = 'RGBY'
        self.special_cards = [ 'W', 'WD4' ]
        self.players = { }
        self.owners = { }
        self.players_pce = { }  # Player color enabled hash table
        self.playerOrder = [ ]
        self.game_on = False
        self.currentPlayer = 0
        self.topCard = None
        self.way = 1
        self.drawn = False
        self.scoreFile = SCOREFILE
        self.deck = [ ]
        self.prescores = [ ]
        self.dealt = False
        self.lastActive = datetime.now()
        self.timeout = timedelta(minutes=INACTIVE_TIMEOUT)
 
    def start(self, jenni, owner):
        if self.game_on:
            jenni.msg (CHANNEL, STRINGS['ALREADY_STARTED'] % self.game_on)
        else:
            self.lastActive = datetime.now()
            self.game_on = owner
            self.deck = [ ]
            jenni.msg (CHANNEL, STRINGS['GAME_STARTED'] % owner)
            self.players = { }
            self.players[owner] = [ ]
            self.playerOrder = [ owner ]
            if self.players_pce.get(owner, 0):
                jenni.notice(owner, STRINGS['ENABLED_PCE'] % owner)
    
    def stop (self, jenni, input):
        tmptime = datetime.now()
        if input.nick == self.game_on or tmptime - self.lastActive > self.timeout:
            jenni.msg (CHANNEL, STRINGS['GAME_STOPPED'])
            self.game_on = False
            self.dealt = False
        elif self.game_on:
            jenni.msg (CHANNEL, STRINGS['CANT_STOP'] % (self.game_on, self.timeout.seconds - (tmptime - self.lastActive).seconds))
            
    def join (self, jenni, input):
        #print dir (jenni.bot)
        #print dir (input)
        if self.game_on:
            if not self.dealt:
                if input.nick not in self.players:
                    self.players[input.nick] = [ ]
                    self.playerOrder.append (input.nick)
                    self.lastActive = datetime.now()
                    if self.players_pce.get(input.nick, 0):
                        jenni.notice(input.nick, STRINGS['ENABLED_PCE'] % input.nick)
                    if self.deck:
                        for i in xrange (0, 7):
                            self.players[input.nick].append (self.getCard ())
                        jenni.msg (CHANNEL, STRINGS['DEALING_IN'] % (input.nick, self.playerOrder.index (input.nick) + 1))
                    else:
                        jenni.msg (CHANNEL, STRINGS['JOINED'] % (input.nick, self.playerOrder.index (input.nick) + 1))
                        if len (self.players) == 2:
                            jenni.msg (CHANNEL, STRINGS['ENOUGH'])
            else:
                jenni.msg (CHANNEL, STRINGS['GAME_ALREADY_DEALT'])
        else:
            jenni.msg (CHANNEL, STRINGS['NOT_STARTED'])
    
    def deal (self, jenni, input):
        if not self.game_on:
            jenni.msg (CHANNEL, STRINGS['NOT_STARTED'])
            return
        if len (self.players) < 2:
            jenni.msg (CHANNEL, STRINGS['NOT_ENOUGH'])
            return
        if input.nick != self.game_on:
            jenni.msg (CHANNEL, STRINGS['NEEDS_TO_DEAL'] % self.game_on)
            return
        if len (self.deck):
            jenni.msg (CHANNEL, STRINGS['ALREADY_DEALT'])
            return
        self.startTime = datetime.now ()
        self.lastActive = datetime.now()
        self.deck = self.createnewdeck ()
        for i in xrange (0, 7):
            for p in self.players:
                self.players[p].append (self.getCard ())
        self.topCard = self.getCard ()
        while self.topCard in ['W', 'WD4']: self.topCard = self.getCard ()
        self.currentPlayer = 1
        self.cardPlayed (jenni, self.topCard)
        self.showOnTurn (jenni)
        self.dealt = True
    
    def play (self, jenni, input):
        if not self.game_on or not self.deck:
            return
        if input.nick != self.playerOrder[self.currentPlayer]:
            jenni.msg (CHANNEL, STRINGS['ON_TURN'] % self.playerOrder[self.currentPlayer])
            return
        tok = [z.strip () for z in str (input).upper ().split (' ')]
        if len (tok) != 3:
            return
        searchcard = ''
        if tok[1] in self.special_cards:
            searchcard = tok[1]
        else:
            searchcard = (tok[1] + tok[2])
        if searchcard not in self.players[self.playerOrder[self.currentPlayer]]:
            jenni.msg (CHANNEL, STRINGS['DONT_HAVE'] % self.playerOrder[self.currentPlayer])
            return
        playcard = (tok[1] + tok[2])
        if not self.cardPlayable (playcard):
            jenni.msg (CHANNEL, STRINGS['DOESNT_PLAY'] % self.playerOrder[self.currentPlayer])
            return
        
        self.drawn = False
        self.players[self.playerOrder[self.currentPlayer]].remove (searchcard)
        
        pl = self.currentPlayer
        
        self.incPlayer ()
        self.cardPlayed (jenni, playcard)

        if len (self.players[self.playerOrder[pl]]) == 1:
            jenni.msg (CHANNEL, STRINGS['UNO'] % self.playerOrder[pl])
        elif len (self.players[self.playerOrder[pl]]) == 0:
            jenni.msg (CHANNEL, STRINGS['WIN'] % (self.playerOrder[pl], (datetime.now () - self.startTime)))
            self.gameEnded (jenni, self.playerOrder[pl])
            return
            
        self.lastActive = datetime.now()
        self.showOnTurn (jenni)

    def draw (self, jenni, input):
        if not self.game_on or not self.deck:
            return
        if input.nick != self.playerOrder[self.currentPlayer]:
            jenni.msg (CHANNEL, STRINGS['ON_TURN'] % self.playerOrder[self.currentPlayer])
            return
        if self.drawn:
            jenni.msg (CHANNEL, STRINGS['DRAWN_ALREADY'])
            return
        self.drawn = True
        jenni.msg (CHANNEL, STRINGS['DRAWS'] % self.playerOrder[self.currentPlayer])
        c = self.getCard ()
        self.players[self.playerOrder[self.currentPlayer]].append (c)
        self.lastActive = datetime.now()
        jenni.notice (input.nick, STRINGS['DRAWN_CARD'] % self.renderCards (input.nick, [c], 0))

    # this is not a typo, avoiding collision with Python's pass keyword
    def passs (self, jenni, input):
        if not self.game_on or not self.deck:
            return
        if input.nick != self.playerOrder[self.currentPlayer]:
            jenni.msg (CHANNEL, STRINGS['ON_TURN'] % self.playerOrder[self.currentPlayer])
            return
        if not self.drawn:
            jenni.msg (CHANNEL, STRINGS['DRAW_FIRST'] % self.playerOrder[self.currentPlayer])
            return
        self.drawn = False
        jenni.msg (CHANNEL, STRINGS['PASSED'] % self.playerOrder[self.currentPlayer])
        self.incPlayer ()
        self.lastActive = datetime.now()
        self.showOnTurn (jenni)

    def top10 (self, jenni, input):
        self.rankings("ppg")
        i = 1
        for z in self.prescores[:10]:
            if self.game_on or self.deck:
                jenni.msg(input.nick, STRINGS['SCORE_ROW'] % (i, z[0], z[3], z[1], z[2], float(z[3])/float(z[1]), float(z[2])/float(z[1])*100))
            else:
                jenni.msg(input.nick, STRINGS['SCORE_ROW'] % (i, z[0], z[3], z[1], z[2], float(z[3])/float(z[1]), float(z[2])/float(z[1])*100))
            i += 1

    def createnewdeck (self):
        ret = [ ]
        for a in self.colored_card_nums:
            for b in self.colors:
                ret.append (b + a)
        for a in self.special_cards: 
            ret.append (a)
            ret.append (a)

        if len(self.playerOrder) <= 4:
            ret *= 2
            random.shuffle (ret)
        elif len(self.playerOrder) > 4:
            ret *= 3
            random.shuffle (ret)
        elif len(self.playerOrder) > 6:
            ret *= 4
            random.shuffle (ret)

        random.shuffle (ret)

        return ret
    
    def getCard(self):
        ret = self.deck[0]
        self.deck.pop (0)
        if not self.deck:
            self.deck = self.createnewdeck ()        
        return ret
    
    def showOnTurn (self, jenni):
        jenni.msg (CHANNEL, STRINGS['TOP_CARD'] % (self.playerOrder[self.currentPlayer], self.renderCards (None, [self.topCard], 1)))
        jenni.notice (self.playerOrder[self.currentPlayer], STRINGS['YOUR_CARDS'] % self.renderCards (self.playerOrder[self.currentPlayer], self.players[self.playerOrder[self.currentPlayer]], 0))
        msg = STRINGS['NEXT_START']
        tmp = self.currentPlayer + self.way
        if tmp == len (self.players):
            tmp = 0
        if tmp < 0:
            tmp = len (self.players) - 1
        arr = [ ]
        while tmp != self.currentPlayer:
            arr.append (STRINGS['NEXT_PLAYER'] % (self.playerOrder[tmp], len (self.players[self.playerOrder[tmp]])))
            tmp = tmp + self.way
            if tmp == len (self.players):
                tmp = 0
            if tmp < 0:
                tmp = len (self.players) - 1
        msg += ' - '.join (arr)
        jenni.notice (self.playerOrder[self.currentPlayer], msg)
    
    def showCards (self, jenni, user):
        if not self.game_on or not self.deck:
            return
        msg = STRINGS['NEXT_START']
        tmp = self.currentPlayer + self.way
        if tmp == len (self.players):
            tmp = 0
        if tmp < 0:
            tmp = len (self.players) - 1
        arr = [ ]
        k = len(self.players)
        while k > 0:
            arr.append (STRINGS['NEXT_PLAYER'] % (self.playerOrder[tmp], len (self.players[self.playerOrder[tmp]])))
            tmp = tmp + self.way
            if tmp == len (self.players):
                tmp = 0
            if tmp < 0:
                tmp = len (self.players) - 1
            k-=1
        msg += ' - '.join (arr)
        if user not in self.players:
            jenni.notice (user, msg) 
        else:
            jenni.notice (user, STRINGS['YOUR_CARDS'] % self.renderCards (user, self.players[user], 0))
            jenni.notice (user, msg)

    def renderCards (self, nick, cards, is_chan):
        ret = [ ]
        for c in sorted (cards):
            if c in ['W', 'WD4']:
                sp = ''
                if not is_chan:
                    sp = ' '
                ret.append ('\x0300,01[' + c + ']' + sp)
                continue
            if c[0] == 'W':
                c = c[-1] + '*'
            t = '\x0300,01\x03'
            if c[0] == 'B':
                t += '11,01'
            elif c[0] == 'Y':
                t += '08,01'
            elif c[0] == 'G':
                t += '09,01'
            elif c[0] == 'R':
                t += '04,01'
            if not is_chan:
                if self.players_pce.get(nick, 0):
                    t += '%s/ [%s]  ' % (c[0], c[1:])
                else:
                    t += '[%s]' % c[1:]
            else:
				t += '[%s] (%s)' % (c[1:], c[0])
            t += "\x0300,01"
            ret.append (t)
        return ''.join (ret)
    
    def cardPlayable (self, card):
        if card[0] == 'W' and card[-1] in self.colors:
            return True
        if self.topCard[0] == 'W':
            return card[0] == self.topCard[-1]
        return (card[0] == self.topCard[0]) or (card[1] == self.topCard[1])
    
    def cardPlayed (self, jenni, card):
        if card[1:] == 'D2':
            jenni.msg (CHANNEL, STRINGS['D2'] % self.playerOrder[self.currentPlayer])
            z = [self.getCard (), self.getCard ()]
            jenni.notice(self.playerOrder[self.currentPlayer], STRINGS['CARDS'] % self.renderCards (self.playerOrder[self.currentPlayer], z, 0))
            self.players[self.playerOrder[self.currentPlayer]].extend (z)
            self.incPlayer ()
        elif card[:2] == 'WD':
            jenni.msg (CHANNEL, STRINGS['WD4'] % self.playerOrder[self.currentPlayer])
            z = [self.getCard (), self.getCard (), self.getCard (), self.getCard ()]
            jenni.notice(self.playerOrder[self.currentPlayer], STRINGS['CARDS'] % self.renderCards (self.playerOrder[self.currentPlayer], z, 0))
            self.players[self.playerOrder[self.currentPlayer]].extend (z)
            self.incPlayer ()
        elif card[1] == 'S':
            jenni.msg (CHANNEL, STRINGS['SKIPPED'] % self.playerOrder[self.currentPlayer])
            self.incPlayer ()
        elif card[1] == 'R' and card[0] != 'W':
            jenni.msg (CHANNEL, STRINGS['REVERSED'])
            if len(self.players) > 2:
                self.way = -self.way
                self.incPlayer ()
                self.incPlayer ()
            else:
                self.incPlayer ()
        self.topCard = card
    
    def gameEnded (self, jenni, winner):
        try:
            score = 0
            for p in self.players:
                for c in self.players[p]:
                    if c[0] == 'W':
                        score += self.special_scores[c]
                    elif c[1] in [ 'S', 'R', 'D' ]:
                        score += self.special_scores[c[1:]]
                    else:
                        score += int (c[1])
            jenni.msg(CHANNEL, STRINGS['GAINS'] % (winner, score))
            self.saveScores (self.players.keys (), winner, score, (datetime.now () - self.startTime).seconds)
        except Exception, e:
            print 'Score error: %s' % e
        self.players = { }
        self.playerOrder = [ ]
        self.game_on = False
        self.currentPlayer = 0
        self.topCard = None
        self.way = 1
        self.dealt = False
        
    
    def incPlayer (self):
        self.currentPlayer = self.currentPlayer + self.way
        if self.currentPlayer == len (self.players):
            self.currentPlayer = 0
        if self.currentPlayer < 0:
            self.currentPlayer = len (self.players) - 1
    
    def saveScores (self, players, winner, score, time):
        from copy import copy
        prescores = { }
        try:
            f = open (self.scoreFile, 'r')
            for l in f:
                t = l.replace ('\n', '').split (' ')
                if len (t) < 4: continue
                if len (t) == 4: t.append (0)
                prescores[t[0]] = [t[0], int (t[1]), int (t[2]), int (t[3]), int (t[4])]
            f.close ()
        except: pass
        for p in players:
            if p not in prescores:
                prescores[p] = [ p, 0, 0, 0, 0 ]
            prescores[p][1] += 1
            prescores[p][4] += time
        prescores[winner][2] += 1
        prescores[winner][3] += score
        try:
            f = open (self.scoreFile, 'w')
            for p in prescores:
                f.write (' '.join ([str (s) for s in prescores[p]]) + '\n')
            f.close ()
        except Exception, e:
            print 'Failed to write score file %s' % e
     
    # Custom added functions ============================================== #
    def rankings (self, rank_type):
        from copy import copy
        self.prescores = [ ]
        try:
            f = open (self.scoreFile, 'r')
            for l in f:
                t = l.replace ('\n', '').split (' ')
                if len (t) < 4: continue
                self.prescores.append (copy (t))
                if len (t) == 4: t.append (0)
            f.close ()
        except: pass
        if rank_type == "ppg":
            self.prescores = sorted (self.prescores, lambda x, y: cmp ((y[1] != '0') and (float (y[3]) / int (y[1])) or 0, (x[1] != '0') and (float (x[3]) / int (x[1])) or 0))
        elif rank_type == "pw":
            self.prescores = sorted (self.prescores, lambda x, y: cmp ((y[1] != '0') and (float (y[2]) / int (y[1])) or 0, (x[1] != '0') and (float (x[2]) / int (x[1])) or 0))
        
        if not self.prescores:
            jenni.say(STRINGS['NO_SCORES'])
            
    def showTopCard_demand (self, jenni):
        if not self.game_on or not self.deck:
            return
        jenni.reply (STRINGS['TOP_CARD'] % (self.playerOrder[self.currentPlayer], self.renderCards (None, [self.topCard], 1)))

    def leave (self, jenni, input):
        self.remove_player(jenni, input.nick)

    def remove_player (self, jenni, nick):
        if not self.game_on:
            return

        user = self.players.get(nick, None)
        if user is not None:
            numPlayers = len(self.playerOrder)

            self.playerOrder.remove(nick)
            del self.players[nick]

            if self.way == 1 and self.currentPlayer == numPlayers - 1:
                self.currentPlayer = 0
            elif self.way == -1:
                if self.currentPlayer == 0:
                    self.currentPlayer = numPlayers - 2
                else: 
                    self.currentPlayer -= 1
            
            jenni.msg(CHANNEL, STRINGS['PLAYER_LEAVES'] % nick)
            if numPlayers == 2 and self.dealt or numPlayers == 1:
                jenni.msg (CHANNEL, STRINGS['GAME_STOPPED'])
                self.game_on = None
                self.dealt = None
                return
            
            if self.game_on == nick:
                self.game_on = self.playerOrder[0]
                jenni.msg(CHANNEL, STRINGS['OWNER_CHANGE'] % (nick, self.playerOrder[0]))

            if self.dealt:
                jenni.msg(CHANNEL, STRINGS['TOP_CARD'] % (self.playerOrder[self.currentPlayer], self.renderCards(None, [self.topCard], 1)))

    def enablePCE (self, jenni, nick):
        if not self.players_pce.get(nick, 0):
            self.players_pce.update({ nick : 1})
            jenni.notice(nick, STRINGS['PLAYER_COLOR_ENABLED'])
        else:
            jenni.notice(nick, STRINGS['ENABLED_PCE'] % nick)

    def disablePCE (self, jenni, nick):
        if self.players_pce.get(nick, 0):
            self.players_pce.update({ nick : 0})
            jenni.notice(nick, STRINGS['PLAYER_COLOR_DISABLED'])
        else:
            jenni.notice(nick, STRINGS['DISABLED_PCE'] % nick)

    def isPCEEnabled (self, jenni, nick):
        if not self.players_pce.get(nick, 0):
            jenni.notice(nick, STRINGS['DISABLED_PCE'] % nick)
        else:
            jenni.notice(nick, STRINGS['ENABLED_PCE'] % nick)

    def PCEClear (self, jenni, nick):
        if not self.owners.get(nick, 0):
            self.players_pce.clear()
            jenni.msg(CHANNEL, STRINGS['PCE_CLEARED'] % nick)

    def unostat (self, jenni, input):
        text = input.group().split()
        
        if len(text) != 3:
            jenni.say("Invalid input for stats command. Try '.unostats ppg 10' to show the top 10 ranked by points per game. You can also show rankings by percent-wins 'pw'.")
            return

        if text[1] == "pw" or text[1] == "ppg":
            self.rankings(text[1])
            self.rank_assist(jenni, input, text[2], "SCORE_ROW")
        
        if not self.prescores:
            jenni.say(STRINGS['NO_SCORES'])

    def rank_assist (self, jenni, input, nicknum, ranktype):
        if nicknum.isdigit():
            i = 1
            s = int(nicknum)
            for z in self.prescores[:s]:
                jenni.msg(input.nick, STRINGS[ranktype] % (i, z[0], z[3], z[1], z[2], float(z[3])/float(z[1]), float(z[2])/float(z[1])*100))
                i += 1
        else:
            j = 1
            t = str(nicknum)
            for y in self.prescores:
                if y[0] == t:
                    jenni.say(STRINGS[ranktype] % (j, y[0], y[3], y[1], y[2], float(y[3])/float(y[1]), float(y[2])/float(y[1])*100))
                j += 1
            
unobot = UnoBot ()

def uno(jenni, input):
    unobot.start (jenni, input.nick)
uno.commands = ['uno']
uno.priority = 'low'

def unostop(jenni, input):
    unobot.stop (jenni, input)
unostop.commands = ['unostop']
unostop.priority = 'low'

def join(jenni, input):
    unobot.join (jenni, input)
join.rule = '^join$'
join.priority = 'low'

def deal(jenni, input):
    unobot.deal (jenni, input)
deal.commands = ['deal']
deal.priority = 'low'

def play(jenni, input):
    unobot.play (jenni, input)
play.commands = ['play', 'p']
play.priority = 'low'

def draw(jenni, input):
    unobot.draw (jenni, input)
draw.commands = ['draw', 'd']
draw.priority = 'low'

def passs(jenni, input):
    unobot.passs (jenni, input)
passs.commands = ['pass', 'pa']
passs.priority = 'low'

def unotop10 (jenni, input):
    unobot.top10 (jenni, input)
unotop10.commands = ['unotop10']
unotop10.priority = 'low'

def show_user_cards (jenni, input):
    unobot.showCards (jenni, input.nick)
show_user_cards.commands = ['cards']
show_user_cards.priority = 'low'

def top_card (jenni, input):
    unobot.showTopCard_demand(jenni)
top_card.commands = ['top']
top_card.priority = 'low'

def leave (jenni, input):
    unobot.leave(jenni, input)
leave.commands = ['leave']
leave.priority = 'low'

def remove_on_part (jenni, input):
    unobot.remove_player(jenni, input.nick)
remove_on_part.event = 'PART'
remove_on_part.rule = '.*'
remove_on_part.priority = 'low'

def remove_on_quit (jenni, input):
    unobot.remove_player(jenni, input.nick)
remove_on_quit.event = 'QUIT'
remove_on_quit.rule = '.*'
remove_on_quit.priority = 'low'

def remove_on_nickchg (jenni, input):
    unobot.remove_player(jenni, input.nick)
remove_on_nickchg.event = 'NICK'
remove_on_nickchg.rule = '.*'
remove_on_nickchg.priority = 'low'

def unostats (jenni, input):
    unobot.unostat (jenni, input)
unostats.commands = ['unostats']
unostats.priority = 'low'

def uno_help (jenni, input):
    jenni.reply("For rules, examples, and getting started: http://j.mp/ekfaww")
uno_help.commands = ['uno-help']
uno_help.priority = 'low'

def uno_pce_on (jenni, input):
    unobot.enablePCE(jenni, input.nick)
uno_pce_on.commands = ['pce-on']
uno_pce_on.priority = 'low'

def uno_pce_off (jenni, input):
    unobot.disablePCE(jenni, input.nick)
uno_pce_off.commands = ['pce-off']
uno_pce_off.priority = 'low'

def uno_ispce (jenni, input):
    unobot.isPCEEnabled(jenni, input.nick)
uno_ispce.commands = ['pce']
uno_ispce.priority = 'low'

def uno_pce_clear (jenni, input):
    unobot.PCEClear(jenni, input.nick)
uno_pce_clear.commands = ['.pce-clear']
uno_pce_clear.priority = 'low'

if __name__ == '__main__':
    print __doc__.strip()

