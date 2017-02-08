# Thx to Ayuto
# Version 1.1
# [+] More Colors
# [+] Public variables
# [FIX] Displaying color-codes in console
version = '1.1'

# =============================================================================
# >> Imports
# =============================================================================
import es
from configobj import ConfigObj
import usermsg
import re

# =============================================================================
# >> GLOBALS
# =============================================================================
CUSTOMCOLORS_PATH = '_libs/python/esc/colors.ini'
colors = ConfigObj(es.getAddonPath(CUSTOMCOLORS_PATH))

# =============================================================================
# >> Format Colors
# =============================================================================
def formatColor(r, g, b, a=255):
    return '\x08%02X%02X%02X%02X'% (r, g, b, a)

def format(message):
    # > Find Colors
    re1='(#)'	# Any Single Character 1
    re2='(\\d+)'	# Integer Number 1
    re3='(,)'	# Any Single Character 2
    re4='(\\d+)'	# Integer Number 2
    re5='(,)'	# Any Single Character 3
    re6='(\\d+)'	# Integer Number 3

    rg = re.compile(re1+re2+re3+re4+re5+re6,re.IGNORECASE|re.DOTALL)
    m = re.findall(rg,message)
    # > Format
    for match in m:
        # > Get
        h,r,k1,g,k2,b= match          
        # > Format
        r = int(r)
        g = int(g)
        b = int(b)
        # > Make Color-String
        message = message.replace(''.join(map(str,match)), formatColor(r,g,b))
        
    # > Custom Colors
    for color in colors:
        r,g,b = tuple(colors[color])
        r = int(r)
        g = int(g)
        b = int(b)
        message = message.replace(color, formatColor(r,g,b))
        
    return message
    
# =============================================================================
# >> Tell-Function
# =============================================================================    
def tell(userid, message):
    if not es.getuserid(userid):
       return
    
    usermsg.saytext2(userid, 0, '\x01'+format(message))

# =============================================================================
# >> Message-Function
# =============================================================================
def msg(message):
    usermsg.saytext2('#all', 0, '\x01'+format(message))

# =============================================================================
# >> Public Variable
# =============================================================================    
es.set('esc_version', version)
es.makepublic('esc_version')