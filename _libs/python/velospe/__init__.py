
from path import path

import spe
import es
import playerlib
import string
from spe import HookType
from spe import HookAction

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
        spe.parseINI(es.getAddonPath("_libs/python/velohook/signatures.ini"))
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
        else:message = chat.call_hook(userid, steamid, name, args[5], False)

    if not message == args[3]:
        args[3] = '\x01'+format(message)


    # These have to be strings - not None - so SPE can parse them.
    args[6] = ''
    args[7] = ''
    return (HookAction.Modified, 0)











