import es
import esc
import string
import os
import re
import time
import playerlib
import popuplib
import gamethread
import langlib
import operator
import cPickle as pickle

from configobj import ConfigObj

from path import path
import spe
import playerlib
import string
from spe import HookType
from spe import HookAction


nospam = dict()

trikztimer = es.import_addon("trikztimer")
mysql = es.import_addon("trikztimer/mysql")
tags = ConfigObj(es.getAddonPath( "trikztimer" ) + "/plugins/chat/tags.ini")
dogtags = {}
sync_chat = {}




version = '1.1'

# =============================================================================
# >> Imports
# =============================================================================
from configobj import ConfigObj
import re



class ChatHandler:
    def __init__(self):
        self.hook = None

    def signature_Hook(self, func):
        self.hook = func

    def signature_loadHook(self):
        spe.parseINI('trikztimer/plugins/' + path(__file__).namebase + '/signatures.ini')
        spe.detourFunction('SayText2Filter', HookType.Pre, preHook)

    def signature_unloadHook(self):
        spe.undetourFunction('SayText2Filter', HookType.Pre, preHook)

    def getHook(self):
        return self.hook

    def call_hook(self, userid, steamid, name, text, channel):
        return self.hook(userid, steamid, name, text, channel)


chat = ChatHandler()
# =============================================================================
# >> GLOBALS
# =============================================================================
CUSTOMCOLORS_PATH = '_libs/python/esc/colors.ini'
colors = ConfigObj(es.getAddonPath(CUSTOMCOLORS_PATH))



# =============================================================================
# >> Format Colors
# =============================================================================
def formatColor(r, g, b, a=255):
    return '\x08%02X%02X%02X%02X' % (r, g, b, a)



def format(message):
    # > Find Colors
    re1 = '(#)'  # Any Single Character 1
    re2 = '(\\d+)'  # Integer Number 1
    re3 = '(,)'  # Any Single Character 2
    re4 = '(\\d+)'  # Integer Number 2
    re5 = '(,)'  # Any Single Character 3
    re6 = '(\\d+)'  # Integer Number 3

    rg = re.compile(re1 + re2 + re3 + re4 + re5 + re6, re.IGNORECASE | re.DOTALL)
    m = re.findall(rg, message)
    # > Format
    for match in m:
        # > Get
        h, r, k1, g, k2, b = match
        # > Format
        r = int(r)
        g = int(g)
        b = int(b)
        # > Make Color-String
        message = message.replace(''.join(map(str, match)), formatColor(r, g, b))

    # > Custom Colors
    for color in colors:
        r, g, b = tuple(colors[color])
        r = int(r)
        g = int(g)
        b = int(b)
        message = message.replace(color, formatColor(r, g, b))

    return message



def preHook(args):
    userid = es.getuserid(str(args[4]))
    steamid = es.getplayersteamid(userid)
    name = es.getplayername(userid)
    # Name args[4]
    message = args[3]
    method = chat.getHook()
    if hasattr(method, '__call__'):
        if args[3] in ["Cstrike_Chat_Spec", "Cstrike_Chat_CT", "Cstrike_Chat_T"]:
            message = chat.call_hook(userid, steamid, name, args[5], True)
        else:
            message = chat.call_hook(userid, steamid, name, args[5], False)



    args[3] = '\x01'+format(message)
    args[4] = ''
    args[5] = ''
    args[6] = ''
    args[7] = ''
    return (HookAction.Modified, 0)




def load_sm_dogtags():
            global dogtags
            dictPath = os.path.join( es.getAddonPath("trikztimer"), "/database/sm_dogtags.db")
            if os.path.isfile(dictPath):
              fileStream = open(dictPath, 'rb')
              dogtags = pickle.load(fileStream)
              fileStream.close()



def sm_save_dogtags():
             dictPath = os.path.join( es.getAddonPath("trikztimer"), "database/sm_dogtags.db")
             fileStream = open(dictPath, 'wb')
             pickle.dump(dogtags, fileStream)
             fileStream.close()




def player_activate(ev):
    userid    = ev['userid']
    steamid   = es.getplayersteamid(userid)
    name      = es.getplayername(userid)
    if not steamid in dogtags:
       dogtags[steamid] = {'addtag':'!addtag','textcolor':'#20,20,230','current_tag':'default', 'guild_tag':0, 'level_tag':1, 'no_tag':0}

    if steamid not in sync_chat:
            sync_chat[steamid] = {'antispam':0}

    esc.tell(userid, '#0,255,0Patch 3.523, Welcome to Trikz Cafe')




def load():
    load_sm_dogtags()
    chat.signature_Hook(chat_handler)
    chat.signature_loadHook()
    mysql.query.save()
    for userid in es.getUseridList():
        steamid = es.getplayersteamid(userid)
        if not steamid in dogtags:
            dogtags[steamid] = {'addtag':'!addtag','textcolor':'#20,20,230','current_tag':'default', 'guild_tag':0, 'level_tag':1, 'no_tag':0}
    print("DuoPlanet - Module 'chat': Registered a event (chat_handler) ")


def unload():
    chat.signature_unloadHook()
    print("DuoPlanet - Module 'chat': Unregistered a event (chat_handler) ")


def dog_tags(userid):
    steamid = es.getplayersteamid(userid)
    rank = getPos(steamid)
    points = getPoints(steamid)
    dog_t = popuplib.easymenu(str(steamid) + 'Dog_tags', None, dog_tags_select)
    dog_t.settitle("Dog Tags")
    dog_t.setdescription('Current: None')
    dog_t.c_beginsep = " "
    dog_t.c_pagesep = " "
    for pos in tags:

        if not pos.startswith('[U:'):


            if str(tags[pos]['type']) == "ranked":
                if points > 7000:
                    if int(rank) >= int(tags[pos]['min_rank']):
                            dog_t.addoption(pos, pos)
                    else:
                        dog_t.addoption(pos, pos, state=False)
                else:
                        dog_t.addoption(pos, pos, state=False)



            elif tags[pos]["type"] == "points":
                 if points >= int(tags[pos]['min_points']):
                        dog_t.addoption(pos, pos)

                 else:
                        dog_t.addoption(pos, pos, state=False)



    dog_t.send(userid)



def dog_tags_select(userid, choice, popupid):
    userid = steamid = es.getplayersteamid(userid)
    dogtags[steamid]['current_tag'] = choice
    esc.tell(userid, '#255,0,0[Tags] #greyYou have updated your tag to #yellow%s' % choice)



def getPos(steamid):
    index = 0
    data = mysql.query.fetchall("SELECT steamid FROM stats ORDER BY points DESC")
    for item in data:
        index += 1
        if item[0] == steamid:
            return index


def getPoints(steamid):
    data = mysql.query.fetchone("SELECT points FROM stats WHERE steamid = '%s'" % steamid)
    points = int(data[0])
    return points



def getTag(userid):
    player = playerlib.getPlayer(userid)
    steamid = player.steamid
    plyName = player.name

    if player.team == 2:

        team = '#255,61,61'

    elif player.team == 3:

        team = '#154,205,255'

    else:

        team = '#154,205,255'

    rank = getPos(steamid)
    points = getPoints(steamid)

    color = "Error Tag"
    _getprop = None
    for pos in tags:

      if not steamid in tags:

        if not pos.startswith('[U:'):


            if str(tags[pos]['type']) == "ranked":
                if int(rank) <= int(tags[pos]['min_rank']) and int(rank) >= int(tags[pos]['max_rank']):
                        _getprop = str(tags[pos]['tag']).replace('#team', team).replace('#name', plyName)
                        color = _getprop


            elif tags[pos]["type"] == "points":
                 if points >= int(tags[pos]['min_points']) and points <= int(tags[pos]['max_points']):
                        _getprop = str(tags[pos]['tag']).replace('#team', team).replace('#name', plyName)
                        color = _getprop

      else:
                    _getprop = str(tags[steamid]['tag']).replace('#team', team).replace('#name', plyName)
                    color = _getprop
    return color



def getClantag(userid):
    player = playerlib.getPlayer(userid)
    steamid = player.steamid
    plyName = player.name



    if player.team == 2:

        team = '#255,61,61'

    elif player.team == 3:

        team = '#154,205,255'

    else:

        team = '#154,205,255'

    rank = getPos(steamid)
    points = getPoints(steamid)

    color = "Error Tag"
    _getprop = None
    for pos in tags:

      if not steamid in tags:

        if not pos.startswith('[U:'):

            if str(tags[pos]['type']) == "ranked":
                if int(rank) <= int(tags[pos]['min_rank']) and int(rank) >= int(tags[pos]['max_rank']):
                        color = pos

            elif tags[pos]["type"] == "points":
                 if points >= int(tags[pos]['min_points']) and points <= int(tags[pos]['max_points']):
                        color = pos

      else:
                    _getprop = str(tags[steamid]['clan_tag']).replace('#team', team).replace('#name', plyName)
                    color = _getprop

    return color



def getRankedTitle():
    for pos in tags:

      if not steamid in tags:

        if not pos.startswith('U:'):

            if str(tags[pos]['type']) == "ranked":
                if int(rank) <= int(tags[pos]['min_rank']) and int(rank) >= int(tags[pos]['max_rank']):

                        return pos


def auto_correct(text):

    """ Correcting names """
    try:
     """
        for item in text.split(" "):
            player = es.getuserid(item)
            if player:
                player2 = playerlib.getPlayer(player)
                if player2.team == 2:

                    team = '#255,61,61'

                elif player2.team == 3:

                    team = '#154,205,255'

                else:

                    team = '#154,205,255'
                if len(item) >= int(len(es.getplayername(player)) / 5) and len(item) >= 3:
                    name = len(es.getplayername(player))
                    if name > 12:
                        text = text.replace(item, ("%s" % (es.getplayername(player)[:16])))
                    else:
                        text = text.replace(item, ("%s" % (es.getplayername(player)[:12])))

     """
     text = str(text).replace('\\n', '\n').replace('\n', '\ n').replace('\\t', '\t').replace('\t', '\ t')

    finally:
        return text


message = ["lol", 0]

def chat_handler(userid, steamid, name, text, teamonly):
    player = playerlib.getPlayer(userid)
    steamid = steamid
    plyName = name
    ip_address = player.address.split(':')[0]


    if player.team == 2:

        team = '#255,61,61'

    elif player.team == 3:

        team = '#154,205,255'

    else:

        team = '#154,205,255'

    rank = getPos(steamid)
    points = getPoints(steamid)

    color = "Error Tag"
    _getprop = None
    for pos in tags:

      if not steamid in tags:

        if not pos.startswith('[U:'):


            if str(tags[pos]['type']) == "ranked":
                if int(rank) <= int(tags[pos]['min_rank']) and int(rank) >= int(tags[pos]['max_rank']):
                        _getprop = str(tags[pos]['tag']).replace('#team', team).replace('#name', plyName)
                        color = _getprop


            elif tags[pos]["type"] == "points":
                 if points >= int(tags[pos]['min_points']) and points <= int(tags[pos]['max_points']):
                        _getprop = str(tags[pos]['tag']).replace('#team', team).replace('#name', plyName)
                        color = _getprop

      else:
                    _getprop = str(tags[steamid]['tag']).replace('#team', team).replace('#name', plyName)
                    color = _getprop




    if text == "!tags":
        dog_tags(userid)


    if player.team == 1:

        if teamonly:
                return  '(Spectator) %s %s' % (color, text)


        else:
            for users in playerlib.getPlayerList('#alive'):
              if not message[0] == "*SPEC* %s %s" % (color, text):

                esc.tell(users, "*SPEC* %s %s" % (color, text))

            message[0] = ("*SPEC* %s %s" % (color, text))
            message[1] = 1

            return '*SPEC* %s %s' % (color, text)


    if player.team == 2:

        if teamonly:

            if player.isdead:
                for users in playerlib.getPlayerList('#alive'):
                    esc.tell(users, '*DEAD*(Terrorist) %s %s' % (color, text))

                    return '*DEAD*(Terrorist) %s %s' % (color, text)

            else:

                    return '(Terrorist) %s %s' % (color, text)
        else:

            if player.isdead:
                for users in playerlib.getPlayerList('#alive'):
                    esc.tell(users, '*DEAD* %s %s' % (color, text))

                return '*DEAD* %s %s' % (color, text)

            else:

                return '%s %s' % (color, text)

    if player.team == 3:

        if teamonly:

            if player.isdead:
                for users in playerlib.getPlayerList('#alive'):
                    esc.tell(users, '*DEAD*(Counter-Terrorist) %s %s' % (color, text))

                return '*DEAD*(Counter-Terrorist) %s %s' % (color, text)

            else:

                   return '(Counter-Terrorist) %s %s' % (color, text)


        else:

            if player.isdead:
                for users in playerlib.getPlayerList('#alive'):
                    esc.tell(users, '*DEAD* %s %s' % (color, text))

                return '*DEAD* %s %s' % (color, text)


            else:

                return '%s %s' % (color, text)









