import es

import esc
import playerlib
import popuplib
import os
import cPickle as pickle
from velohook import chat
import vecmath
import effectlib
import gamethread
import time

client = {}
location = {}

times = 0

current_map = es.ServerVar('eventscripts_currentmap')

timer_plugin = True


def load_client_pref():
    global client
    dictPath = os.path.join(es.getAddonPath("queue_timer"), "/database/clientpref_trikz.db")
    if os.path.isfile(dictPath):
        fileStream = open(dictPath, 'rb')
        client = pickle.load(fileStream)
        fileStream.close()


def save_client_pref():
    dictPath = os.path.join(es.getAddonPath("queue_timer"), "database/clientpref_trikz.db")
    fileStream = open(dictPath, 'wb')
    pickle.dump(client, fileStream)
    fileStream.close()


class QueueExtendTrikz(object):
    def __init__(self):
        self.primary_color = "#245,0,61"
        self.secondary_color = "None"

    def Validate(self, userid, message=1):
        steamid = es.getplayersteamid(userid)
        if steamid not in client:
            client[steamid] = {'auto_switch': "On",
                               'auto_flash': "On",
                               'auto_stuck': "On",
                               'stop_speed': "Off",
                               'save_angles': "Off",
                               'view_angles': False,
                               'auto_jump': "On",
                               'check_stuck': 1,
                               'strafe_sync': 'Off',
                               'esp': "Off",
                               'partner': 'Nobody',
                               'player_state': "Block",
                               'time_elapsed': 0,
                               'snapshot_1': (0, 0, 0),
                               'snapshot_2': (0, 0, 0),
                               'pratice_mode': 0,
                               'time': 0,
                               'ignored': [],
                               'tp_accept': 0,
                               'tp_location': None,
                               'tp_userid': None,
                               'x': 1,
                               'x_mh': 1,
                               'bot_style': "Normal",
                               'bot_firstboost': "ML",
                               'bot_jump': 'Yes',
                               'bot_crouch': "No",
                               'best_x': 1,
                               'last_k': 0,
                               'spam': 0,
                               'view_angle': (0, 0, 0),
                               'view_angle_2': (0, 0, 0),
                               'ignore_list': [],
                               'save_speed': (0, 0, 0),
                               'save_speed_stack': 0,
                               'save_speed_2': 0,
                               'save_speed_stack_2': 0}
            if message == 1:
                esc.tell(userid,
                         '#0,167,255[ #0,137,255Trikz #0,167,255] #snowCorrupt data has been found and has been restored!')
        else:
            if message == 1:
                esc.tell(userid,
                         '#0,167,255[ #0,137,255Trikz #0,167,255] #snowThis is a validation check. If you get this message you are all set.')

    def Intro_menu(self, userid):
        info = popuplib.create('intro_menu')
        info.addline('Queue Plugin')
        info.addline('=> Running [Queue] 0.9.8v')
        info.addline(' ')
        info.addline('1. Commands')
        info.addline('2. Menus')
        info.addline('3. Credits')
        info.addline('4. Modules')
        info.addline(' ')
        info.addline('0 Exit')
        info.enablekeys = "08"
        info.unsend(userid)
        info.send(userid)
        info.delete()
        info.menuselect = None


QueueAPI = QueueExtendTrikz()


def load():
    es.set('eventscripts_noisy', 1)
    global client
    gamethread.cancelDelayed("antispam")
    antispam()
    load_client_pref()

    chat.hook("window.chat", None)

    """ Trikz menu """
    chat.registerHiddenCommand("!t", trikz_menu, True, True)
    chat.registerHiddenCommand("/t", trikz_menu, True, True)
    chat.registerHiddenCommand("t", trikz_menu, True, True)
    chat.registerHiddenCommand("!trikz", trikz_menu, True, True)

    """ TP menu """
    # TODO: startswith
    chat.registerPublicCommand("!tp ", tp_menu, True, True, startswith=True)
    chat.registerPublicCommand("!tp", tp_menu, True, True, startswith=False)
    chat.registerPublicCommand("!tpto", tp_menu, True, True, startswith=True)
    chat.registerHiddenCommand("/tp ", tp_menu, True, True, startswith=True)
    chat.registerHiddenCommand("/tp", tp_menu, True, True, startswith=False)
    chat.registerHiddenCommand("/tptp", tp_menu, True, True, startswith=True)

    """ TP accept """
    chat.registerPublicCommand("!y", tp_accept, False, True, startswith=True)
    chat.registerHiddenCommand("/y", tp_accept, False, True, startswith=True)

    """ Commands menu"""
    chat.registerPublicCommand("!commands", commands, True, True)
    chat.registerHiddenCommand("/commands", commands, True, True)

    """ Get weapon_glock command"""
    chat.registerPublicCommand("!glock", get_glock, False, True)
    chat.registerHiddenCommand("/glock", get_glock, False, True)

    """ Get weapon_usp command"""
    chat.registerPublicCommand("!usp", get_usp, False, True)
    chat.registerHiddenCommand("/usp", get_usp, False, True)

    """ Toggle block command """
    chat.registerPublicCommand("!b", toggle, True, True)
    chat.registerPublicCommand("!block", toggle, True, True)
    chat.registerHiddenCommand("/b", toggle, True, True)
    chat.registerHiddenCommand("/block", toggle, True, True)

    """ Set player spectate command """
    # TODO: Choose target (startswith method)
    chat.registerPublicCommand("!spec", change_spec, True, True)
    chat.registerPublicCommand("!spectate", change_spec, True, True)
    chat.registerHiddenCommand("/spec", change_spec, True, True)
    chat.registerHiddenCommand("/spectate", change_spec, True, True)

    # TODO: Choose target (startswith method)
    chat.registerPublicCommand("!cp", cp_menu, True, True)
    chat.registerPublicCommand("!checkpoint", cp_menu, True, True)
    chat.registerHiddenCommand("/cp", cp_menu, True, True)
    chat.registerHiddenCommand("/checkpoint", cp_menu, True, True)


def unload():
    es.set('eventscripts_noisy', 0)
    global client
    save_client_pref()
    client = {}


def player_activate(ev):
    userid = ev["userid"]
    QueueAPI.Validate(userid, 0)
    save_client_pref()

def iequal(a, b):
    try:
        return a.upper() == b.upper()
    except AttributeError:
        return a == b


def get_usp(userid, text, steamid, name):
    player = playerlib.getPlayer(userid)
    if not player.isdead:
        if not client[steamid]["spam"] > 3:
            esc.tell(userid, '#0,167,255[ #0,137,255Trikz #0,167,255] #snowYou have received an #yellowUSP.')
            es.server.queuecmd('es_xgive %s weapon_usp' % userid)
            client[steamid]["spam"] += 1
        else:
            esc.tell(userid, '#0,167,255[ #0,137,255Trikz #0,167,255] #snowStop spamming the command #yellow%s' % text)


def get_glock(userid, text, steamid, name):
    player = playerlib.getPlayer(userid)
    if not player.isdead:
        if not client[steamid]["spam"] > 3:
            esc.tell(userid, '#0,167,255[ #0,137,255Trikz #0,167,255] #snowYou have received an #yellowGlock.')
            es.server.queuecmd('es_xgive %s weapon_glock' % userid)
            client[steamid]["spam"] += 1
        else:
            esc.tell(userid, '#0,167,255[ #0,137,255Trikz #0,167,255] #snowStop spamming the command #yellow%s' % text)


def change_spec(userid):
    es.server.queuecmd('es_xchangeteam %i 1' % int(userid))
    esc.tell(userid, "#0,167,255[ #0,137,255Trikz #0,167,255] #snowYou've been sent to #yellowspectator!")


def antispam():
    for userid in es.getUseridList():
        steamid = es.getplayersteamid(userid)
        if steamid not in client:
            QueueAPI.Validate(userid, 0)
        client[steamid]["spam"] = 0
    gamethread.delayedname(30, "spam", antispam)


def player_spawn(ev):
    userid = ev['userid']
    player = playerlib.getPlayer(userid)
    steamid = es.getplayersteamid(userid)
    interp = es.getclientvar(userid, 'cl_interp')

    if not player.isdead:
        es.server.queuecmd('es_xgive %s weapon_flashbang' % userid)
        es.server.queuecmd('es_xgive %s weapon_flashbang' % userid)
        gamethread.cancelDelayed("auto_stuck_%s" % userid)
        auto_stuck(userid)
        QueueAPI.Validate(userid, 0)
        if not interp == "0":
            esc.tell(userid,
                     "#0,167,255[ #0,137,255Trikz #0,167,255] #snowYou lerp is not optimal, do #yellow'cl_interp 0' #snowin console")


def auto_switch(userid):
    es.server.queuecmd('es_sexec %s use weapon_knife' % userid)
    es.server.queuecmd('es_sexec %s use weapon_flashbang' % userid)


def weapon_fire(ev):
    userid = ev["userid"]
    steamid = es.getplayersteamid(userid)
    player = playerlib.getPlayer(userid)
    if ev['weapon'] == 'flashbang':
        if client[steamid]["auto_flash"] == "On":
            if player.getFB() < 10:
                player.setFB(30)

        if client[steamid]['auto_switch'] == "On":
            gamethread.delayed(0.10, auto_switch, userid)


def trikz_menu(userid, text=None, steamid=None, name=None):
    QueueAPI.Validate(userid, 0)
    steamid = es.getplayersteamid(userid)
    info = popuplib.create('trikz_menu')
    info.addline('Trikz menu')
    info.addline(' ')
    if client[steamid]["auto_switch"] == "On":
        info.addline('->1. Auto Switch: On')
    else:
        info.addline('->1. Auto Switch: Off')

    if client[steamid]["auto_jump"] == "On":
        info.addline('->2. Auto Jump: On')
    else:
        info.addline('->2. Auto Jump: Off')
    if client[steamid]["auto_stuck"] == "On":
        info.addline('->3. Anti Stuck: On')
    else:
        info.addline('->3. Anti Stuck: Off')

    if client[steamid]["player_state"] == "Ghost":

        info.addline('->4. Blocking: Off')
    else:
        info.addline('->4. Blocking: On')
    info.addline(' ')
    info.addline('->5. Checkpoints')
    info.addline('->6. Delay')
    info.addline(' ')
    info.addline('0. Exit')
    info.enablekeys = "12345680"
    info.unsend(userid)
    info.send(userid)
    info.delete()
    info.menuselect = trikz_menu_select


def commands(userid):
    steamid = es.getplayersteamid(userid)
    QueueAPI.Validate(userid, 0)
    player = playerlib.getPlayer(userid)
    info = popuplib.create('commands')
    info.addline('<!commands list>  ')
    info.addline('Timer Commands:')
    info.addline(' ')
    info.addline('!r')
    info.addline('!b <number>')
    info.addline('!end')
    info.addline('!bend <number>')
    info.addline('!wr ')
    info.addline('!bwr ')
    info.addline('!rank <name|steamid>')
    info.addline('!crank <name|steamid> ')
    info.addline('!top')
    info.addline('!ctop <country name>')
    info.addline('!partner | !p')
    info.addline('!unpartner')
    info.addline('!tags')
    info.addline('!points <map name>')
    info.addline('!mode | !style | (!sw,!n,!hsw, !w)')
    info.addline('!hud | !settings')
    info.addline('!stop | Stops your timer')
    info.addline(' ')
    info.addline('Server Commands:')
    info.addline('!retry, !tp, !cp, !trikz, !lj, !ip')
    info.addline('!spec | !spectate')
    info.addline(' ')
    info.addline('0. Exit')
    info.enablekeys = "123456780"
    info.unsend(userid)
    info.send(userid)
    info.delete()
    info.menuselect = None


def trikz_menu_select(userid, choice, popupid):
    steamid = es.getplayersteamid(userid)
    player = playerlib.getPlayer(userid)
    timer = es.import_addon("queue_timer/plugins/timer")
    """
    if int(choice) == 1:
        if player.getFB() in (0, 1):
            client[steamid]['auto_flash'] = "On"
            esc.tell(userid, '#0,167,255[ #0,137,255Trikz #0,167,255] #snowYou got a #yellowrefill #245,61,0flash')
        trikz_menu(userid)

    if int(choice) == 1:
        if not client[steamid]['auto_flash'] == "On":
            client[steamid]['auto_flash'] = "On"
            auto_switch(userid)
            esc.tell(userid, '#0,167,255[ #0,137,255Trikz #0,167,255] #245,61,0AutoFlash#snow is now #yellowON')
        else:
            client[steamid]['auto_flash'] = "Off"
            auto_switch(userid)
            esc.tell(userid, '#0,167,255[ #0,137,255Trikz #0,167,255] #245,61,0AutoFlash#snow is now #yellowOFF')
        trikz_menu(userid)
    """
    if int(choice) == 1:
        if not client[steamid]['auto_switch'] == "On":
            client[steamid]['auto_switch'] = "On"
            esc.tell(userid, '#0,167,255[ #0,137,255Trikz #0,167,255] #245,61,0AutoSwitch#snow is now #yellowON')
        else:
            client[steamid]['auto_switch'] = "Off"
            esc.tell(userid, '#0,167,255[ #0,137,255Trikz #0,167,255] #245,61,0AutoSwitch#snow is now #yellowOFF')
        trikz_menu(userid)

    if int(choice) == 2:
        if not client[steamid]['auto_jump'] == "On":
            client[steamid]['auto_jump'] = "On"
            es.cexec(userid, 'sm_%s' % "autojump")

        else:
            client[steamid]['auto_jump'] = "Off"
            es.cexec(userid, 'sm_%s' % "autojump")
        trikz_menu(userid)

    if int(choice) == 3:

        if client[steamid]['auto_stuck'] == "Off":
            esc.tell(userid,
                     '#0,167,255[ #0,137,255Trikz #0,167,255] #245,61,0Anti-Stuck #snowis now #yellowON')
            client[steamid]['auto_stuck'] = "On"
            gamethread.cancelDelayed("auto_stuck_%s" % userid)
            auto_stuck(userid)
        else:
            esc.tell(userid,
                     '#0,167,255[ #0,137,255Trikz #0,167,255] #245,61,0Anti-Stuck #snowis now #yellowOFF #255,0,0(NOT Recommended)')
            client[steamid]['auto_stuck'] = "Off"
            gamethread.cancelDelayed("auto_stuck_%s" % userid)
        trikz_menu(userid)

    if int(choice) == 4:
        toggle(userid)
        trikz_menu(userid)

    if int(choice) == 5:
        cp_menu(userid)

    if int(choice) == 6:
        es.cexec(userid, 'sm_delay')


def development(userid):
    steamid = es.getplayersteamid(userid)
    QueueAPI.Validate(userid, 0)
    timer = es.import_addon("queue_timer/plugins/timer")
    player = playerlib.getPlayer(userid)
    timer.player[steamid]["disabled"] = 1
    info = popuplib.create('development')
    info.addline('Development features')
    info.addline('---------------------')
    if client[steamid]["esp"] == "Off":
        info.addline('->1. ESP [Off]')
    else:
        info.addline('->1. ESP [On]')
    if client[steamid]["strafe_sync"] == "Off":
        info.addline('->2. Strafe Re-Sync [Off]')
    else:
        info.addline('->2. Strafe Re-Sync [On]')
    info.addline('----------------------')
    info.addline('0. Exit')
    info.enablekeys = "123456780"
    info.unsend(userid)
    info.send(userid)
    info.delete()
    info.menuselect = development_select


def development_select(userid, choice, popupid):
    steamid = es.getplayersteamid(userid)
    player = playerlib.getPlayer(userid)
    timer = es.import_addon("queue_timer/plugins/timer")
    if int(choice) == 1:
        if client[steamid]["esp"] == "Off":
            esc.tell(userid,
                     '#245,0,61[Development] #245,61,0ESP #snowis now #yellowOn')
            client[steamid]["esp"] = "On"
            gamethread.cancelDelayed("esp_%s" % userid)
            esp(userid)
        else:
            esc.tell(userid,
                     '#245,0,61[Development] #245,61,0ESP #snowis now #yellowOff')
            client[steamid]["esp"] = "Off"
            gamethread.cancelDelayed("esp_%s" % userid)

    if int(choice) == 2:

        if client[steamid]['strafe_sync'] == "Off":
            if timer.CheckPartner(userid):
                timer_id = timer.player[steamid]["timer_id"]
                state = timer.timer[timer_id]["state"]
                if state == 2:
                    return
                else:
                    esc.tell(userid,
                             '#0,167,255[ #0,137,255Trikz #0,167,255] #245,61,0Perfect Strafe synchronization #snowis now #yellowON')
                    client[steamid]['strafe_sync'] = "On"
            else:
                esc.tell(userid,
                         '#0,167,255[ #0,137,255Trikz #0,167,255] #245,61,0Perfect Strafe synchronization #snowis now #yellowON')
                client[steamid]['strafe_sync'] = "On"

        else:
            esc.tell(userid,
                     '#0,167,255[ #0,137,255Trikz #0,167,255] #245,61,0Perfect Strafe synchronization #snowis now #yellowOFF')
            client[steamid]['strafe_sync'] = "Off"
    if int(choice) in (1, 2, 3, 4, 5, 6):
        development(userid)


def esp(userid):
    if es.exists("userid", userid):
        steamid = es.getplayersteamid(userid)
        player = playerlib.getPlayer(userid)
        if not player.isdead:
            if client[steamid]["auto_flash"] == "On":
                if player.getFB() < 2:
                    es.server.queuecmd('es_xgive %s weapon_flashbang' % userid)
                    # es.server.queuecmd('es_xgive %s weapon_flashbang' % userid)
                    # player.setFB(30)

        if client[steamid]['auto_stuck'] == "On":
            alive = es.getlivingplayercount()
            if alive > 1:
                location = es.getplayerlocation(userid)
                PosBoxUp = (location[0] + 64, location[1] + 64, location[2] + 64)
                PosBoxDown = (location[0] - 64, location[1] - 64, location[2])

                player = playerlib.getPlayer(userid)
                steamid = es.getplayersteamid(userid)

                target = playerlib.getPlayer(player.getClosestPlayer(team=None)[1])
                player_target = playerlib.getPlayer(target)

                target_pos = es.getplayerlocation(player.getClosestPlayer(team=None)[1])  # Tuple
                player_pos = es.getplayerlocation(userid)

                target_x = float(target_pos[0])
                target_y = float(target_pos[1])
                target_z = float(target_pos[2])

                player_x = float(player_pos[0])
                player_y = float(player_pos[1])
                player_z = float(player_pos[2])

                if not player.isdead:
                    if abs(-target_z - (-player_z)) < 61 and abs(-target_z - (-player_z)) >= 0 and abs(
                                    -target_x - (-player_x)) < 128 and abs(-target_y - (-player_y)) < 128:
                        drawbox(userid, userid, PosBoxDown, "Noob", PosBoxUp)
                    else:

                        drawbox(userid, userid, PosBoxDown, "extra", PosBoxUp)

    gamethread.delayedname(0.01, 'esp_%s' % userid, esp, args=(userid))


def drawbox(userid, loop_number, start_point, type, end_point=None):
    if not end_point:
        effectlib.drawBox(start_point, es.getplayerlocation(userid), 'materials/sprites/laser.vmt',
                          'materials/sprites/laser.vmt', 2, '3', '3', 255, 255, 255, '255', '10', '0', '0', '0', '0')
    else:
        if type == "end":

            effectlib.drawBox(start_point, end_point, 'materials/sprites/laser.vmt', 'materials/sprites/laser.vmt', 2,
                              '3', '3', 255, 0, 0, '255', '10', '0', '0', '0', '0')
        elif type == "extra":
            effectlib.drawBox(start_point, end_point, 'materials/sprites/laser.vmt', 'materials/sprites/laser.vmt', 0.1,
                              '3', '3', 255, 0, 0, '255', '10', '0', '0', '0', '0')
        else:
            effectlib.drawBox(start_point, end_point, 'materials/sprites/laser.vmt', 'materials/sprites/laser.vmt', 0.1,
                              '3', '3', 0, 255, 0, '255', '10', '0', '0', '0', '0')


def sm2es_keyPress(ev):
    userid = ev["userid"]
    timer = es.import_addon("queue_timer/plugins/timer")
    if es.exists("userid", userid):

        if ev['status'] == '0':
            return

        ply = playerlib.getPlayer(userid)

        if ply.isdead:
            return

        velocity_x = float(es.getplayerprop(userid, 'CBasePlayer.localdata.m_vecVelocity[0]'))
        velocity_y = float(es.getplayerprop(userid, 'CBasePlayer.localdata.m_vecVelocity[1]'))
        steamid = es.getplayersteamid(userid)

        if ev["command"] == 'IN_MOVELEFT':
            if not ply.onGround() and client[steamid]["strafe_sync"] == "On":
                if not client[steamid]["view_angle"] == ply.viewVector():
                    if not client[steamid]["last_k"] == 0:
                        if timer.CheckPartner(userid):
                            timer_id = timer.player[steamid]["timer_id"]
                            state = timer.timer[timer_id]["state"]
                            if state == 2:
                                return
                            else:
                                myNewVector = es.createvectorstring((velocity_x ** 0.1) * 18, (velocity_y ** 0.1) * 18)
                                myNewVector2 = es.createvectorstring((velocity_x ** 0.1) * 18, (velocity_y ** 0.1) * 18)
                                es.setplayerprop(userid, "CBasePlayer.localdata.m_vecBaseVelocity", myNewVector)
                                es.setplayerprop(userid, "CBasePlayer.localdata.m_vecBaseVelocity", myNewVector2)
                                client[steamid]["view_angle"] = ply.viewVector()
                                client[steamid]["last_k"] = 0
                        else:
                            myNewVector = es.createvectorstring((velocity_x ** 0.1) * 18, (velocity_y ** 0.1) * 18)
                            myNewVector2 = es.createvectorstring((velocity_x ** 0.1) * 18, (velocity_y ** 0.1) * 18)
                            es.setplayerprop(userid, "CBasePlayer.localdata.m_vecBaseVelocity", myNewVector)
                            es.setplayerprop(userid, "CBasePlayer.localdata.m_vecBaseVelocity", myNewVector2)
                            client[steamid]["view_angle"] = ply.viewVector()
                            client[steamid]["last_k"] = 0
        if ev['command'] == 'IN_MOVERIGHT':
            if not ply.onGround() and client[steamid]["strafe_sync"] == "On":
                if not client[steamid]["view_angle"] == ply.viewVector():
                    if not client[steamid]["last_k"] == 1:
                        if timer.CheckPartner(userid):
                            timer_id = timer.player[steamid]["timer_id"]
                            state = timer.timer[timer_id]["state"]
                            if state == 2:
                                return
                            else:
                                myNewVector = es.createvectorstring((velocity_x ** 0.1) * 18, (velocity_y ** 0.1) * 18)
                                myNewVector2 = es.createvectorstring((velocity_x ** 0.1) * 18, (velocity_y ** 0.1) * 18)
                                es.setplayerprop(userid, "CBasePlayer.localdata.m_vecBaseVelocity", myNewVector)
                                es.setplayerprop(userid, "CBasePlayer.localdata.m_vecBaseVelocity", myNewVector2)
                                client[steamid]["view_angle"] = ply.viewVector()
                                client[steamid]["last_k"] = 0
                        else:
                            myNewVector = es.createvectorstring((velocity_x ** 0.1) * 18, (velocity_y ** 0.1) * 18)
                            myNewVector2 = es.createvectorstring((velocity_x ** 0.1) * 18, (velocity_y ** 0.1) * 18)
                            es.setplayerprop(userid, "CBasePlayer.localdata.m_vecBaseVelocity", myNewVector)
                            es.setplayerprop(userid, "CBasePlayer.localdata.m_vecBaseVelocity", myNewVector2)
                            client[steamid]["view_angle"] = ply.viewVector()
                            client[steamid]["last_k"] = 0


def cp_menu(userid):
    steamid = es.getplayersteamid(userid)
    timer = es.import_addon("queue_timer/plugins/timer")
    QueueAPI.Validate(userid, 0)
    info = popuplib.create('checkpoint_menu')
    info.addline('Checkpoints')
    info.addline(' ')
    info.addline('->1. Save CP 1')
    info.addline('->2. Teleport to CP 1 ')
    info.addline(' ')
    info.addline('->3. Save CP 2')
    info.addline('->4. Teleport to CP 2')
    info.addline(' ')
    if client[steamid]["stop_speed"] == "On":
        info.addline('->5. Save speed: On')
    else:
        info.addline('->5. Save speed: Off')
    if client[steamid]["save_angles"] == "On":
        info.addline('->6. Save angles: On')
    else:
        info.addline('->6. Save angles: Off')
    info.addline(' ')
    if timer.CheckPartner(userid):
        info.addline('Disabled during timer!')
        info.addline(' ')
    info.addline('->8. Back')
    info.addline('0 Exit')
    info.enablekeys = "12345608"
    info.unsend(userid)
    info.send(userid)
    info.delete()
    info.menuselect = cp_menu_select


def set_boost(userid, cp):
    steamid = es.getplayersteamid(userid)
    if cp == 0:
        client[steamid]["save_speed_stack"] += 1
        myNewVector2 = es.createvectorstring(client[steamid]['save_speed'][0], client[steamid]['save_speed'][1],
                                             client[steamid]['save_speed'][2])
        # es.setplayerprop(userid, "CBasePlayer.localdata.m_vecBaseVelocity", myNewVector)
        es.setplayerprop(userid, "CBasePlayer.localdata.m_vecBaseVelocity", myNewVector2)
        if client[steamid]["save_speed_stack"] > 1:
            esc.tell(userid,
                     "#0,167,255[ #0,137,255Trikz #0,167,255] #245,0,61Speed has now been stacked (multiplier X%s" %
                     client[steamid]["save_speed_stack"])
        client[steamid]["save_speed_stack"] -= 1
    else:
        client[steamid]["save_speed_stack_2"] += 1
        myNewVector2 = es.createvectorstring(client[steamid]['save_speed_2'][0], client[steamid]['save_speed_2'][1],
                                             client[steamid]['save_speed_2'][2])
        # es.setplayerprop(userid, "CBasePlayer.localdata.m_vecBaseVelocity", myNewVector)
        es.setplayerprop(userid, "CBasePlayer.localdata.m_vecBaseVelocity", myNewVector2)
        if client[steamid]["save_speed_stack_2"] > 1:
            esc.tell(userid,
                     "#0,167,255[ #0,137,255Trikz #0,167,255] #245,0,61Speed has now been stacked (multiplier X%s" %
                     client[steamid]["save_speed_stack"])
        client[steamid]["save_speed_stack_2"] -= 1


def cp_menu_select(userid, choice, popupid):
    steamid = es.getplayersteamid(userid)
    velocity_x = float(es.getplayerprop(userid, 'CBasePlayer.localdata.m_vecVelocity[0]'))
    velocity_y = float(es.getplayerprop(userid, 'CBasePlayer.localdata.m_vecVelocity[1]'))
    velocity_z = float(es.getplayerprop(userid, 'CBasePlayer.localdata.m_vecVelocity[2]'))
    timer = es.import_addon("queue_timer/plugins/timer")
    if timer.CheckPartner(userid):
        timer_id = timer.player[steamid]["timer_id"]
        state = timer.timer[timer_id]["state"]

    if int(choice) == 1:
        if timer.CheckPartner(userid):
            cp_menu(userid)
        else:
            player = playerlib.getPlayer(userid)
            client[steamid]["view_angles"] = player.getViewAngle()
            view_angles = client[steamid]["view_angles"]
            client[steamid]['snapshot_1'] = es.getplayerlocation(userid)
            client[steamid]['save_speed'] = (velocity_x, velocity_y, velocity_z)
            esc.tell(userid,
                     '#0,167,255[ #0,137,255Trikz #0,167,255] #snowYou have saved your #yellow1st #245,61,0checkpoint')
            cp_menu(userid)

    if int(choice) == 2:
        if timer.CheckPartner(userid):
            cp_menu(userid)
        else:
            if client[steamid]['snapshot_1'] != (0, 0, 0):
                current_location = es.getplayerlocation(userid)
                location = client[steamid]['snapshot_1']
                distance = vecmath.distance(current_location, location)
                player = playerlib.getPlayer(userid)
                view_angles = client[steamid]["view_angles"]
                timer.TimerSolo_Stop(userid)
                client[steamid]["time"] = time.time()
                player.setColor(255, 255, 255, 255)
                player.noblock(0)
                if client[steamid]["stop_speed"] == "On":
                    es.server.queuecmd('es_setpos %s %s %s %s' % (userid, location[0], location[1], location[2]))

                    velocity_x = float(es.getplayerprop(userid, 'CBasePlayer.localdata.m_vecVelocity[0]'))
                    velocity_y = float(es.getplayerprop(userid, 'CBasePlayer.localdata.m_vecVelocity[1]'))
                    velocity_z = float(es.getplayerprop(userid, 'CBasePlayer.localdata.m_vecVelocity[2]'))
                    myNewVector2 = es.createvectorstring(-velocity_x, -velocity_y, -velocity_z)

                    es.setplayerprop(userid, "CBasePlayer.localdata.m_vecBaseVelocity", myNewVector2)

                    gamethread.delayed(0.025, set_boost, args=(userid, 0))


                else:
                    es.server.queuecmd('es_setpos %s %s %s %s' % (userid, location[0], location[1], location[2]))
                    velocity_x = float(es.getplayerprop(userid, 'CBasePlayer.localdata.m_vecVelocity[0]'))
                    velocity_y = float(es.getplayerprop(userid, 'CBasePlayer.localdata.m_vecVelocity[1]'))
                    velocity_z = float(es.getplayerprop(userid, 'CBasePlayer.localdata.m_vecVelocity[2]'))
                    myNewVector2 = es.createvectorstring(-velocity_x, -velocity_y, -velocity_z)
                    es.setplayerprop(userid, "CBasePlayer.localdata.m_vecBaseVelocity", myNewVector2)

                if client[steamid]["save_angles"] == "On":
                    es.server.queuecmd('es_xsetang %s %s %s %s' % (
                    userid, str(view_angles[0]), str(view_angles[1]), str(view_angles[2])))

            else:
                esc.tell(userid, '#0,167,255[ #0,137,255Trikz #0,167,255] #245,0,61You have not set your 1st checkpoint.')
            cp_menu(userid)

    if int(choice) == 3:
        if timer.CheckPartner(userid):
            cp_menu(userid)
        else:
            player = playerlib.getPlayer(userid)
            client[steamid]["view_angles_2"] = player.getViewAngle()
            client[steamid]['snapshot_2'] = es.getplayerlocation(userid)
            client[steamid]['save_speed_2'] = (velocity_x, velocity_y, velocity_z)
            esc.tell(userid,
                     '#0,167,255[ #0,137,255Trikz #0,167,255] #snowYou have saved your #yellow2nd #245,61,0checkpoint')
            cp_menu(userid)

    if int(choice) == 4:
        if timer.CheckPartner(userid):
            cp_menu(userid)
        else:
            if client[steamid]['snapshot_2'] != (0, 0, 0):
                current_location = es.getplayerlocation(userid)
                location = client[steamid]['snapshot_2']
                distance = vecmath.distance(current_location, location)
                player = playerlib.getPlayer(userid)
                view_angles = client[steamid]["view_angles_2"]
                client[steamid]["time"] = time.time()
                timer.TimerSolo_Stop(userid)
                player.setColor(255, 255, 255, 255)
                player.noblock(0)
                if client[steamid]["stop_speed"] == "On":
                    es.server.queuecmd('es_setpos %s %s %s %s' % (userid, location[0], location[1], location[2]))

                    velocity_x = float(es.getplayerprop(userid, 'CBasePlayer.localdata.m_vecVelocity[0]'))
                    velocity_y = float(es.getplayerprop(userid, 'CBasePlayer.localdata.m_vecVelocity[1]'))
                    velocity_z = float(es.getplayerprop(userid, 'CBasePlayer.localdata.m_vecVelocity[2]'))
                    myNewVector2 = es.createvectorstring(-velocity_x, -velocity_y, -velocity_z)

                    es.setplayerprop(userid, "CBasePlayer.localdata.m_vecBaseVelocity", myNewVector2)

                    gamethread.delayed(0.025, set_boost, args=(userid, 1))
                else:

                    es.server.queuecmd('es_setpos %s %s %s %s' % (userid, location[0], location[1], location[2]))

                    velocity_x = float(es.getplayerprop(userid, 'CBasePlayer.localdata.m_vecVelocity[0]'))
                    velocity_y = float(es.getplayerprop(userid, 'CBasePlayer.localdata.m_vecVelocity[1]'))
                    velocity_z = float(es.getplayerprop(userid, 'CBasePlayer.localdata.m_vecVelocity[2]'))
                    myNewVector2 = es.createvectorstring(-velocity_x, -velocity_y, -velocity_z)
                    es.setplayerprop(userid, "CBasePlayer.localdata.m_vecBaseVelocity", myNewVector2)

                if client[steamid]["save_angles"] == "On":
                    es.server.insertcmd('es_xsetang %s %s %s %s' % (
                    userid, str(view_angles[0]), str(view_angles[1]), str(view_angles[2])))

            else:
                esc.tell(userid, '#0,167,255[ #0,137,255Trikz #0,167,255] #245,0,61You have not set your 2nd checkpoint.')
            cp_menu(userid)

    if int(choice) == 5:
        if client[steamid]['stop_speed'] == "Off":
            esc.tell(userid,
                     '#0,167,255[ #0,137,255Trikz #0,167,255] #snowYour speed will now be restored when teleporting!')
            client[steamid]['stop_speed'] = "On"
            cp_menu(userid)
        else:
            esc.tell(userid, '#0,167,255[ #0,137,255Trikz #0,167,255] #snowYou will not save speed anymore!')
            client[steamid]['stop_speed'] = "Off"
            cp_menu(userid)

    if int(choice) == 6:
        if client[steamid]['save_angles'] == "Off":
            esc.tell(userid, '#0,167,255[ #0,137,255Trikz #0,167,255] #snowYou will now save ur angles!')
            client[steamid]['save_angles'] = "On"
            cp_menu(userid)
        else:
            esc.tell(userid, '#0,167,255[ #0,137,255Trikz #0,167,255] #snowYou angles wont be saved!')
            client[steamid]['save_angles'] = "Off"
            cp_menu(userid)

    if int(choice) == 8:
        trikz_menu(userid)


def toggle(userid):
    steamid = es.getplayersteamid(userid)
    player = playerlib.getPlayer(userid)
    if not player.getNoBlock():
        es.setplayerprop(userid,
                         "CCSPlayer.baseclass.baseclass.baseclass.baseclass.baseclass.baseclass.m_CollisionGroup", 2)

        player.setColor(255, 255, 255, 100)
        esc.tell(userid, '#0,167,255[ #0,137,255Trikz #0,167,255] #245,61,0Blocking#snow is now #yellowOFF')
        client[steamid]["player_state"] = "Ghost"
    else:
        esc.tell(userid, '#0,167,255[ #0,137,255Trikz #0,167,255] #245,61,0Blocking#snow is now #yellowON')
        es.setplayerprop(userid,
                         "CCSPlayer.baseclass.baseclass.baseclass.baseclass.baseclass.baseclass.m_CollisionGroup", 0)
        player.setColor(255, 255, 255, 255)
        client[steamid]["player_state"] = "Block"


def auto_stuck(userid):
    # Player X-X width = 64.0625 units
    # Player Y-Y width = 64.2360839844
    # Player height = 62.03125 units
    if es.exists("userid", userid):
        if not es.isbot(userid):
            steamid = es.getplayersteamid(userid)
            player = playerlib.getPlayer(userid)
            if not player.isdead:
                if client[steamid]["auto_flash"] == "On":
                    if player.getFB() == 0:
                        es.server.queuecmd('es_give %s weapon_flashbang' % userid)
                        es.server.queuecmd('es_give %s weapon_flashbang' % userid)
                        # player.setFB(100)

            if client[steamid]['auto_stuck'] == "On":
                alive = es.getlivingplayercount()
                if alive > 1 and time.time() - client[steamid]["time"] > 1.5:
                    player = playerlib.getPlayer(userid)
                    steamid = es.getplayersteamid(userid)

                    target = playerlib.getPlayer(player.getClosestPlayer(team=None)[1])

                    player_target = playerlib.getPlayer(target)
                    target_steamid = player_target.steamid

                    target_pos = es.getplayerlocation(player.getClosestPlayer(team=None)[1])  # Tuple
                    player_pos = es.getplayerlocation(userid)

                    target_x = float(target_pos[0])
                    target_y = float(target_pos[1])
                    target_z = float(target_pos[2])

                    player_x = float(player_pos[0])
                    player_y = float(player_pos[1])
                    player_z = float(player_pos[2])

                    if not player.isdead:
                        if not es.isbot(target):
                            if abs(-target_z - (-player_z)) < 61 and abs(-target_z - (-player_z)) >= 0 and abs(
                                            -target_x - (-player_x)) < 32 and abs(-target_y - (
                            -player_y)) < 32 and not player_target.isDucked() and not player.isDucked():
                                player.noblock(1)
                                player_target.noblock(1)
                                player.setColor(255, 255, 255, 100)
                                player_target.setColor(255, 255, 255, 100)
                                es.centertell(userid, 'Anti-Stuck')

                            elif abs(-target_z - (-player_z)) < 45 and abs(-target_z - (-player_z)) >= 0 and abs(
                                            -target_x - (-player_x)) < 32 and abs(-target_y - (
                            -player_y)) < 32 and player_target.isDucked() and not player.isDucked():
                                player.noblock(1)
                                player_target.noblock(1)
                                player.setColor(255, 255, 255, 100)
                                player_target.setColor(255, 255, 255, 100)
                                es.centertell(userid, 'Anti-Stuck')

                            elif abs(-target_z - (-player_z)) < 45 and abs(-target_z - (-player_z)) >= 0 and abs(
                                            -target_x - (-player_x)) < 32 and abs(-target_y - (
                            -player_y)) < 32 and not player_target.isDucked() and player.isDucked():

                                player.noblock(1)
                                player_target.noblock(1)
                                player.setColor(255, 255, 255, 100)
                                player_target.setColor(255, 255, 255, 100)
                                es.centertell(userid, 'Anti-Stuck')

                            elif abs(-target_z - (-player_z)) < 45 and abs(-target_z - (-player_z)) >= 0 and abs(
                                            -target_x - (-player_x)) < 32 and abs(-target_y - (
                            -player_y)) < 32 and player_target.isDucked() and player.isDucked():
                                player.noblock(1)
                                player_target.noblock(1)
                                player.setColor(255, 255, 255, 100)
                                player_target.setColor(255, 255, 255, 100)
                                es.centertell(userid, 'Anti-Stuck')



                            elif abs(-target_z - (-player_z)) < 61 and abs(-target_z - (-player_z)) >= 0 and abs(
                                            -target_x - (-player_x)) < 32 and abs(-target_y - (
                            -player_y)) < 32 and not player_target.isDucked() and player.isDucked():
                                if target_z < player_z:
                                    player.noblock(1)
                                    player_target.noblock(1)
                                    player.setColor(255, 255, 255, 100)
                                    player_target.setColor(255, 255, 255, 100)
                                    es.centertell(userid, 'Anti-Stuck 1')

                            elif abs(-target_z - (-player_z)) < 61 and abs(-target_z - (-player_z)) >= 0 and abs(
                                            -target_x - (-player_x)) < 32 and abs(-target_y - (
                            -player_y)) < 32 and player_target.isDucked() and not player.isDucked():
                                if target_z > player_z:
                                    player.noblock(1)
                                    player_target.noblock(1)
                                    player.setColor(255, 255, 255, 100)
                                    player_target.setColor(255, 255, 255, 100)
                                    es.centertell(userid, 'Anti-Stuck 2')

                            else:
                                if client[steamid]["player_state"] == "Block" and client[target_steamid][
                                    "player_state"] == "Block":
                                    player.setColor(255, 255, 255, 255)
                                    player.noblock(0)
                                    player_target.noblock(0)
                                    player_target.setColor(255, 255, 255, 255)



                    else:
                        gamethread.cancelDelayed("auto_stuck_%s" % userid)
                        return

    gamethread.delayedname(0.1, 'auto_stuck_%s' % userid, auto_stuck, args=(userid))


def tp_menu(userid):
    steamid = es.getplayersteamid(userid)
    info = popuplib.easymenu(str(steamid) + 'tpto', None, tp_menu_select)
    info.settitle("Teleport menu\nStops your timer\n\nSelect a player..")
    info.c_beginsep = " "
    info.c_pagesep = " "
    for userid_2 in es.getUseridList():
		if not es.isbot(userid_2):
			if userid == userid_2:
				name = es.getplayername(userid_2)

				info.addoption(str(userid_2), "%s" % name, False)
			else:
				name = es.getplayername(userid_2)
				info.addoption(str(userid_2), "%s" % name)

    info.send(userid)


def tp_menu_select(userid, choice, popupid):
    timer = es.import_addon("queue_timer/plugins/timer")
    steamid = es.getplayersteamid(choice)
    if not timer.CheckPartner(userid):
        # if es.getplayerprop(userid, "CCSPlayer.baseclass.localdata.m_hGroundEntity") != -1:
        client[steamid]["tp_location"] = es.getplayerlocation(choice)
        client[steamid]["tp_userid"] = userid
        client[steamid]["tp_accept"] = 1
        esc.tell(userid,
                 '#0,167,255[ #0,137,255Trikz #0,167,255] #snowYou have sent a teleport request to %s' % es.getplayername(
                     choice))
        esc.tell(choice,
                 '#0,167,255[ #0,137,255Trikz #0,167,255]#tomato %s #snowwants to teleport to you! Type #tomato!yes #snowor #tomatoignore' % (
                     es.getplayername(userid)))
    else:
        esc.tell(userid,
                 '#0,167,255[ #0,137,255Trikz #0,167,255] #snowPlease unpartner first!')


def tp_accept(userid, text, steamid, name):
    if client[steamid]["tp_accept"] == 1:

        if timer_plugin:
            timer = es.import_addon('queue_timer/plugins/timer')
            timer.TimerSolo_Stop(userid)
            timer.TimerPartner_Stop(userid)

        tp_userid = client[steamid]["tp_userid"]
        location = es.getplayerlocation(userid)

        es.server.queuecmd('es_setpos %s %s %s %s' % (tp_userid, location[0], location[1], location[2] + 64))
        esc.tell(tp_userid,
                 '#0,167,255[ #0,137,255Trikz #0,167,255] #snowYou have #245,61,0teleported#snow to #yellow%s' % es.getplayername(
                     userid))
        client[steamid]["tp_accept"] = 0


def getPushAngle(userid, view_angle, horiz, vert, vert_override=False):
    """

    Pushes the player along his or her view vector.

    Call without underscore, i.e.: player.push(horiz, vert, vert_override)

    """

    myVector = view_angle

    horzX = float(horiz) * float(myVector[0])

    horzY = float(horiz) * float(myVector[1])

    if str(vert_override) == '0':

        vertZ = float(myVector[2]) * float(vert)

    else:

        vertZ = vert

    myNewVector = es.createvectorstring(horzX, horzY, vertZ)

    es.setplayerprop(userid, "CBasePlayer.localdata.m_vecBaseVelocity", myNewVector)
