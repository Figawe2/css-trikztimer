import es
import cPickle as pickle
from playerlib import getPlayer
from playerlib import _eyeangle as eyeangle
from gamethread import delayedname as thread_start
from gamethread import delayed as thread_set
from gamethread import cancelDelayed as thread_stop
from configobj import ConfigObj
from esc import msg
from vecmath import distance
import cmdlib
import os

current_map = es.ServerVar('eventscripts_currentmap')

styles = ConfigObj(es.getAddonPath( "trikztimer" ) + "/plugins/botreplay/styles.ini")
thread_handle = {'tick':0}

angles      = {}
positions   = {}
attacks     = {}
crouchs     = {}
tick        = {}
started     = {}
switches    = {}
weapons     = {}
speed       = {}
player_data = {}

rp_angles      = {}
rp_positions   = {}
rp_attacks     = {}
rp_crouchs     = {}
rp_tick        = {}
rp_started     = {}
rp_switches    = {}
rp_weapons     = {}
rp_speed       = {}
rp_player_data = {}

rp_botid   = {}

data = {}
save_data = {}
dump_data = {}


def logclient(userid):
    if not es.isbot(userid):
        angles[userid]     = {}
        positions[userid]  = {}
        attacks[userid]    = {}
        crouchs[userid]    = {}
        tick[userid]       = {}
        switches[userid]   = {}
        weapons[userid]    = {}
        player_data[userid] = {}
        speed[userid]      = {}
        started[userid]    = 0

def resetclient(userid):
        angles[userid]     = {}
        positions[userid]  = {}
        attacks[userid]    = {}
        crouchs[userid]    = {}
        tick[userid]       = {}
        switches[userid]   = {}
        weapons[userid]    = {}
        player_data[userid] = {}
        speed[userid]      = {}
        started[userid]    = 0



def clean_data(userid):
    if userid in (angles, positions, attacks, crouchs, tick, switches, weapons, player_data, speed):
            resetclient(userid)



def load():

    cmdlib.registerServerCommand('botreplay_startrecord', botreplay_startrecord, 'Start Recording')
    cmdlib.registerServerCommand('botreplay_stoprecord', botreplay_stoprecord, 'Stop Recording')
    cmdlib.registerServerCommand('botreplay_saverecord', botreplay_saverecord, 'Save Record')
    for userid in es.getUseridList():
        if not es.isbot(userid):
            logclient(userid)


    thread_stop("player_recorder")
    record_start()

    thread_stop("record_replay")
    record_replay()
    for style in styles:
        load_bots_smooth(style)

def unload():
    thread_stop("record_replay")

    cmdlib.unregisterServerCommand('botreplay_startrecord')
    cmdlib.unregisterServerCommand('botreplay_stoprecord')
    cmdlib.unregisterServerCommand('botreplay_saverecord')

def player_activate(ev):
    userid = ev["userid"]
    if not es.isbot(userid):
        logclient(userid)


""" Record a player """
def record_start():
        # Notify everyone that u are recording

        for userid in started:
            if es.exists("userid", userid):
               if started[userid]:

                    player = getPlayer(userid)

                    tick = started[userid]

                    # ANGLES
                    angles[userid][tick]    = getPlayerAngle(userid)

                    # POSITIONS
                    positions[userid][tick] = es.getplayerlocation(userid)

                    # DUCK
                    if player.isDucked():crouchs[userid][tick] = 1
                    else: crouchs[userid][tick] = 0

                    started[userid] += 1


               else: clean_data(userid)

        # BOTS
        for bot in rp_started:
            if rp_started[bot]:

                userid = bot
                tick = rp_started[bot]
                botid = rp_botid[userid]
                max_tick = len(rp_angles[userid])
                if tick < max_tick:
                    if tick == 1:
                        es.server.queuecmd('es_sexec %s use %s' % (botid, rp_player_data[userid]["weapon"]))

                    es.server.insertcmd('es_xsetang %s %s %s %s' % (
                    botid, rp_angles[userid][tick][0], rp_angles[userid][tick][1], rp_angles[userid][tick][2]))

                    es.server.insertcmd('es_xsetpos %s %s %s %s' % (
                    botid, rp_positions[userid][tick][0], rp_positions[userid][tick][1], rp_positions[userid][tick][2]))

                    if rp_crouchs[userid][tick]:
                        es.server.queuecmd('es_sexec %s sm_start_crouch' % (botid))
                    else:
                        es.server.queuecmd('es_sexec %s sm_stop_crouch' % (botid))
                    if tick in rp_attacks[userid]:
                        es.server.queuecmd('es_sexec %s sm_start_attack' % (botid))
                    else:
                        es.server.queuecmd('es_sexec %s sm_stop_attack' % (botid))

                    if tick in rp_switches[userid]: es.server.queuecmd(
                        'es_sexec %s use %s' % (botid, rp_switches[userid][tick]))

                else:
                    rp_started[bot] = 1
                rp_started[bot] += 1

        if thread_handle["tick"] > 2000:
            thread_handle["tick"] = 0
        thread_handle["tick"] += 1
        thread_start(0.005, "player_recorder", record_start)


def record_stop(userid):
        started[userid] = 0


def save_record(userid, current_map, type, dict_type, real_dict):
        path = os.path.join(es.getAddonPath("trikztimer") + "/plugins/botreplay/databases/%s_%s_%s.db" % (str(current_map), str(dict_type), str(type)))
        file = open(path, 'wb')
        pickle.dump(real_dict, file)
        file.close()


def record_save(userid, map, style):
    record_stop(userid)

    player_data[userid]["steamid"] = es.getplayersteamid(userid)
    player_data[userid]["name"] = es.getplayername(userid)
    index = 0
    for bot in es.getUseridList():
        if es.isbot(bot):
            if not str(index) in rp_started:
                es.server.queuecmd('es_botsetvalue %s name "Saving data.."' % (bot))
            index += 1

    try:
        thread_set(2, save_record, args=(userid, map, style, "player_data", player_data[userid]))
        thread_set(4, save_record, args=(userid, map, style, "angles", angles[userid]))
        thread_set(6, save_record, args=(userid, map, style, "positions", positions[userid]))
    finally:
        thread_set(8, save_record, args=(userid, map, style, "attacks", attacks[userid]))
        thread_set(10, save_record, args=(userid, map, style, "crouchs", crouchs[userid]))
        thread_set(12, save_record, args=(userid, map, style, "switches", switches[userid]))
        thread_set(14, save_record, args=(userid, map, style, "weapons", weapons[userid]))

    thread_set(15, msg, args=('#200,130,40[Replay Bots] #100,100,100Record saved... Bots are now loading!'))
    thread_set(20, load_bots_smooth, args=(style))


def load_record(current_map, type, dict_type):
    global data
    path = os.path.join(es.getAddonPath("trikztimer") + "/plugins/botreplay/databases/%s_%s_%s.db" % (str(current_map), str(dict_type), str(type)))
    if os.path.isfile(path):
        file = open(path, 'rb')
        data = pickle.load(file)
        file.close()
        rp_started[str(type)] = 0
        return data
    else:
        return False


def sort_load_record(current_map, type, dict_type):
    if dict_type == "angles":
        rp_angles[type] = load_record(current_map, type, dict_type)
    if dict_type == "positions":
        rp_positions[type] = load_record(current_map, type, dict_type)
    if dict_type == "attacks":
        rp_attacks[type] = load_record(current_map, type, dict_type)
    if dict_type == "crouchs":
        rp_crouchs[type] = load_record(current_map, type, dict_type)
    if dict_type == "switches":
        rp_switches[type] = load_record(current_map, type, dict_type)
    if dict_type == "weapons":
        rp_weapons[type] = load_record(current_map, type, dict_type)
    if dict_type == "player_data":
        rp_player_data[type] = load_record(current_map, type, dict_type)


def record_replay():
    pass


def sm2es_keyPress(ev):
    userid = ev["userid"]
    event = ev["command"]
    if ev['status'] == '0': return

    if userid in started:
        if started[userid]:
            tick = len(angles[userid])
        else:
            return
    else: return

    if event == 'IN_ATTACK':
            attacks[userid][tick] = 1

    if event == 'weapon_flashbang':
            switches[userid][tick] = 'weapon_flashbang'

    if event == 'weapon_usp':
            switches[userid][tick] = 'weapon_usp'

    if event == "weapon_knife":
            switches[userid][tick] = 'weapon_knife'

    if event == "weapon_glock":
            switches[userid][tick] = 'weapon_usp'

def es_map_start(ev):
    es.set('bot_zombie', 1)
    es.set('bot_stop', 1)
    es.server.queuecmd('bot_quota %s' % len(styles))
    es.server.queuecmd('bot_join_after_player 0')
    es.server.queuecmd('bot_chatter "off"')
    es.server.queuecmd('bot_join_team "any"')
    thread_stop("player_recorder")
    record_start()
    thread_set(1, load_bots)



def load_bots():

    for style in styles:
        sort_load_record(current_map, style, "player_data")
        sort_load_record(current_map, style, "angles")
        sort_load_record(current_map, style, "positions")
        sort_load_record(current_map, style, "attacks")
        sort_load_record(current_map, style, "crouchs")
        sort_load_record(current_map, style, "speed")
        sort_load_record(current_map, style, "switches")

    index = 0
    for userid in es.getUseridList():
            if es.isbot(userid):
                    if str(index) in rp_started:
                        es.server.queuecmd('es_botsetvalue %s name "Normal - %s' % (userid, rp_player_data["%s" % index]["name"]))
                        rp_botid[str(index)] = userid

                    else:
                        es.server.queuecmd('es_botsetvalue %s name "No record"' % (userid))
                    index += 1


    thread_set(3, load_bots_harsh)

def load_bots_harsh():
    msg('#200,130,40[Replay Bots] #100,100,100You might experience lag for a sec!')
    for bot in rp_started:
        rp_started[bot] = 1


def load_bots_smooth(style):
    s = int(style)
    thread_set(2+s, sort_load_record, args=(current_map, style, "player_data"))
    thread_set(4+s, sort_load_record, args=(current_map, style, "angles"))
    thread_set(6+s, sort_load_record, args=(current_map, style, "positions"))
    thread_set(8+s, sort_load_record, args=(current_map, style, "attacks"))
    thread_set(10+s, sort_load_record, args=(current_map, style, "crouchs"))
    thread_set(12+s, sort_load_record, args=(current_map, style, "speed"))
    thread_set(14+s, sort_load_record, args=(current_map, style, "switches"))
    thread_set(20+s, run_bots_smooth)


def run_bots_smooth():
    index = 0
    for userid in es.getUseridList():
        if es.isbot(userid):
            if str(index) in rp_started:
                es.server.queuecmd(
                    'es_botsetvalue %s name "Normal - %s' % (userid, rp_player_data["%s" % index]["name"]))
                rp_botid[str(index)] = userid

            else:
                es.server.queuecmd('es_botsetvalue %s name "No record"' % (userid))
            index += 1
    for bot in rp_started:
        rp_started[bot] = 1

    msg('#200,130,40[Replay Bots] #100,100,100Succesfully loaded bots!!')
    record_replay()

def player_spawn(ev):
    userid = ev["userid"]
    if es.isbot(userid):
        player = getPlayer(userid)
        es.setplayerprop(userid,
                         "CCSPlayer.baseclass.baseclass.baseclass.baseclass.baseclass.baseclass.m_CollisionGroup",
                         1)
        player.noclip(1)
    logclient(userid)


def set_recordstart(userid):
    player = getPlayer(userid)
    resetclient(userid)
    player_data[userid]["weapon"] = str(player.weapon)
    started[userid] = 1


def botreplay_startrecord(args):
        set_recordstart(str(args[0]))
        msg('Recording %s' % str(args[0]))

def botreplay_stoprecord(args):
        record_stop(str(args[0]))

def botreplay_saverecord(args):
        record_save(str(args[0]), str(args[1]), str(args[2]))

def player_say(ev):
    userid = ev["userid"]
    text = ev["text"]
    player = getPlayer(userid)

    if text == "!rec":
        set_recordstart(userid)
        msg('Recording..')

    if text == "!record?":
        if thread_handle["tick"] > 1:
            msg('You are being recorded!')
            msg('Data block at %s ' % (thread_handle["tick"]))

    if text == "!replay":
        record_replay()

    if text == "replay_sm":
        run_bots_smooth()
    if text == "replay_load":
        load_bots()

    if text == "!rec_save":
        record_save(userid, current_map, "0")


    if text == "!rec_save_2":
        record_save(userid, current_map, "1")


def getPlayerAngle(userid):
    return tuple((float(es.getplayerprop(getPlayer(userid), eyeangle % x)) for x in xrange(2))) + (0.0,)
