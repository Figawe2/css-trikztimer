from __future__ import with_statement
from path import path
from configobj import ConfigObj
from usermsg import hudhint, keyhint
import es
import spe
from spe.tools.player import SPEPlayer
import esc
import popuplib
import string
import os
import re
import time
import playerlib
import gamethread
import langlib
import operator



"""
.text:00582D10
.text:00582D10 _ZN9CCSPlayer10SetClanTagEPKc:          ; CODE XREF: .text:002ECFAAp
.text:00582D10                 push    ebp
.text:00582D11                 mov     ebp, esp
.text:00582D13                 sub     esp, 18h
.text:00582D16                 mov     eax, [ebp+0Ch]
.text:00582D19                 test    eax, eax
.text:00582D1B                 jz      short locret_582D39
.text:00582D1D                 mov     [esp+4], eax
.text:00582D21                 mov     eax, [ebp+8]
.text:00582D24                 mov     dword ptr [esp+8], 10h
.text:00582D2C                 add     eax, 1610h
.text:00582D31                 mov     [esp], eax
.text:00582D34                 call    near ptr _Z9V_strncpyPcPKci
.text:00582D39
.text:00582D39 locret_582D39:                          ; CODE XREF: .text:00582D1Bj
.text:00582D39                 leave
.text:00582D3A                 retn
"""


class Dissambly(object):
    def __init__(self):
        self.add = eax 

    def eax(self, eax="1610h"):
        self.eax=int(eax)
        self.offset = int(self.eax, 16)
        return self.offset






clantag_offset = 5648 if spe.platform == 'nt' else 5600


chat = es.import_addon('trikztimer/plugins/chat')


def load():
    set_clan_tag()

def setClanTag(userid, clan_tag):

    MAX_SIZE = 64

    length = len(clan_tag)



    if length >= MAX_SIZE:

        raise ValueError('Clan tag is too long')



    player = spe.getPlayer(userid)



    if not player:

        raise ValueError('Could not find player pointer')



    for offset, char in enumerate(clan_tag):

        spe.setLocVal('i', player + clantag_offset + offset, ord(char))



def set_clan_tag():
    for userid in es.getUseridList():
		 spe_player = SPEPlayer(userid)
		 steamid = es.getplayersteamid(userid)
		 player = playerlib.getPlayer(userid)
		 if not player.isdead:
			 if not es.isbot(userid):
				spe_player.clantag = "[%s]" % chat.getClantag(userid)
			 else:
				spe_player.clantag = "N Replay | "



    gamethread.delayedname(10, "tag", set_clan_tag)



