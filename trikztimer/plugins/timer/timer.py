from usermsg import hudhint
from vecmath import vector
from usermsg import keyhint
from velohook import chat
from configobj import ConfigObj
import cPickle as pickle
import es
import os
import re
import random
import vecmath
import playerlib
import esc
import effectlib
import gamethread
import time
import iptocountry
import popuplib

""" Stuff imported from the folder """
trikz = es.import_addon("queue_timer")
mysql = es.import_addon("queue_timer/mysql")
TSQL = es.import_addon("queue_timer/threaded_mysql")

""" local storage area for preventing mysql executing too many times """
zones = {}

sounds = ['buttons/bell1.wav', 'ambient/3dmeagle.wav']

commands = {}

c_season = 3

tournament = {'status': 0,
              'queue': {},
              'coupe': [],
              'turn': 0,
              'time': 1800,
              'disconnect': 120,
              'tick': 0}

match = {}

auth_zone = 1
admins = ConfigObj(es.getAddonPath("queue_timer") + "/admins.ini")

# Current map in the server
current_map = es.ServerVar('eventscripts_currentmap')

var_timeleft = es.ServerVar('mp_timelimit')

timeleft = 0

auth = {'vaild': 0,
        'id': 0}

player = {}
timer = {}

client_pref = {}


def load_client_pref():
    global client_pref
    dictPath = os.path.join(es.getAddonPath("queue_timer"), "/database/clientpref.db")
    if os.path.isfile(dictPath):
        fileStream = open(dictPath, 'rb')
        client_pref = pickle.load(fileStream)
        fileStream.close()


def save_client_pref():
    dictPath = os.path.join(es.getAddonPath("queue_timer"), "database/clientpref.db")
    fileStream = open(dictPath, 'wb')
    pickle.dump(client_pref, fileStream)
    fileStream.close()


def unload():
    mysql.query.save()
    gamethread.cancelDelayed("event")
    gamethread.cancelDelayed("save")


def load():
    global zones, match, player, timer, auth, commands, mysql
    clear_cache()
    load_zones(current_map)
    load_client_pref()
    CreateTimer_save()
    for userid in es.getUseridList():
        if es.exists("userid", userid):
            steamid = es.getplayersteamid(userid)

            datahandle.client_validate(steamid)
            datahandle.timer_validate(steamid)
            CreateTimer_keyhint(userid)
            TimeLeft(var_timeleft, 0)
            TimerSolo_Stop(userid)
            TimerPartner_Stop(userid)
            CheckZone(userid)

    """ Partner menu """
    # TODO: startswith method
    chat.registerPublicCommand("!p", Menu.partner_menu, True, True)
    chat.registerPublicCommand("!partner", Menu.partner_menu, True, True)
    chat.registerHiddenCommand("/p", Menu.partner_menu, True, True)
    chat.registerHiddenCommand("/partner", Menu.partner_menu, True, True)

    """ Unpartner """
    chat.registerPublicCommand("!unpartner", Notify.unpartner, True, True)
    chat.registerHiddenCommand("/unpartner", Notify.unpartner, True, True)

    """ Notify Stop timer command """
    chat.registerPublicCommand("!stop", Notify.Timer_Stop, True, True)
    chat.registerPublicCommand("!stoptimer", Notify.Timer_Stop, True, True)
    chat.registerHiddenCommand("/stop", Notify.Timer_Stop, True, True)
    chat.registerHiddenCommand("/stoptimer", Notify.Timer_Stop, True, True)

    """ Notify country rank command """
    chat.registerPublicCommand("!crank", Notify.Country_rank, False, False, True)
    chat.registerHiddenCommand("/crank", Notify.Country_rank, False, False, True)

    """ Notify country rank command """
    chat.registerPublicCommand("!rank ", Notify.rank, False, False, True)
    chat.registerHiddenCommand("/rank ", Notify.rank, False, False, True)
    chat.registerPublicCommand("!rank", Notify.rank, False, False, False)
    chat.registerHiddenCommand("/rank", Notify.rank, False, False, False)

    chat.registerPublicCommand("!ranks", displayRanks, True, False, False)
    chat.registerHiddenCommand("/ranks", displayRanks, True, False, False)
    chat.registerPublicCommand("!chatranks", displayRanks, True, False, False)
    chat.registerHiddenCommand("/chatranks", displayRanks, True, False, False)

    """ Create zone command """
    chat.registerHiddenCommand("!tn", Menu.zones_create_command, False, False, True)
    chat.registerHiddenCommand("/tn", Menu.zones_create_command, False, False, True)

    """ Change points command """
    chat.registerHiddenCommand("!tcp", Menu.zones_points_command, False, False, True)
    chat.registerHiddenCommand("/tcp", Menu.zones_points_command, False, False, True)

    """ Change tier command"""
    chat.registerHiddenCommand("!tct", Menu.zones_tier_command, False, False, True)
    chat.registerHiddenCommand("/tct", Menu.zones_tier_command, False, False, True)

    """ Rename zone command"""
    chat.registerHiddenCommand("!tcn", Menu.zones_rename_command, False, False, True)
    chat.registerHiddenCommand("/tcn", Menu.zones_rename_command, False, False, True)

    """ Timmer admin menu """
    chat.registerHiddenCommand("!timer", Menu.start_menu, True, True)
    chat.registerHiddenCommand("/timer", Menu.start_menu, True, True)

    """ Hud menu"""
    chat.registerPublicCommand("!hud", Menu.settings, True, True)
    chat.registerPublicCommand("!settings", Menu.settings, True, True)
    chat.registerHiddenCommand("/hud", Menu.settings, True, True)
    chat.registerHiddenCommand("/settings", Menu.settings, True, True)

    """ Styles menu """
    chat.registerPublicCommand("!style", Menu.mode, True, True)
    chat.registerPublicCommand("!mode", Menu.mode, True, True)
    chat.registerPublicCommand("!n", Menu.mode, True, True)
    chat.registerPublicCommand("!sw", Menu.mode, True, True)
    chat.registerPublicCommand("!hsw", Menu.mode, True, True)
    chat.registerPublicCommand("!w", Menu.mode, True, True)

    chat.registerHiddenCommand("/style", Menu.mode, True, True)
    chat.registerHiddenCommand("/mode", Menu.mode, True, True)
    chat.registerHiddenCommand("/n", Menu.mode, True, True)
    chat.registerHiddenCommand("/sw", Menu.mode, True, True)
    chat.registerHiddenCommand("/hsw", Menu.mode, True, True)
    chat.registerHiddenCommand("/w", Menu.mode, True, True)

    """ Teleport to zones """
    chat.registerPublicCommand("!restart", tp_restart, True, True)
    chat.registerPublicCommand("!r", tp_restart, True, True)
    chat.registerPublicCommand("!start", tp_restart, True, True)
    chat.registerHiddenCommand("/r", tp_restart, True, True)
    chat.registerHiddenCommand("/restart", tp_restart, True, True)
    chat.registerHiddenCommand("/start", tp_restart, True, True)

    chat.registerPublicCommand("!b", tp_bonus, False, True, False)
    chat.registerPublicCommand("!b ", tp_bonus, False, True, True)
    chat.registerPublicCommand("!bonus", tp_bonus, False, True, True)
    chat.registerHiddenCommand("/b", tp_bonus, False, True, True)
    chat.registerHiddenCommand("/b ", tp_bonus, False, True, True)
    chat.registerHiddenCommand("/bonus", tp_bonus, False, True, True)

    chat.registerPublicCommand("!end", tp_end, True, True)
    chat.registerPublicCommand("!end", tp_end, True, True)
    chat.registerHiddenCommand("/end", tp_end, True, True)
    chat.registerHiddenCommand("/end", tp_end, True, True)

    chat.registerPublicCommand("!bend", tp_bend, True, False)
    chat.registerPublicCommand("!bend", tp_bend, True, False)
    chat.registerHiddenCommand("/bend", tp_bend, True, False)
    chat.registerHiddenCommand("/bend", tp_bend, True, False)

    """ View map points """
    chat.registerPublicCommand("!points", Notify.challenge_points, False, False, True)
    chat.registerHiddenCommand("/points", Notify.challenge_points, False, False, True)

    """ View records """
    chat.registerPublicCommand("!wr", Notify.wr, False, False, True)
    chat.registerHiddenCommand("/wr", Notify.wr, False, False, True)

    chat.registerPublicCommand("!bwr", Notify.bwr, False, False, False)
    chat.registerPublicCommand("!bwr ", Notify.bwr, False, False, True)
    chat.registerHiddenCommand("/bwr", Notify.bwr, False, False, False)
    chat.registerHiddenCommand("/bwr ", Notify.bwr, False, False, True)

    """ Top points """
    chat.registerPublicCommand("!top", Notify.top, False, True)
    chat.registerHiddenCommand("/top", Notify.top, False, True)

    chat.registerPublicCommand("!ctop", Notify.ctop, False, False, True)
    chat.registerHiddenCommand("/ctop", Notify.ctop, False, False, True)

    chat.registerPublicCommand("!register", TSet.signup, False, False, False)
    chat.registerHiddenCommand("/register", TSet.signup, False, False, False)
    chat.registerPublicCommand("!signup", TSet.signup, False, False, False)
    chat.registerHiddenCommand("/signup", TSet.signup, False, False, False)
    esc.msg('#255,0,0[Timer] #0,255,0has been reloaded')
    esc.msg('#255,0,0[Timer] #0,255,0Might experience lag spike for a sec..')

    UpdateRanks()
    gamethread.delayed(30, UpdateRankedPointsAll)



def player_say(ev):
    text = ev['text']
    if text == '!update':
        TSQL.Query.fetchone('SELECT name FROM stats', callback=test)
    if text == 'update_all':
        UpdateRanks()


def test(data):

    esc.msg(str(data[0]))


def player_spawn(ev):
    userid = ev["userid"]
    steamid = es.getplayersteamid(userid)
    ply = playerlib.getPlayer(userid)
    datahandle.timer_validate(steamid)
    datahandle.client_validate(steamid)
    name = es.getplayername(userid)

    if not ply.isdead:
        data = mysql.query.fetchone("SELECT name FROM completed WHERE steamid='%s'", (steamid,))
        if bool(data):
            mysql.query.execute("UPDATE completed SET name='%s' WHERE steamid='%s'", (name, steamid))

        data = mysql.query.fetchone("SELECT name FROM completed WHERE steamid_partner='%s'", (steamid,))
        if bool(data):
            mysql.query.execute("UPDATE completed SET name_partner='%s' WHERE steamid_partner='%s'", (name, steamid))

        data = mysql.query.fetchone("SELECT name FROM completed_personal WHERE steamid='%s'", (steamid,))
        if bool(data):
            mysql.query.execute("UPDATE completed_personal SET name='%s' WHERE steamid='%s'", (name, steamid))
        gamethread.cancelDelayed('CheckZone_%s' % userid)
        gamethread.cancelDelayed("keyhint_%s" % userid)
        CheckZone(userid)
        CreateTimer_keyhint(userid)


def displayRanks(userid):
    chat = es.import_addon('queue_timer/plugins/chat')
    tags = chat.tags
    clan_tag = popuplib.create('Clan Tags')
    clan_tag.addline('Chat ranks:')
    clan_tag.addline(' ')
    for pos in tags:
        if not pos.startswith('[U:'):
            if str(tags[pos]['type']) == "ranked":
                clan_tag.addline("Ranked [%s-%s] %s" % (tags[pos]['max_rank'], tags[pos]['min_rank'], pos))


            elif tags[pos]["type"] == "points":
                clan_tag.addline("Points [%s-%s] %s" % (tags[pos]['min_points'], tags[pos]['max_points'], pos))

    clan_tag.addline('Beta tester (Limited)')
    clan_tag.addline('0. Exit')
    clan_tag.enablekeys = "1230"
    clan_tag.unsend(userid)
    clan_tag.send(userid)
    clan_tag.delete()


def displayPoints(steamid):
    row = mysql.query.fetchone("SELECT points FROM stats WHERE steamid = '%s'", (steamid,))
    return row[0]


def displayRank(steamid, country=None):
    index = 0
    if not country:
        for item in mysql.query.fetchall("SELECT steamid, points FROM stats ORDER by points DESC"):
            index += 1
            if item[0] == steamid:
                return index
    else:
        for item in mysql.query.fetchall("SELECT steamid, points FROM stats WHERE country='%s' ORDER by points DESC",
                                         (country,)):
            index += 1
            if item[0] == steamid:
                return index


def displayLen(country=None):
    if not country:
        data = mysql.query.fetchone("SELECT COUNT(steamid) FROM stats")
        return data[0]

    else:
        data = mysql.query.fetchone("SELECT COUNT(steamid) FROM stats WHERE country='%s'", (country,))
        return data[0]


class DataHandler:
    def __init__(self):
        pass

    def client_validate(self, steamid):
        if not steamid in client_pref:
            client_pref[steamid] = {'partner': None,
                                    'id': None,
                                    'zone': None,
                                    'timer_id': None,
                                    'disabled': 0,
                                    'disabled_keyhint': 0,
                                    'case': 0,
                                    'text_display': "",
                                    'spec_display': "",
                                    'last_spec': -1,
                                    'now_spec': -1,
                                    'spectators': [],
                                    'spec_list': [],
                                    'settings_hudhint': 1,
                                    'settings_jumps': 0,
                                    'settings_flashbangs': 0,
                                    'settings_strafes': 1,
                                    'settings_speedmeter': 1,
                                    'settings_macro': 0}

            player[steamid] = {'partner': None,
                               'id': None,
                               'zone': None,
                               'timer_id': None,
                               'disabled': client_pref[steamid]["disabled"],
                               'disabled_keyhint': client_pref[steamid]["disabled_keyhint"],
                               'case': 0,
                               'text_display': "",
                               'spec_display': "",
                               'last_spec': -1,
                               'now_spec': -1,
                               'spec_list': [],
                               'spectators': [],
                               'keyhint_display': "",
                               'settings_hudhint': client_pref[steamid]["settings_hudhint"],
                               'settings_jumps': 0,
                               'settings_flashbangs': 0,
                               'settings_strafes': 1,
                               'settings_speedmeter': 1,
                               'settings_macro': client_pref[steamid]["settings_macro"]}

            if not "settings_macro" in client_pref[steamid]:
                client_pref[steamid]["settings_macro"] = 0

    def timer_validate(self, steamid):
        if steamid in client_pref:
            player[steamid] = {'partner': None,
                               'id': None,
                               'zone': None,
                               'timer_id': None,
                               'disabled': client_pref[steamid]["disabled"],
                               'disabled_keyhint': client_pref[steamid]["disabled_keyhint"],
                               'case': 0,
                               'text_display': "",
                               'spec_display': "",
                               'last_spec': -1,
                               'now_spec': -1,
                               'spec_list': [],
                               'spectators': [],
                               'keyhint_display': "",
                               'settings_hudhint': client_pref[steamid]["settings_hudhint"],
                               'settings_jumps': 0,
                               'settings_flashbangs': 0,
                               'settings_strafes': 1,
                               'settings_speedmeter': 1,
                               'settings_macro': client_pref[steamid]["settings_macro"]}
        else:
            datahandle.client_validate(steamid)


datahandle = DataHandler()


def player_activate(ev):
    userid = ev["userid"]
    steamid = es.getplayersteamid(userid)
    name = es.getplayername(userid)
    datahandle.client_validate(steamid)
    datahandle.timer_validate(steamid)

    data_pack = {'userid': userid, 'steamid': steamid, 'name': name}

    sql = "SELECT steamid, points, country, points_last_seen, ip, (SELECT COUNT(*) FROM stats) as length, (SELECT COUNT(*)+1 FROM stats WHERE points>x.points) AS rank FROM `stats`x WHERE x.steamid = '%s'" % steamid
    TSQL.Query.fetchone(sql, callback=player_join_callback, data_pack=data_pack)
    save_client_pref()


def player_join_callback(data, data_pack):
    userid = data_pack['userid']
    steamid = data_pack['steamid']
    name = data_pack['name']

    if bool(data):
        rank = data[6]
        length = data[5]
        if data[4] == '0':
            ip = playerlib.getPlayer(userid).address.split(':')[0]
            TSQL.Query.execute("UPDATE stats SET name='%s', points_last_seen=points, ip='%s' WHERE steamid='%s'",
                               (name, ip, steamid))
        else:
            TSQL.Query.execute("UPDATE stats SET name='%s', points_last_seen=points WHERE steamid='%s'",
                               (name, steamid))
        esc.msg('#snowPlayer:#245,61,0 %s #tomato[%s points] #245,0,61(%s/%s) #snowconnected from #245,0,61%s' % (
        name, data[1], rank, length, data[2]))
        earned = data[1] - data[3]
        if earned < 0:
            esc.tell(userid,
                     '#255,0,0 ** NOTICE ** #0,255,0You have #255,0,0lost#0,255,0 %s points in the period you were inactive, because of new ranks!' % (
                     earned))
        elif earned > 0:
            esc.tell(userid,
                     '#255,0,0 ** NOTICE ** #0,255,0You have #255,0,0gained#0,255,0 %s points in the period you were inactive, because of new ranks!' % (
                         earned))
        else:
            esc.tell(userid,
                     '#255,0,0 ** NOTICE ** #0,255,0Your points has not been modified in the period you were inactive!')

    else:
        ip = playerlib.getPlayer(userid).address.split(':')[0]
        country = iptocountry.get_country(ip)[0]
        TSQL.Query.execute(
            "INSERT INTO stats (steamid, points, name, country, points_last_seen, ip) VALUES ('%s', 0, '%s', '%s', 0, '%s')" % (
            steamid, name, country, ip))
        esc.msg('#snowPlayer:#245,61,0 %s #245,0,61(New player) #snowconnected from#245,0,61 %s' % (name, country))


def load_zones(s_map):
    clear_cache()
    s_map = str(s_map)
    global zones, commands
    zones = {}
    commands = {}
    TSQL.Query.fetchall(
        "SELECT location_1, location_2, location_3, location_4, restart_loc, id, type, name, tier, points, partner_needed FROM zones WHERE map='%s'",
        args=(s_map,), callback=load_zones_callback)


def load_zones_callback(data):
    if bool(data):

        for item in data:

            if str(item[5]) not in zones:

                name = str(item[5])

                if str(item[0]) != "0":
                    t_loc_1 = (float(item[0].split(",")[0]), float(item[0].split(",")[1]), float(item[0].split(",")[2]))
                else:
                    t_loc_1 = "none"

                if str(item[1]) != "0":
                    t_loc_2 = (float(item[1].split(",")[0]), float(item[1].split(",")[1]), float(item[1].split(",")[2]))
                    t_loc_2_fixed = (
                        float(item[1].split(",")[0]), float(item[1].split(",")[1]), float(item[0].split(",")[2]))
                else:
                    t_loc_2 = "none"

                if str(item[2]) != "0":
                    t_loc_3 = (float(item[2].split(",")[0]), float(item[2].split(",")[1]), float(item[2].split(",")[2]))

                else:
                    t_loc_3 = "none"

                if str(item[3]) != "0":
                    t_loc_4 = (float(item[3].split(",")[0]), float(item[3].split(",")[1]), float(item[3].split(",")[2]))
                    t_loc_4_fixed = (
                        float(item[3].split(",")[0]), float(item[3].split(",")[1]), float(item[2].split(",")[2]))
                else:
                    t_loc_4 = "none"

                if str(item[4]) != "0":
                    t_loc_5 = (float(item[4].split(",")[0]), float(item[4].split(",")[1]), float(item[4].split(",")[2]))
                else:
                    t_loc_5 = "none"

                zones[name] = {}
                zones[name]['location_1'] = t_loc_1
                zones[name]['location_2'] = t_loc_2
                zones[name]['location_3'] = t_loc_3
                zones[name]['location_4'] = t_loc_4
                zones[name]['restart_loc'] = t_loc_5
                zones[name]['id'] = item[5]
                zones[name]['type'] = item[6]
                zones[name]['name'] = item[7]
                zones[name]['tier'] = item[8]
                zones[name]['points'] = item[9]
                zones[name]['partner_needed'] = item[10]

                if not item[7] in commands:
                    commands[item[7]] = item[5]

                if not t_loc_1 == "none" and not t_loc_2 == "none":
                    drawbox(0, item[5], t_loc_1, "start", t_loc_2_fixed)

                if not t_loc_3 == "none" and not t_loc_4 == "none":
                    drawbox(0, item[5], t_loc_3, "end", t_loc_4_fixed)



    else:
        zones["0"] = {}
        zones["0"]['location_1'] = "none"
        zones["0"]['location_2'] = "none"
        zones["0"]['location_3'] = "none"
        zones["0"]['location_4'] = "none"
        zones["0"]['restart_loc'] = "none"


def clear_cache():
    """
    Cleares all the visual of zones in the server
    :return:
    """
    data = mysql.query.fetchall('SELECT id FROM zones')
    if bool(data):
        for object in data:
            gamethread.cancelDelayed("drawbox_%s" % object[0])


def auth_zones():
    data = mysql.query.fetchone("SELECT id FROM zones WHERE type='none'")
    if bool(data):
        return data[0]
    else:
        return "True"


def CheckPartner(userid):
    steamid = es.getplayersteamid(userid)
    steamid_partner = es.getplayersteamid(player[steamid]["partner"])
    if bool(steamid_partner):
        if str(player[steamid_partner]["partner"]) == str(userid):
            return True
        else:
            return False
    else:
        return False


def TimeFormat(seconds, op=None, milli=None):
    hours, minutes = divmod(seconds, 3600)
    minutes, seconds = divmod(minutes, 60)
    if not milli:
        milli = str(seconds).split(".")[1][:2]
    if op:
        return "%02d:%02d:%s" % (minutes, seconds, milli[0])
    else:
        if milli:
            return "%02d:%02d:%s" % (minutes, seconds, milli)
        else:
            return "%02d:%02d" % (minutes, seconds)


def timer_unique():
    index = 0
    for object in timer:
        index += 1
    return index


def TimerDisable(userid):
    steamid = es.getplayersteamid(userid)
    player[steamid]['disabled'] = 1


def Timer_Validate(userid):
    steamid = es.getplayersteamid(userid)
    if steamid not in timer:
        timer[steamid] = {'partner_needed': 0,
                          'time': time.time(),
                          'flashbangs': 0,
                          'jumps': 0,
                          'strafes': 0,
                          'style': "Normal",
                          'id': player[steamid]["id"],
                          'state': 0}

    else:
        timer[steamid]["partner_needed"] = 0
        timer[steamid]["time"] = time.time()
        timer[steamid]["flashbangs"] = 0
        timer[steamid]["strafes"] = 0
        timer[steamid]["jumps"] = 0
        timer[steamid]["id"] = player[steamid]["id"]
        timer[steamid]["state"] = 0


def TimerSolo_Reset(userid):
    steamid = es.getplayersteamid(userid)
    if steamid not in timer:
        timer[steamid] = {'partner_needed': 0,
                          'time': time.time(),
                          'flashbangs': 0,
                          'jumps': 0,
                          'strafes': 0,
                          'style': "Normal",
                          'id': player[steamid]["id"],
                          'state': 1}

    else:
        timer[steamid]["partner_needed"] = 0
        timer[steamid]["time"] = time.time()
        timer[steamid]["flashbangs"] = 0
        timer[steamid]["strafes"] = 0
        timer[steamid]["jumps"] = 0
        timer[steamid]["id"] = player[steamid]["id"]
        timer[steamid]["state"] = 1


def TimerSolo_Stop(userid):
    steamid = es.getplayersteamid(userid)
    if steamid not in timer:
        timer[steamid] = {'partner_needed': 0,
                          'time': 0,
                          'flashbangs': 0,
                          'jumps': 0,
                          'style': "Normal",
                          'id': player[steamid]["id"],
                          'state': 0}
    else:
        timer[steamid]["partner_needed"] = 0
        timer[steamid]["time"] = 0
        timer[steamid]["strafes"] = 0
        timer[steamid]["flashbangs"] = 0
        timer[steamid]["jumps"] = 0
        timer[steamid]["id"] = player[steamid]["id"]
        timer[steamid]["state"] = 0


def TimerPartner_Stop(userid):
    if CheckPartner(userid):
        steamid = es.getplayersteamid(userid)
        timer_id = player[steamid]["timer_id"]
        if timer_id not in timer:
            timer[timer_id] = {'partner_needed': 1,
                               'time': 0,
                               'flashbangs': 0,
                               'jumps': 0,
                               'style': "Normal",
                               'id': player[steamid]["id"],
                               'state': 0}
        else:
            timer[timer_id]["partner_needed"] = 1
            timer[timer_id]["time"] = 0
            timer[timer_id]["jumps"] = 0
            timer[timer_id]["strafes"] = 0
            timer[timer_id]["flashbangs"] = 0
            timer[timer_id]["id"] = player[steamid]["id"]
            timer[timer_id]["state"] = 0


def TimerPartner_Reset(userid):
    if CheckPartner(userid):
        steamid = es.getplayersteamid(userid)
        timer_id = player[steamid]["timer_id"]
        if timer_id not in timer:
            timer[timer_id] = {'partner_needed': 1,
                               'time': time.time(),
                               'flashbangs': 0,
                               'jumps': 0,
                               'strafes': 0,
                               'style': "Normal",
                               'id': player[steamid]["id"],
                               'state': 1}

        else:
            timer[timer_id]["partner_needed"] = 1
            timer[timer_id]["time"] = time.time()
            timer[timer_id]["jumps"] = 0
            timer[timer_id]["strafes"] = 0
            timer[timer_id]["flashbangs"] = 0
            timer[timer_id]["state"] = 1
            timer[timer_id]["id"] = player[steamid]["id"]


def ShowHudHint(userid):
    steamid = es.getplayersteamid(userid)
    id = str(player[steamid]['id'])
    timer_id = player[steamid]["timer_id"]
    player[steamid]["zone"] = "start"
    velocity = round(vector(float(es.getplayerprop(userid, 'CBasePlayer.localdata.m_vecVelocity[0]')),
                            float(es.getplayerprop(userid, 'CBasePlayer.localdata.m_vecVelocity[1]'))).length(), 2)
    debug_mode = 1

    if zones[id]['type'] == "timer":
        if player[steamid]["disabled"] == 0:

            if zones[id]["partner_needed"] == 1 and not CheckPartner(userid):

                TSet.teleport(userid)

                hudhint(userid, '(00:00:00)\n \nSpeed: %s\nYou need !partner in this area' % (velocity))

                TimerSolo_Stop(userid)




            elif zones[id]["partner_needed"] == 1 and CheckPartner(userid):
                TSet.teleport(userid)
                partner = es.getplayersteamid(player[steamid]["partner"])

                if player[partner]["zone"] == "start" and player[partner]['id'] == id:

                    player[steamid]["text_display"] = '(00:00:00)\n \nMode: %s' % (timer[timer_id]['style'])
                    string = player[steamid]["text_display"]

                    # Settings
                    if player[steamid]["settings_strafes"] == 1:
                        string += "\nStrafes: %s" % timer[timer_id]["strafes"]

                    if player[steamid]["settings_jumps"] == 1:
                        string += "\nJumps: %s" % timer[timer_id]["jumps"]

                    if player[steamid]["settings_flashbangs"] == 1:
                        string += "\nFlashbangs: %s" % timer[timer_id]["flashbangs"]

                    if player[steamid]["settings_speedmeter"] == 1:
                        string += "\nSpeed: %s" % velocity

                    # Extra
                    string += "\n(Ready!)"

                    if player[steamid]['settings_hudhint'] == 1:
                        hudhint(userid, string)

                    TimerPartner_Reset(userid)



                elif timer[timer_id]['state'] == 2 and not player[partner]['id'] == id:
                    hudhint(userid, '(%s)\n(REAL: %s)\n[%s Timer]\n \nMode: %s\nSpeed: %s' % (
                        TimeFormat((float(time.time()) - float(timer[timer_id]['time'])), 1),
                        zones[timer[timer_id]['id']]['name'],
                        zones[id]['name'], timer[timer_id]['style'], velocity))



                elif timer[timer_id]['state'] == 0:
                    player[steamid]["text_display"] = '(00:00:00)\n \nMode: %s' % (timer[timer_id]['style'])
                    string = player[steamid]["text_display"]

                    # Settings
                    if player[steamid]["settings_strafes"] == 1:
                        string += "\nStrafes: %s" % timer[timer_id]["strafes"]

                    if player[steamid]["settings_jumps"] == 1:
                        string += "\nJumps: %s" % timer[timer_id]["jumps"]

                    if player[steamid]["settings_flashbangs"] == 1:
                        string += "\nFlashbangs: %s" % timer[timer_id]["flashbangs"]

                    if player[steamid]["settings_speedmeter"] == 1:
                        string += "\nSpeed: %s" % velocity

                    # Extra
                    string += "\n(Waiting for partner...)"

                    if player[steamid]['settings_hudhint'] == 1:
                        hudhint(userid, string)


                elif timer[timer_id]['state'] == 2:
                    player[steamid]["text_display"] = '(%s)\n \nMode: %s' % (
                        TimeFormat((float(time.time()) - float(timer[timer_id]['time'])), 1), timer[timer_id]['style'])
                    string = player[steamid]["text_display"]
                    # Settings
                    if player[steamid]["settings_strafes"] == 1:
                        string += "\nStrafes: %s" % timer[timer_id]["strafes"]

                    if player[steamid]["settings_jumps"] == 1:
                        string += "\nJumps: %s" % timer[timer_id]["jumps"]

                    if player[steamid]["settings_flashbangs"] == 1:
                        string += "\nFlashbangs: %s" % timer[timer_id]["flashbangs"]

                    if player[steamid]["settings_speedmeter"] == 1:
                        string += "\nSpeed: %s" % velocity

                    if player[steamid]['settings_hudhint'] == 1:
                        hudhint(userid, string)




            else:
                if CheckPartner(userid):
                    if not timer[timer_id]['state'] == 2:
                        esc.tell(userid,
                                 '#255,51,0[#0,137,255 Timer #255,51,0] #snowYou automatic unpartnered with %s' % es.getplayername(
                                     player[steamid]["partner"]))
                        esc.tell(player[steamid]["partner"],
                                 '#255,51,0[#0,137,255 Timer #255,51,0] #snowYou automatic unpartnered with %s' % es.getplayername(
                                     userid))
                        player[steamid]["partner"] = None

                        TimerSolo_Reset(userid)
                        hudhint(userid, '(00:00:00) \n \nMode: %s\nSpeed: %s\n(SOLO - Ready!)' % (
                            timer[steamid]['style'], velocity))
                    else:
                        player[steamid]["text_display"] = '(In Bonus !unpartner)\n(%s)\n \nMode: %s' % (
                            TimeFormat((float(time.time()) - float(timer[timer_id]['time'])), 1),
                            timer[timer_id]['style'])
                        string = player[steamid]["text_display"]
                        # Settings
                        if player[steamid]["settings_strafes"] == 1:
                            string += "\nStrafes: %s" % timer[timer_id]["strafes"]

                        if player[steamid]["settings_jumps"] == 1:
                            string += "\nJumps: %s" % timer[timer_id]["jumps"]

                        if player[steamid]["settings_flashbangs"] == 1:
                            string += "\nFlashbangs: %s" % timer[timer_id]["flashbangs"]

                        if player[steamid]["settings_speedmeter"] == 1:
                            string += "\nSpeed: %s" % velocity

                        if player[steamid]['settings_hudhint'] == 1:
                            hudhint(userid, string)
                else:
                    TimerSolo_Reset(userid)
                    hudhint(userid, '(00:00:00) \n  \nMode: %s\nSpeed: %s\n(SOLO - Ready!)' % (
                        timer[steamid]['style'], velocity))

                # Set players noblock
                ply = playerlib.getPlayer(userid)
                if not ply.getNoBlock():
                    trikz = es.import_addon("queue_timer")
                    trikz.client[steamid]["player_state"] = "Ghost"
                    ply.setColor(255, 255, 255, 100)
                    es.setplayerprop(userid,
                                     "CCSPlayer.baseclass.baseclass.baseclass.baseclass.baseclass.baseclass.m_CollisionGroup",
                                     2)


    elif zones[id]['type'] == "cheat":
        esc.tell(userid, 'You have entered cheat zone')
        TimerSolo_Stop(userid)
        TimerPartner_Stop(userid)

    elif zones[id]['type'] == "tournament":
        # Check if enabled
        TSet.teleport(userid)


def player_disconnect(ev):
    userid = ev["userid"]
    gamethread.cancelDelayed("CheckZone_%s" % userid)
    gamethread.cancelDelayed("keyhint_%s" % userid)


def tp_restart(userid):
    if "Map" in commands:
        if not zones[str(commands["Map"])]['restart_loc'] == "none":
            restart_location = zones[str(commands["Map"])]['restart_loc']
            es.server.queuecmd(
                'es_setpos %s %s %s %s' % (
                    userid, restart_location[0], restart_location[1], restart_location[2]))
            TimerSolo_Stop(userid)
            TimerPartner_Stop(userid)
        else:
            esc.tell(userid,
                     '#255,0,0#255,51,0[#0,137,255 Timer #255,51,0] #snowNo restart location has been set, contact admin!')
    else:
        esc.tell(userid,
                 '#255,0,0#255,51,0[#0,137,255 Timer #255,51,0] #snowNo restart location has been set, contact admin!')


def tp_end(userid):
    steamid = es.getplayersteamid(userid)
    if "Map" in commands:
        if not zones[str(commands["Map"])]['location_3'] == "none" and not zones[str(commands["Map"])][
            'location_4'] == "none":
            end_point_1 = zones[str(commands["Map"])]['location_3']
            end_point_2 = zones[str(commands["Map"])]['location_4']

            if end_point_1[2] >= end_point_2[2]:
                Point1 = ((end_point_2[0] - end_point_1[0]) / 2)
                Point2 = ((end_point_2[1] - end_point_1[1]) / 2)
                restart_location = (end_point_1[0] + Point1, end_point_1[1] + Point2, end_point_2[2])
            else:
                Point1 = ((end_point_2[0] - end_point_1[0]) / 2)
                Point2 = ((end_point_2[1] - end_point_1[1]) / 2)
                restart_location = (end_point_1[0] + Point1, end_point_1[1] + Point2, end_point_1[2])

            es.server.queuecmd(
                'es_setpos %s %s %s %s' % (
                    userid, restart_location[0], restart_location[1], restart_location[2]))
            if CheckPartner(userid):
                esc.tell(userid,
                         '#255,51,0[#0,137,255 Timer #255,51,0] #snowYou automatic unpartnered with %s' % es.getplayername(
                             player[steamid]["partner"]))
                esc.tell(player[steamid]["partner"],
                         '#255,51,0[#0,137,255 Timer #255,51,0] #snowYou automatic unpartnered with %s' % es.getplayername(
                             userid))
                player[steamid]["partner"] = None
        else:
            esc.tell(userid,
                     '#255,0,0#255,51,0[#0,137,255 Timer #255,51,0] #snowThere are no end!')
    else:
        esc.tell(userid,
                 '#255,0,0#255,51,0[#0,137,255 Timer #255,51,0] #snowNo end location has not been calculated contact admin!')


def tp_bend(userid, text, steamid, name):
    number = 0
    find_number = re.findall(r'\d+', text)
    if len(find_number) > 0:
        number = find_number[0]

    if number == 0:
        if "Bonus 1" in commands:
            if not zones[str(commands["Bonus 1"])]['location_3'] == "none" and not zones[str(commands["Bonus 1"])][
                'location_4'] == "none":
                end_point_1 = zones[str(commands["Bonus 1"])]['location_3']
                end_point_2 = zones[str(commands["Bonus 1"])]['location_4']

                if end_point_1[2] >= end_point_2[2]:
                    Point1 = ((end_point_2[0] - end_point_1[0]) / 2)
                    Point2 = ((end_point_2[1] - end_point_1[1]) / 2)
                    restart_location = (end_point_1[0] + Point1, end_point_1[1] + Point2, end_point_2[2])
                else:
                    Point1 = ((end_point_2[0] - end_point_1[0]) / 2)
                    Point2 = ((end_point_2[1] - end_point_1[1]) / 2)
                    restart_location = (end_point_1[0] + Point1, end_point_1[1] + Point2, end_point_1[2])

                es.server.queuecmd(
                    'es_setpos %s %s %s %s' % (
                        userid, restart_location[0], restart_location[1], restart_location[2]))
                if CheckPartner(userid):
                    esc.tell(userid,
                             '#255,51,0[#0,137,255 Timer #255,51,0] #snowYou automatic unpartnered with %s' % es.getplayername(
                                 player[steamid]["partner"]))
                    esc.tell(player[steamid]["partner"],
                             '#255,51,0[#0,137,255 Timer #255,51,0] #snowYou automatic unpartnered with %s' % es.getplayername(
                                 userid))
                    player[steamid]["partner"] = None
            else:
                esc.tell(userid,
                         '#255,0,0#255,51,0[#0,137,255 Timer #255,51,0] #snowThere are no end!')
        else:
            esc.tell(userid,
                     '#255,0,0#255,51,0[#0,137,255 Timer #255,51,0] #snowNo end location has not been calculated contact admin!')

    elif "Bonus %s" % number in commands:
        if not zones[str(commands["Bonus %s" % number])]['location_3'] == "none" and not \
                zones[str(commands["Bonus %s" % number])][
                    'location_4'] == "none":
            end_point_1 = zones[str(commands["Bonus %s"] % number)]['location_3']
            end_point_2 = zones[str(commands["Bonus %s"] % number)]['location_4']

            if end_point_1[2] >= end_point_2[2]:
                Point1 = ((end_point_2[0] - end_point_1[0]) / 2)
                Point2 = ((end_point_2[1] - end_point_1[1]) / 2)
                restart_location = (end_point_1[0] + Point1, end_point_1[1] + Point2, end_point_2[2])
            else:
                Point1 = ((end_point_2[0] - end_point_1[0]) / 2)
                Point2 = ((end_point_2[1] - end_point_1[1]) / 2)
                restart_location = (end_point_1[0] + Point1, end_point_1[1] + Point2, end_point_1[2])

            es.server.queuecmd(
                'es_setpos %s %s %s %s' % (
                    userid, restart_location[0], restart_location[1], restart_location[2]))
            TimerSolo_Stop(userid)
            TimerPartner_Stop(userid)
        else:
            esc.tell(userid,
                     '#255,0,0#255,51,0[#0,137,255 Timer #255,51,0] #snowThere are no end!')
    else:
        esc.tell(userid,
                 '#255,0,0#255,51,0[#0,137,255 Timer #255,51,0] #snowNo end location has not been calculated contact admin!')


def tp_bonus(userid, text, steamid, name):
    number = 0
    find_number = re.findall(r'\d+', text)
    if len(find_number) > 0:
        number = find_number[0]

    if number == 0:
        if "Bonus 1" in commands:
            if not zones[str(commands["Bonus 1"])]['restart_loc'] == "none":
                restart_location = zones[str(commands["Bonus 1"])]['restart_loc']
                es.server.queuecmd(
                    'es_setpos %s %s %s %s' % (
                        userid, restart_location[0], restart_location[1], restart_location[2]))
                TimerSolo_Stop(userid)
                TimerPartner_Stop(userid)
            else:
                esc.tell(userid,
                         '#255,0,0#255,51,0[#0,137,255 Timer #255,51,0] #yellowBonus 1 #snowteleport location has not been set, contact admin!')
        else:
            esc.tell(userid,
                     '#255,0,0#255,51,0[#0,137,255 Timer #255,51,0] #snowThat bonus does not exist!')

    elif "Bonus %s" % number in commands:
        if not zones[str(commands["Bonus %s" % number])]['restart_loc'] == "none":
            restart_location = zones[str(commands["Bonus %s" % number])]['restart_loc']
            es.server.queuecmd(
                'es_setpos %s %s %s %s' % (
                    userid, restart_location[0], restart_location[1], restart_location[2]))
            TimerSolo_Stop(userid)
            TimerPartner_Stop(userid)
        else:
            esc.tell(userid,
                     '#255,0,0#255,51,0[#0,137,255 Timer #255,51,0] #yellowBonus %s #snowteleport location has not been set, contact admin!' % number)
    else:
        esc.tell(userid,
                 '#255,0,0#255,51,0[#0,137,255 Timer #255,51,0] #snowThat bonus does not exist!')


def CheckZone(userid):
    steamid = es.getplayersteamid(userid)
    ply = playerlib.getPlayer(userid)
    if not ply.isdead:
        if steamid in timer:
            if steamid in player:
                location = es.getplayerlocation(userid)
                timer_id = player[steamid]["timer_id"]

                velocity = round(vector(float(es.getplayerprop(userid, 'CBasePlayer.localdata.m_vecVelocity[0]')),
                                        float(es.getplayerprop(userid,
                                                               'CBasePlayer.localdata.m_vecVelocity[1]'))).length(), 2)

                if player[steamid]['disabled'] == 0:
                    for id in zones:
                        if zones[id]['location_1'] != "none" and zones[id][
                            'location_2'] != "none" and vecmath.isbetweenRect(location, zones[id]['location_1'],
                                                                              zones[id]['location_2']):
                            player[steamid]['id'] = str(id)
                            ShowHudHint(userid)
                            break

                        if zones[id]['location_3'] != "none" and zones[id][
                            'location_4'] != "none" and vecmath.isbetweenRect(location, zones[id]['location_3'],
                                                                              zones[id]['location_4']):
                            player[steamid]['id'] = str(id)
                            EndZone(userid)
                            break

                    else:
                        string = player[steamid]["text_display"]
                        player[steamid]['zone'] = "none"

                        # PARTNER TIMER
                        if CheckPartner(userid):
                            player[steamid]['id'] = timer[timer_id]['id']
                            if timer[timer_id]['state'] == 1:
                                timer[timer_id]['state'] = 2
                                userid_partner = player[steamid]["partner"]

                                es.server.queuecmd('es_sexec %s sm_record.start' % userid)
                                es.server.queuecmd('es_sexec %s sm_record.start' % userid_partner)
                            elif timer[timer_id]['state'] == 2:

                                player[steamid]["text_display"] = '(%s)\n \nMode: %s' % (
                                    TimeFormat(float(time.time()) - float(timer[timer_id]['time']), 1),
                                    timer[timer_id]['style'])

                                # Settings
                                if player[steamid]["settings_strafes"] == 1:
                                    string += "\nStrafes: %s" % timer[timer_id]["strafes"]

                                if player[steamid]["settings_jumps"] == 1:
                                    string += "\nJumps: %s" % timer[timer_id]["jumps"]

                                if player[steamid]["settings_flashbangs"] == 1:
                                    string += "\nFlashbangs: %s" % timer[timer_id]["flashbangs"]

                                if player[steamid]["settings_speedmeter"] == 1:
                                    string += "\nSpeed: %s" % velocity

                                if player[steamid]['settings_hudhint'] == 1:
                                    hudhint(userid, string)



                            else:
                                if player[steamid]['settings_hudhint'] == 1:
                                    hudhint(userid, '(Timer stopped)\n \nPartner: %s\nSpeed: %s' % (
                                        es.getplayername(player[steamid]["partner"]), velocity))


                        ####################

                        # SOLO TIMER

                        elif timer[steamid]['state'] == 1:
                            player[steamid]['id'] = timer[steamid]['id']
                            timer[steamid]['state'] = 2

                        elif timer[steamid]['state'] == 2:
                            player[steamid]['id'] = timer[steamid]['id']
                            string = '(%s)\n \nMode: %s' % (
                                TimeFormat(float(time.time()) - float(timer[steamid]['time']), 1),
                                timer[steamid]['style'])

                            player[steamid]["text_display"] = string

                            # Settings
                            if player[steamid]["settings_strafes"] == 1:
                                string += "\nStrafes: %s" % timer[steamid]["strafes"]

                            if player[steamid]["settings_jumps"] == 1:
                                string += "\nJumps: %s" % timer[steamid]["jumps"]

                            if player[steamid]["settings_flashbangs"] == 1:
                                string += "\nFlashbangs: %s" % timer[steamid]["flashbangs"]

                            if player[steamid]["settings_speedmeter"] == 1:
                                string += "\nSpeed: %s" % velocity

                            if player[steamid]['settings_hudhint'] == 1:
                                hudhint(userid, string)

                        #####################


                        elif player[steamid]['settings_hudhint'] == 1:
                            hudhint(userid, 'Speed: %s' % velocity)


                elif player[steamid]['settings_hudhint'] == 1:
                    hudhint(userid, '(Timer disabled)\nSpeed: %s' % velocity)

            else:
                datahandle.timer_validate(userid)
        else:
            Timer_Validate(userid)

    gamethread.delayedname(0.1, 'CheckZone_%s' % userid, CheckZone, args=(userid))


def GetWRPersonal(map, style, type):
    wr = mysql.query.fetchone(
        "SELECT steamid, time, id FROM completed_personal WHERE map='%s' AND style='%s' AND type='%s' AND season='%s' ORDER BY time ASC",
        (map, style, type, c_season))
    if bool(wr):
        return wr[1]
    else:
        return 10000000


def GetWRName(map, style, type):
    wr = mysql.query.fetchone(
        "SELECT steamid, time, id FROM completed_personal WHERE map='%s' AND style='%s' AND type='%s' AND season='%s' ORDER BY time ASC",
        (map, style, type, c_season))
    if bool(wr):
        return wr[1]
    else:
        return 10000000


def GetWRPosition(map, style, type, pos):
    index = 0
    wr = mysql.query.fetchall(
        "SELECT steamid, time, id FROM completed_personal WHERE map='%s' AND style='%s' AND type='%s' AND season='%s' ORDER BY time ASC",
        (map, style, type, c_season))
    if bool(wr):
        for object in wr:
            if index == pos:
                return [True, wr[0], wr[1], wr[2]]
            index += 1

    else:
        return [False, False, False, False]

    if index < pos:
        return [False, False, False, False]


def GetRecordExists(steamid, map, type, personal=False):
    index = 0
    if not personal:
        records = mysql.query.fetchone(
            "SELECT id, map, steamid, steamid_partner FROM completed WHERE (steamid='%s' OR steamid_partner='%s') AND map='%s' AND type='%s' AND season=%i ORDER BY ASC",
            (steamid, steamid, map, type, c_season))
        if bool(records):
            for pos in records:
                SetRankedPoints(pos[0], pos[1], steamid, type)


def UpdateRankedPoints(steamid, personal=False):
    points = 0
    records = mysql.query.fetchall(
        "SELECT map, points FROM completed WHERE season=%i AND (steamid='%s' OR steamid_partner='%s') ORDER BY time ASC",
        (c_season, steamid, steamid))
    for object in records:
        points += object[1]
    mysql.query.execute("UPDATE stats SET points='%s' WHERE steamid='%s'", (points, steamid))


def UpdateRankedPointsAll(personal=False):
    TSQL.Query.fetchall("SELECT steamid FROM stats", callback=UpdateRankedPointsAll_Step_1)
    esc.msg('#100,100,100[Timer] #snowRanks are being updated!')


def UpdateRankedPointsAll_Step_1(data):
    for steamid in data:
        points = 0
        map = ""
        style = ""

        data_pack = {'steamid': steamid}
        TSQL.Query.fetchall(
            "SELECT map, points, style FROM completed WHERE season=%i AND (steamid='%s' OR steamid_partner='%s') ORDER BY map, time ASC",
            args=(c_season, steamid[0], steamid[0]), callback=UpdateRankedPointsAll_Step_2, data_pack=data_pack)


def UpdateRankedPointsAll_Step_2(data, data_pack):
    points = 0
    map = ""
    style = ""
    steamid = data_pack['steamid']
    for object in data:
        if not style == object[2] and map == object[0]:
            points += object[1]

        if not map == object[0]:
            points += object[1]
        style = object[2]
        map = object[0]
    TSQL.Query.execute("UPDATE stats SET points='%s' WHERE steamid='%s'", (points, steamid[0]))


def UpdateRanks(personal=False):
    TSQL.Query.fetchall("SELECT id, map, steamid, type FROM completed WHERE season=%i" % c_season,
                        callback=UpdateRanks_Step_1)


def UpdateRanks_Step_1(data):
    records = data
    if bool(records):
        for data in records:
            # Steamid
            SetRankedPoints(data[0], data[1], data[2], data[3])



def SetRankedPoints(id, map, steamid, type, personal=False):
    index = 1
    data_pack = {'id': id, 'map': map, 'steamid': steamid, 'type': type}
    TSQL.Query.fetchall("SELECT id FROM completed) as length FROM completed WHERE map='%s' AND type='%s' AND season=%i ORDER BY time ASC",
                        args=(map, type, c_season), callback=SetRankedPoints_Step_1, data_pack=data_pack)



def SetRankedPoints_Step_1(ranked_position, data_pack):
    index = 1
    id = data_pack['id']
    map = data_pack['map']
    type = data_pack['type']
    if bool(ranked_position):
        for pos in ranked_position:
            if str(pos[0]) == str(id):
                data_pack = {'index': index, 'id': id, 'map': map, 'type': type}
                TSQL.Query.fetchall("SELECT name, points FROM zones WHERE map='%s' AND type='timer'",
                                    args=(map,), callback=SetRankedPoints_Step_2, data_pack=data_pack)

            index += 1



def SetRankedPoints_Step_2(points, data_pack):
    index = data_pack['index']
    type = data_pack['type']
    id = data_pack['id']
    for object in points:
        if object[0] == type:
            points_result = int((index ** -0.5) * 75) + int(object[1]) - index
            TSQL.Query.execute("UPDATE completed SET points='%s' WHERE id=%i", (points_result, id))






def EndZone(userid):
    if es.exists("userid", userid):
        steamid = es.getplayersteamid(userid)
        name = es.getplayername(userid)
        id = str(player[steamid]['id'])
        timer_id = player[steamid]["timer_id"]
        player[steamid]["zone"] = "end"
        velocity = round(vector((float(es.getplayerprop(userid, 'CBasePlayer.localdata.m_vecVelocity[0]')),
                                 float(es.getplayerprop(userid, 'CBasePlayer.localdata.m_vecVelocity[1]')),
                                 float(es.getplayerprop(userid, 'CBasePlayer.localdata.m_vecVelocity[2]')))).length(),
                         2)

        country = iptocountry.get_country(playerlib.getPlayer(userid).address.split(':')[0])[0]

        if zones[id]['type'] == "timer":
            if timer[steamid]["state"] == 2:
                if timer[steamid]['id'] == id:
                    finish_time = (time.time() - timer[steamid]['time'])
                    WR = GetWRPersonal(str(current_map), timer[steamid]['style'], zones[timer[steamid]['id']]['name'])

                    data = mysql.query.fetchone(
                        "SELECT time, steamid, id FROM completed_personal WHERE steamid='%s' AND map='%s' AND style='%s' AND type='%s' AND season=%i",
                        (steamid, str(current_map), timer[steamid]['style'], zones[timer[steamid]['id']]['name'],
                         c_season))

                    if finish_time < WR:
                        esc.msg('#255,0,0NEW %s TOP 1 TIME' % zones[timer[steamid]['id']]['name'])
                        es.cexec_all('play bot/and_thats_how_its_done.wav')

                    else:
                        es.cexec_all('play %s' % random.choice(sounds))

                    if bool(data):
                        if data[0] > finish_time:
                            esc.tell(userid,
                                     '#255,0,0#255,51,0[#0,137,255 Timer #255,51,0] #snowPersonal time improved by #245,61,0%s' % (
                                         TimeFormat(data[0] - finish_time)))
                            mysql.query.execute(
                                "UPDATE completed_personal SET map='%s', steamid='%s', name='%s', country='%s', style='%s', type='%s', time=%f, jumps=%i, flashbangs=%i, date=CURRENT_TIMESTAMP WHERE steamid='%s' AND map='%s' AND style='%s' AND type='%s' AND season=%i",
                                (
                                    str(current_map), steamid, name, country, timer[steamid]['style'],
                                    zones[timer[steamid]['id']]['name'], finish_time, timer[steamid]['jumps'],
                                    timer[steamid]['flashbangs'], steamid, str(current_map), timer[steamid]['style'],
                                    zones[timer[steamid]['id']]['name'], c_season))

                        else:
                            esc.tell(userid,
                                     '#255,0,0#255,51,0[#0,137,255 Timer #255,51,0] #snowNo new personal time...')



                    else:
                        esc.tell(userid,
                                 '#255,0,0#255,51,0[#0,137,255 Timer #255,51,0] #snowYou got %s points for completing it for the first time!' % (
                                     zones[timer[steamid]['id']]['points']))

                        mysql.query.execute("UPDATE stats SET points = points + %i WHERE steamid='%s'",
                                            (zones[timer[steamid]['id']]['points'], steamid))

                        mysql.query.execute(
                            "INSERT INTO completed_personal (map, steamid, name, country, style, type, time, jumps, flashbangs, date, points, season) VALUES ('%s', '%s', '%s', '%s', '%s', '%s', %f, %i, %i, CURRENT_TIMESTAMP, %i, %i)" %
                            (str(current_map), steamid, name, country, timer[steamid]['style'],
                             zones[timer[steamid]['id']]['name'], finish_time, timer[steamid]['jumps'],
                             timer[steamid]['flashbangs'], 0, c_season))

                    if finish_time >= WR:
                        esc.msg(
                            '#255,51,0[#0,137,255 Timer #255,51,0] #245,61,0%s #snowhas completed #245,61,0%s Timer #snowin #245,61,0%s #snow- (SOLO) / (%s) - #tomato(WR +%s)!' % (
                                name, zones[timer[steamid]['id']]['name'], TimeFormat(finish_time),
                                timer[steamid]['style'],
                                TimeFormat(finish_time - WR)))
                    else:
                        esc.msg(
                            '#255,51,0[#0,137,255 Timer #255,51,0] #245,61,0%s #snowhas completed #245,61,0%s Timer #snowin #245,61,0%s #snow- (SOLO) / (%s) - #tomato(NEW WR)!' % (
                                name, zones[timer[steamid]['id']]['name'], TimeFormat(finish_time),
                                timer[steamid]['style']))

                    TimerSolo_Stop(userid)
                    TimerPartner_Stop(userid)
                elif not CheckPartner(userid):
                    hudhint(userid, '(%s)\n \nYou are in the wrong end zone!\nDont worry you still have timer!' % (
                        TimeFormat(float(time.time()) - float(timer[timer_id]['time']))))



            elif CheckPartner(userid) and timer[timer_id]["state"] == 2:
                partner = player[steamid]["partner"]
                userid_partner = player[steamid]["partner"]
                country_partner = iptocountry.get_country(playerlib.getPlayer(partner).address.split(':')[0])[0]
                steamid_partner = es.getplayersteamid(partner)
                name_partner = es.getplayername(partner)
                if timer[timer_id]["id"] == id:
                    finish_time = (time.time() - timer[timer_id]['time'])
                    WR = GetWRPersonal(str(current_map), timer[timer_id]['style'], zones[timer[timer_id]['id']]['name'])

                    if finish_time < WR:
                        if zones[timer[timer_id]['id']]['name'] == "Map" and timer[timer_id]['style'] == "Normal":
                            # if tournament["status"] == 1:
                            es.server.queuecmd('es_sexec %s sm_record.stop 14 0 %s 1' % (userid, finish_time))
                            es.server.queuecmd('es_sexec %s sm_record.stop 14 1 %s 1' % (userid_partner, finish_time))

                        esc.msg('#255,0,0NEW %s TOP 1 TIME' % zones[timer[timer_id]['id']]['name'])
                        for q in es.getUseridList():
                            es.playsound(q, 'trikz_cafe/t3_tournament.mp3', 1.0)
                    else:
                        es.cexec_all('play %s' % random.choice(sounds))

                    """ PERSONAL UPDATE """
                    data = mysql.query.fetchone(
                        "SELECT time, steamid, id FROM completed_personal WHERE steamid='%s' AND map='%s' AND style='%s' AND type='%s' AND season=%s",
                        (steamid, str(current_map), timer[timer_id]['style'], zones[timer[timer_id]['id']]['name'],
                         c_season))

                    if bool(data):
                        if data[0] > finish_time:
                            esc.tell(userid,
                                     '#255,0,0#255,51,0[#0,137,255 Timer #255,51,0] #snowPersonal time improved by #245,61,0%s' % (
                                         TimeFormat(data[0] - finish_time)))
                            mysql.query.execute(
                                "UPDATE completed_personal SET map='%s', steamid='%s', name='%s', country='%s', style='%s', type='%s', time=%f, jumps=%i, flashbangs=%i, date=CURRENT_TIMESTAMP WHERE steamid='%s' AND map='%s' AND style='%s' AND type='%s' AND season=%i" %
                                (
                                    str(current_map), steamid, name, country, timer[timer_id]['style'],
                                    zones[timer[timer_id]['id']]['name'], finish_time, timer[timer_id]['jumps'],
                                    timer[timer_id]['flashbangs'], steamid, str(current_map), timer[timer_id]['style'],
                                    zones[timer[timer_id]['id']]['name'], c_season))

                        else:
                            esc.tell(userid,
                                     '#255,0,0#255,51,0[#0,137,255 Timer #255,51,0] #snowNo new personal time...')



                    else:
                        esc.tell(userid,
                                 '#255,0,0#255,51,0[#0,137,255 Timer #255,51,0] #snowYou got %s points for completing it for the first time!' % (
                                     zones[timer[timer_id]['id']]['points']))
                        mysql.query.execute("UPDATE stats SET points=points + ? WHERE steamid='%s'",
                                            (zones[timer[timer_id]['id']]['points'], steamid))

                        mysql.query.execute(
                            "INSERT INTO completed_personal (map, steamid, name, country, style, type, time, jumps, flashbangs, date, points, season) VALUES ('%s', '%s', '%s', '%s', '%s', '%s', %f, %i, %i, CURRENT_TIMESTAMP, %i, %i)" %
                            (
                                str(current_map), steamid, name, country, timer[timer_id]['style'],
                                zones[timer[timer_id]['id']]['name'], finish_time, timer[timer_id]['jumps'],
                                timer[timer_id]['flashbangs'], 0, c_season))

                    """ PARTNER UPDATE """
                    data = mysql.query.fetchone(
                        "SELECT time, steamid, id FROM completed_personal WHERE steamid='%s' AND map='%s' AND style='%s' AND type='%s'",
                        (steamid_partner, str(current_map), timer[timer_id]['style'],
                         zones[timer[timer_id]['id']]['name']))

                    if bool(data):
                        if data[0] > finish_time:
                            esc.tell(partner,
                                     '#255,0,0#255,51,0[#0,137,255 Timer #255,51,0] #snowPersonal time improved by #245,61,0%s' % (
                                         TimeFormat(data[0] - finish_time)))
                            mysql.query.execute(
                                "UPDATE completed_personal SET map='%s', steamid='%s', name='%s', country='%s', style='%s', type='%s', time=%f, jumps=%i, flashbangs=%i, date=CURRENT_TIMESTAMP WHERE steamid='%s' AND map='%s' AND style='%s' AND type='%s' AND season=%i",
                                (
                                    str(current_map), steamid_partner, name_partner, country_partner,
                                    timer[timer_id]['style'], zones[timer[timer_id]['id']]['name'], finish_time,
                                    timer[timer_id]['jumps'], timer[timer_id]['flashbangs'], steamid_partner,
                                    str(current_map), timer[timer_id]['style'], zones[timer[timer_id]['id']]['name'],
                                    c_season))

                        else:
                            esc.tell(partner,
                                     '#255,0,0#255,51,0[#0,137,255 Timer #255,51,0] #snowNo new personal time...')



                    else:
                        esc.tell(partner,
                                 '#255,0,0#255,51,0[#0,137,255 Timer #255,51,0] #snowYou got %s points for completing it for the first time!' % (
                                     zones[timer[timer_id]['id']]['points']))
                        mysql.query.execute("UPDATE stats SET points=points + ? WHERE steamid='%s'",
                                            (zones[timer[timer_id]['id']]['points'], steamid_partner))

                        mysql.query.execute(
                            "INSERT INTO completed_personal (map, steamid, name, country, style, type, time, jumps, flashbangs, date, points, season) VALUES ('%s', '%s', '%s', '%s', '%s', '%s', %f, %i, %i, CURRENT_TIMESTAMP, %i, %i)" %
                            (
                                str(current_map), steamid_partner, name_partner, country_partner,
                                timer[timer_id]['style'],
                                zones[timer[timer_id]['id']]['name'], finish_time, timer[timer_id]['jumps'],
                                timer[timer_id]['flashbangs'], 0, c_season))

                    """ DATA TO COMPLETED """

                    check = mysql.query.fetchone(
                        "SELECT steamid, steamid_partner, time, id FROM completed WHERE steamid='%s' AND steamid_partner='%s' AND style='%s' AND type='%s' AND map='%s' AND season=%s",
                        (
                            steamid_partner, steamid, timer[timer_id]['style'], zones[timer[timer_id]['id']]['name'],
                            str(current_map), c_season))

                    if not bool(check):
                        check = mysql.query.fetchone(
                            "SELECT steamid, steamid_partner, time, id FROM completed WHERE steamid='%s' AND steamid_partner='%s' AND style='%s' AND type='%s' AND map='%s' AND season=%s",
                            (
                                steamid, steamid_partner, timer[timer_id]['style'],
                                zones[timer[timer_id]['id']]['name'],
                                str(current_map), c_season))

                    if bool(check):
                        if check[2] > finish_time:
                            esc.tell(userid,
                                     "#pinkTeam record improved by #245,0,61%s!" % (
                                     TimeFormat((check[2] - finish_time))))
                            esc.tell(partner,
                                     "#pinkTeam record improved by #245,0,61%s!" % (
                                     TimeFormat((check[2] - finish_time))))
                            mysql.query.execute(
                                "UPDATE completed SET map='%s', name='%s', name_partner='%s', country='%s', country_partner='%s', style='%s', type='%s', time=%f, jumps=%i, flashbangs=%i, date=CURRENT_TIMESTAMP WHERE id=%i AND season=%i",
                                (
                                    str(current_map), name, name_partner, country, country_partner,
                                    timer[timer_id]["style"], zones[timer[timer_id]['id']]['name'],
                                    finish_time, timer[timer_id]["jumps"], timer[timer_id]["flashbangs"], check[3],
                                    c_season))
                        else:
                            esc.tell(userid, "#pinkNo new team record...")
                            esc.tell(partner, "#pinkNo new team record...")


                    else:
                        esc.tell(userid, "#pinkThis is your first team record with %s" % (es.getplayername(partner)))
                        esc.tell(partner, "#pinkThis is your first team record with %s" % (es.getplayername(userid)))
                        mysql.query.execute(
                            "INSERT INTO completed (map, steamid, steamid_partner, name, name_partner, country, country_partner, style, type, time, jumps, flashbangs, date, points, season) VALUES ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', %f, %i, %i, CURRENT_TIMESTAMP, %i, %i)" %
                            (
                                str(current_map), steamid, steamid_partner, name, name_partner, country,
                                country_partner,
                                timer[timer_id]["style"], zones[timer[timer_id]['id']]['name'],
                                finish_time, timer[timer_id]["jumps"], timer[timer_id]["flashbangs"], 0, c_season))

                    if finish_time >= WR:
                        esc.msg(
                            '#255,51,0[#0,137,255 Timer #255,51,0] #245,61,0%s #snow #snowand #245,61,0%s #snowhas completed #245,61,0%s #snowin #245,61,0%s #snow- (PARTNERED) / (%s) - #tomato(WR +%s)!' % (
                                name, name_partner, zones[timer[timer_id]['id']]['name'], TimeFormat(finish_time),
                                timer[timer_id]['style'], TimeFormat(finish_time - WR)))
                    else:
                        esc.msg(
                            '#255,51,0[#0,137,255 Timer #255,51,0] #245,61,0%s #snow #snowand #245,61,0%s #snowhas completed #245,61,0%s #snowin #245,61,0%s #snow- (PARTNERED) / (%s) - #tomato(NEW WR)!' % (
                                name, name_partner, zones[timer[timer_id]['id']]['name'], TimeFormat(finish_time),
                                timer[timer_id]['style']))

                    TimerPartner_Stop(userid)
                    TimerSolo_Stop(userid)
                    UpdateRanks()
                    gamethread.delayed(30, UpdateRankedPointsAll)
                    esc.msg('#255,0,0Updating ranks...')

                elif CheckPartner(userid):
                    hudhint(userid, '(%s)\n \nYou are in the wrong end zone!\nDont worry you still have timer!' % (
                        TimeFormat(float(time.time()) - float(timer[timer_id]['time']))))


            else:
                hudhint(userid, 'You are in the end area..')



        else:
            return


def TimeLeft(time, tick):
    global timeleft
    tick += 1
    time = int(time)
    if tick == 60:
        time -= 1
        tick = 0

    if time == 0:
        timeleft = "Map ended!"
        return

    timeleft = time

    gamethread.delayedname(1, "timeleft", TimeLeft, args=(time, tick))


def GetPersonalWR(steamid, style, map, type):
    p_time = mysql.query.fetchone(
        "SELECT time, id FROM completed_personal WHERE steamid='%s' AND map='%s' AND style='%s' AND type='%s' AND season=%s",
        (steamid, map, style, type, c_season))
    if bool(p_time):
        return (p_time[0])
    else:
        return (0)


def GetWRName2(steamid, style, map, type, personal=False):
    if personal:
        data = mysql.query.fetchone(
            "SELECT name FROM completed_personal WHERE map='%s' AND style='%s' AND type='%s' ORDER BY time ASC",
            (map, style, type))
    else:
        data = mysql.query.fetchone(
            "SELECT name, name_partner FROM completed WHERE map='%s' AND style='%s' AND type='%s' AND season=%s ORDER BY time ASC",
            (map, style, type, c_season))

    if bool(data):
        if personal:
            return (data[0])
        else:
            return ([data[0], data[1]])
    else:
        return 0


def CreateTimer_save():
    # esc.msg('#255,0,0Server database updated...')
    mysql.query.save()
    gamethread.delayedname(5, "save", CreateTimer_save)


def CreateTimer_keyhint(userid):
    steamid = es.getplayersteamid(userid)
    ply = playerlib.getPlayer(userid)

    if steamid in player and not ply.isdead:

        if tournament["status"] == 0:
            if player[steamid]['disabled_keyhint'] == 0:

                player[steamid]["keyhint_display"] = ""
                string = player[steamid]["keyhint_display"]

                if player[steamid]["id"] in zones:
                    if zones[str(player[steamid]["id"])]['type'] == "timer":
                        string += "- %s Timer -" % zones[player[steamid]["id"]]["name"]

                        if zones[player[steamid]["id"]]["partner_needed"] == 1:

                            string += "\nChallenge: Partnered"
                        else:
                            string += "\nChallenge: Solo"
                        if GetPersonalWR(steamid, "Normal", str(current_map),
                                         zones[player[steamid]["id"]]["name"]) != 0:
                            string += "\n\n\nPersonal best: %s" % TimeFormat(
                                GetPersonalWR(steamid, "Normal", str(current_map),
                                              zones[player[steamid]["id"]]["name"]))
                        else:
                            string += "\n\nPersonal best: None"

                        if zones[player[steamid]["id"]]["partner_needed"] == 1:
                            WrName = GetWRName2(steamid, "Normal", str(current_map),
                                                zones[player[steamid]["id"]]["name"])
                            if WrName != 0:
                                string += "\n\nWR: %s and %s" % (WrName[0], WrName[1])
                            else:
                                string += "\n\nWR: "

                            WrName = GetWRName2(steamid, "Sideways", str(current_map),
                                                zones[player[steamid]["id"]]["name"])
                            if WrName != 0:
                                string += "\nSW: %s and %s" % (WrName[0], WrName[1])
                            else:
                                string += "\nSW: "

                            WrName = GetWRName2(steamid, "Half-Sideways", str(current_map),
                                                zones[player[steamid]["id"]]["name"])
                            if WrName != 0:
                                string += "\nHSW: %s and %s" % (WrName[0], WrName[1])
                            else:
                                string += "\nHSW: "

                            WrName = GetWRName2(steamid, "W-Only", str(current_map),
                                                zones[player[steamid]["id"]]["name"])
                            if WrName != 0:
                                string += "\nW-Only: %s and %s" % (WrName[0], WrName[1])
                            else:
                                string += "\nW-Only: "

                        elif zones[player[steamid]["id"]]["partner_needed"] == 0:

                            WrName = GetWRName2(steamid, "Normal", str(current_map),
                                                zones[player[steamid]["id"]]["name"], True)
                            if WrName != 0:
                                string += "\n\nWR: %s" % WrName
                            else:
                                string += "\n\nWR: "

                            WrName = GetWRName2(steamid, "Sideways", str(current_map),
                                                zones[player[steamid]["id"]]["name"], True)
                            if WrName != 0:
                                string += "\nSW: %s" % WrName
                            else:
                                string += "\nSW: "

                            WrName = GetWRName2(steamid, "Half-Sideways", str(current_map),
                                                zones[player[steamid]["id"]]["name"], True)
                            if WrName != 0:
                                string += "\nHSW: %s" % WrName
                            else:
                                string += "\nHSW: "

                            WrName = GetWRName2(steamid, "W-Only", str(current_map),
                                                zones[player[steamid]["id"]]["name"], True)
                            if WrName != 0:
                                string += "\nW-Only: %s" % WrName
                            else:
                                string += "\nW-Only: "
                        else:
                            string += "\nType !r or !b to begin challenge"

                string += "\n \nSpecs: %s" % len(player[steamid]['spectators'])

                name_list = " "

                if len(player[steamid]['spectators']) > 0:
                    for object in player[steamid]['spectators']:
                        s_name = str(es.getplayername(object))
                        if len(s_name) > 12:
                            s_name = str(es.getplayername(object))[0:12] + "..."
                        name_list += "\n" + s_name

                string += name_list

                keyhint(userid, string)



            else:
                ply = playerlib.getPlayer(userid)
                if steamid in player and not ply.isdead:
                    if player[steamid]['disabled_keyhint'] == 2:
                        player[steamid]["keyhint_display"] = ""
                        string = player[steamid]["keyhint_display"]
                        string += "\n \nSpecs: %s" % len(player[steamid]['spectators'])
                        name_list = " "
                        if len(player[steamid]['spectators']) > 0:
                            for object in player[steamid]['spectators']:
                                s_name = str(es.getplayername(object))
                                if len(s_name) > 12:
                                    s_name = str(es.getplayername(object))[0:12] + "..."
                                name_list += "\n" + s_name

                        string += name_list

                        keyhint(userid, string)
                else:
                    keyhint(userid, "Not validated, try rejoining!")



        else:
            player[steamid]["keyhint_display"] = ""
            string = player[steamid]["keyhint_display"]

            string += "-- Tournament Mode --\n "
            turn = tournament["turn"]
            if turn in tournament["queue"]:
                string += "\n %s | %s is playing..\n \n Next couple in: %s \n \n \n" % (
                    tournament["queue"][turn][0]["name"], tournament["queue"][turn][1]["name"],
                    TimeFormat(tournament["time"], None, True))
            else:
                string += "\nNo teams available yet!\n \n \n"

            if player[steamid]["id"] in zones:
                if zones[str(player[steamid]["id"])]['type'] == "timer":
                    string += "- %s Timer -" % zones[player[steamid]["id"]]["name"]

                    if zones[player[steamid]["id"]]["partner_needed"] == 1:

                        string += "\nChallenge: Partnered"
                    else:
                        string += "\nChallenge: Solo"
                    if GetPersonalWR(steamid, "Tournament", str(current_map),
                                     zones[player[steamid]["id"]]["name"]) != 0:
                        string += "\n\n\nPersonal best: %s" % TimeFormat(
                            GetPersonalWR(steamid, "Tournament", str(current_map),
                                          zones[player[steamid]["id"]]["name"]))
                    else:
                        string += "\n\nPersonal best: None"

                    if zones[player[steamid]["id"]]["partner_needed"] == 1:
                        WrName = GetWRName2(steamid, "Tournament", str(current_map),
                                            zones[player[steamid]["id"]]["name"])
                        if WrName != 0:
                            string += "\n\nWR: %s and %s" % (WrName[0], WrName[1])
                        else:
                            string += "\n\nWR: "

                    elif zones[player[steamid]["id"]]["partner_needed"] == 0:

                        WrName = GetWRName2(steamid, "Tournament", str(current_map),
                                            zones[player[steamid]["id"]]["name"], True)
                        if WrName != 0:
                            string += "\n\nWR: %s" % WrName
                        else:
                            string += "\n\nWR: "
                    else:
                        string += "\nType !r or !b to begin challenge"

            string += "\n \nSpecs: %s" % len(player[steamid]['spectators'])

            name_list = " "

            if len(player[steamid]['spectators']) > 0:
                for object in player[steamid]['spectators']:
                    s_name = str(es.getplayername(object))
                    if len(s_name) > 12:
                        s_name = str(es.getplayername(object))[0:12] + "..."
                    name_list += "\n" + s_name

            string += name_list

            keyhint(userid, string)

    gamethread.delayedname(3, "keyhint_%s" % userid, CreateTimer_keyhint, args=(userid))


def FormatZone(type):
    return "%s,%s,%s" % (str(type[0]), str(type[1]), str(type[2]))


def es_map_start(ev):
    current_map = es.ServerVar('eventscripts_currentmap')
    var_timeleft = es.ServerVar('mp_timelimit')
    gamethread.cancelDelayed("timeleft")
    TimeLeft(var_timeleft, 0)
    mysql.query.save()
    clear_cache()
    load_zones(str(current_map))
    save_client_pref()
    es.server.cmd('exec reloader.cfg')


def sm2es_keyPress(ev):
    userid = ev["userid"]
    if es.exists("userid", userid):

        if ev['status'] == '0':
            return

        ply = playerlib.getPlayer(userid)

        if ply.isdead:
            return

        velocity_x = float(es.getplayerprop(userid, 'CBasePlayer.localdata.m_vecVelocity[0]'))
        velocity_y = float(es.getplayerprop(userid, 'CBasePlayer.localdata.m_vecVelocity[1]'))
        steamid = es.getplayersteamid(userid)

        id = player[steamid]["timer_id"]

        if id in timer and CheckPartner(userid):
            if timer[id]["style"] == "Sideways":
                if ev["command"] in ('IN_MOVELEFT', 'IN_MOVERIGHT'):
                    if not ply.onGround():
                        myNewVector = es.createvectorstring(velocity_x, velocity_y, 0)
                        myNewVector2 = es.createvectorstring(-velocity_x, -velocity_y, 0)

                        es.setplayerprop(userid, "CBasePlayer.localdata.m_vecBaseVelocity", myNewVector)
                        es.setplayerprop(userid, "CBasePlayer.localdata.m_vecBaseVelocity", myNewVector2)

            if timer[id]["style"] == "W-Only":
                if ev["command"] in ('IN_MOVELEFT', 'IN_MOVERIGHT', 'IN_BACK'):
                    if not ply.onGround():
                        myNewVector = es.createvectorstring(velocity_x, velocity_y, 0)
                        myNewVector2 = es.createvectorstring(-velocity_x, -velocity_y, 0)

                        es.setplayerprop(userid, "CBasePlayer.localdata.m_vecBaseVelocity", myNewVector)
                        es.setplayerprop(userid, "CBasePlayer.localdata.m_vecBaseVelocity", myNewVector2)

            if timer[id]["style"] == "Backwards":
                if ev["command"] in ('IN_MOVELEFT', 'IN_MOVERIGHT', 'IN_FORWARD'):
                    if not ply.onGround():
                        myNewVector = es.createvectorstring(velocity_x, velocity_y, 0)
                        myNewVector2 = es.createvectorstring(-velocity_x, -velocity_y, 0)

                        es.setplayerprop(userid, "CBasePlayer.localdata.m_vecBaseVelocity", myNewVector)
                        es.setplayerprop(userid, "CBasePlayer.localdata.m_vecBaseVelocity", myNewVector2)

            if timer[player[steamid]["timer_id"]]["state"] == 2:
                if ev["command"] in ("IN_MOVELEFT", "IN_MOVERIGHT") and not ply.onGround():
                    timer[player[steamid]["timer_id"]]["strafes"] += 1



        elif steamid in timer and not CheckPartner(userid):
            if timer[steamid]["style"] == "Sideways":
                if ev["command"] in ('IN_MOVELEFT', 'IN_MOVERIGHT'):
                    if not ply.onGround():
                        myNewVector = es.createvectorstring(velocity_x, velocity_y, 0)
                        myNewVector2 = es.createvectorstring(-velocity_x, -velocity_y, 0)

                        es.setplayerprop(userid, "CBasePlayer.localdata.m_vecBaseVelocity", myNewVector)
                        es.setplayerprop(userid, "CBasePlayer.localdata.m_vecBaseVelocity", myNewVector2)

            if timer[steamid]["style"] == "W-Only":
                if ev["command"] in ('IN_MOVELEFT', 'IN_MOVERIGHT', 'IN_BACK'):
                    if not ply.onGround():
                        myNewVector = es.createvectorstring(velocity_x, velocity_y, 0)
                        myNewVector2 = es.createvectorstring(-velocity_x, -velocity_y, 0)

                        es.setplayerprop(userid, "CBasePlayer.localdata.m_vecBaseVelocity", myNewVector)
                        es.setplayerprop(userid, "CBasePlayer.localdata.m_vecBaseVelocity", myNewVector2)

            if timer[steamid]["style"] == "Backwards":
                if ev["command"] in ('IN_MOVELEFT', 'IN_MOVERIGHT', 'IN_FORWARD'):
                    if not ply.onGround():
                        myNewVector = es.createvectorstring(velocity_x, velocity_y, 0)
                        myNewVector2 = es.createvectorstring(-velocity_x, -velocity_y, 0)
                        es.setplayerprop(userid, "CBasePlayer.localdata.m_vecBaseVelocity", myNewVector)
                        es.setplayerprop(userid, "CBasePlayer.localdata.m_vecBaseVelocity", myNewVector2)

            if timer[steamid]["state"] == 2:
                if ev["command"] in ("IN_MOVELEFT", "IN_MOVERIGHT") and not ply.onGround():
                    timer[steamid]["strafes"] += 1


def player_jump(ev):
    userid = ev["userid"]
    steamid = es.getplayersteamid(userid)
    if CheckPartner(userid):
        if timer[player[steamid]["timer_id"]]["state"] == 2:
            timer[player[steamid]["timer_id"]]["jumps"] += 1

    if steamid in timer:
        if timer[steamid]["state"] == 2:
            timer[steamid]["jumps"] += 1


def weapon_fire(ev):
    userid = ev["userid"]
    steamid = es.getplayersteamid(userid)
    if ev["weapon"] == "flashbang":
        if player[steamid]["timer_id"] in timer:
            if timer[player[steamid]["timer_id"]]["state"] == 2:
                timer[player[steamid]["timer_id"]]["flashbangs"] += 1

        if steamid in timer:
            if timer[steamid]["state"] == 2:
                timer[steamid]["flashbangs"] += 1


def drawbox(userid, loop_number, start_point, type, end_point=None):
    """
    es.precachemodel('materials/sprites/laser.vmt')
    if not end_point:
        effectlib.drawBox(start_point, es.getplayerlocation(userid), model="materials/sprites/laser.vmt", red=255, green=255, blue=255, seconds=0.1)
    else:
        if type == "end":

            effectlib.drawBox(start_point, end_point, model="materials/sprites/laser.vmt", red=255, green=0, blue=0, seconds=0.1)

        elif type == "extra":
            effectlib.drawBox(start_point, end_point, model="materials/sprites/laser.vmt", red=0, green=0, blue=255, seconds=0.1)
        else:

            effectlib.drawBox(start_point, end_point, model="materials/sprites/laser.vmt", red=0, green=255, blue=0, width=12, endwidth=12, seconds=0.2)

    gamethread.delayedname(0.1, 'drawbox_%s' % int(loop_number), drawbox,
                           args=(userid, loop_number, start_point, type, end_point))
    """


class Menu:
    def __init__(self):
        self.type = "none"

    def start_menu(self, userid):
        steamid = es.getplayersteamid(userid)
        if steamid in admins:
            info = popuplib.create('start_menu')
            info.addline('Timer Admin')
            info.addline(' ')
            info.addline('->1. Manage players')
            info.addline('->2. Manage zones')
            info.addline('->3. Noclip')
            info.addline(' ')
            info.addline('0. Exit')
            info.enablekeys = "1234508"
            info.unsend(userid)
            info.send(userid)
            info.delete()
            info.menuselect = self.start_menu_select
        else:
            esc.tell(userid,
                     '#255,51,0[#0,137,255 Timer #255,51,0] #snowYou are not authorized to run this #yellowcommand!')

    def start_menu_select(self, userid, choice, popupid):
        if int(choice) == 2:
            Menu.zones_menu(userid)

    def zones_menu(self, userid):
        info = popuplib.create('zones_menu')
        info.addline('Timer Admin')
        info.addline(':: Zones Management')
        info.addline('Map: %s' % str(current_map))
        info.addline('->1. Create a category')
        info.addline('->2. Delete zones')
        info.addline('->3. Modify zones')
        info.addline(' ')
        info.addline(' ')
        info.addline(' ')
        info.addline(' ')
        info.addline(' ')
        info.addline('->8. Back')
        info.addline('0. Exit')
        info.enablekeys = "123456708"
        info.unsend(userid)
        info.send(userid)
        info.delete()
        info.menuselect = self.zones_menu_select

    def zones_menu_select(self, userid, choice, popupid):
        if int(choice) == 1:
            esc.tell(userid,
                     "#255,51,0[#0,137,255 Timer #255,51,0] #snowPlease type a #245,61,0name #snowfor your catogory! (Use #tomato!tn <name> #snow)")
            auth['vaild'] = es.getplayersteamid(userid)
            auth['id'] = False

        elif int(choice) == 2:
            Menu.zones_delete(userid)

        elif int(choice) == 3:
            Menu.zones_hook_modify(userid)

        elif int(choice) == 8:
            Menu.start_menu(userid)

    def zones_delete(self, userid, limit=None):
        steamid = es.getplayersteamid(userid)
        info = popuplib.easymenu(steamid + 'Delete', None, self.zones_delete_select)
        info.settitle("[ DELETE ] Delete zones for this map")
        info.submenu(10, 'zones_menu')
        info.c_beginsep = " "
        info.c_pagesep = " "
        data = mysql.query.fetchall("SELECT type, name, id FROM zones WHERE map='%s' ORDER BY id", (str(current_map),))
        for item in data:
            info.addoption(item[2], "ID: %s: Name: %s | Type: %s" % (item[2], item[1], item[0]))
        info.send(userid)

    def zones_delete_select(self, userid, choice, popupid):
        mysql.query.execute('DELETE FROM zones WHERE id = %s', (int(choice),))
        gamethread.cancelDelayed('drawbox_%s' % str(choice))
        esc.tell(userid, '#255,51,0[#0,137,255 Timer #255,51,0] #snowYou deleted a zone! ID %s' % choice)
        load_zones(str(current_map))
        Menu.zones_delete(userid)

    def zones_hook_modify(self, userid, limit=None):
        steamid = es.getplayersteamid(userid)
        info = popuplib.easymenu(steamid + 'Hook Modify', None, self.zones_hook_modify_select)
        info.settitle("[ MODIFY ] Modify zones for this map")
        info.submenu(10, 'zones_menu')
        info.c_beginsep = " "
        info.c_pagesep = " "
        data = mysql.query.fetchall("SELECT type, name, id FROM zones WHERE map='%s' ORDER BY id", (str(current_map),))
        for item in data:
            info.addoption(item[2], "ID: %s: Name: %s | Type: %s" % (item[2], item[1], item[0]))
        info.send(userid)

    def zones_hook_modify_select(self, userid, choice, popupid):
        steamid = es.getplayersteamid(userid)
        auth['vaild'] = steamid
        auth['id'] = int(choice)
        Menu.zones_modify(userid, int(choice))
        load_zones(str(current_map))

    def zones_teleport(self, userid, limit=None):
        steamid = es.getplayersteamid(userid)
        info = popuplib.easymenu(steamid + 'Teleport', None, self.zones_teleport_select)
        info.settitle("[ Timer ] Available restart locations")
        info.c_beginsep = "Normal Usage: !r <zone name>\n "
        info.c_pagesep = " "
        for object in sorted(commands, reverse=True):
            if not zones[str(commands[object])]["restart_loc"] == "none":
                if zones[str(commands[object])]["partner_needed"] == 1:
                    info.addoption(commands[object], "%s Timer (Req: partner)" % (object))
                else:
                    info.addoption(commands[object], "%s Timer (Solo)" % (object))

        info.send(userid)

    def zones_teleport_select(self, userid, choice, popupid):
        steamid = es.getplayersteamid(userid)
        restart_location = zones[str(choice)]["restart_loc"]
        es.server.queuecmd(
            'es_setpos %s %s %s %s' % (userid, restart_location[0], restart_location[1], restart_location[2]))
        TimerSolo_Stop(userid)
        TimerPartner_Stop(userid)
        Menu.zones_teleport(userid)

    def zones_modify(self, userid, id):
        load_zones(str(current_map))
        TimerSolo_Stop(userid)
        TimerPartner_Stop(userid)
        data = mysql.query.fetchone("SELECT id, type, name, tier, points, partner_needed FROM zones WHERE id='%s'",
                                    (id,))
        info = popuplib.create('zones_modify')
        info.addline('Timer Admin')
        info.addline(':: Zones Modify')
        info.addline('Map: %s' % str(current_map))
        info.addline(' ')
        info.addline('ID %s | Name: %s' % (str(data[0]), str(data[2])))
        info.addline('Tier: %s' % (str(data[3])))
        info.addline('Points: %s' % (str(data[4])))
        info.addline('Type: %s' % (str(data[1])))
        if data[5] == 0:
            info.addline('Partner Needed: No')
        else:
            info.addline('Partner Needed: Yes')
        info.addline(' ')
        info.addline('->1. Edit Name')
        info.addline('->2. Edit Tier')
        info.addline('->3. Edit Points')
        info.addline('->4. Edit Type')
        info.addline('->5. Edit Partner needed')
        info.addline(' ')
        info.addline('->6. Add Start Zone')
        if data[1] == "timer":
            info.addline('->7. Add End Zone')
        else:
            info.addline('7. Add End Zone ')
            info.addline('Not available for this type')
        info.addline(' ')
        info.addline('->8. Set Teleport Location')
        info.addline(' ')
        info.addline('->9. Back')
        info.addline('0. Exit')
        info.enablekeys = "1234567890"
        info.unsend(userid)
        info.send(userid)
        info.delete()
        info.menuselect = self.zones_modify_select

    def zones_modify_select(self, userid, choice, popupid):
        id = auth['id']
        if int(choice) == 1:
            esc.tell(userid,
                     "#255,51,0[#0,137,255 Timer #255,51,0] #snowPlease type a new #245,61,0name #snowfor your zone! (Use #tomato!tcn <name> #snow)")
            auth['vaild'] = es.getplayersteamid(userid)

        elif int(choice) == 2:
            esc.tell(userid,
                     "#255,51,0[#0,137,255 Timer #255,51,0] #snowPlease type a new number to change #245,61,0tier (Use #tomato!tct <number> #snow)")
            auth['vaild'] = es.getplayersteamid(userid)

        elif int(choice) == 3:
            esc.tell(userid,
                     "#255,51,0[#0,137,255 Timer #255,51,0] #snowPlease type a new number to change #245,61,0points (Use #tomato!tcp <number> #snow)")
            auth['vaild'] = es.getplayersteamid(userid)

        elif int(choice) == 4:
            esc.tell(userid,
                     "#255,51,0[#0,137,255 Timer #255,51,0] #snowWhat should this zone do? If you choose Timer it requires an end zone!")
            Menu.zones_modify_type(userid, auth['id'])
            auth['vaild'] = es.getplayersteamid(userid)


        elif int(choice) == 5:
            data = mysql.query.fetchone("SELECT id, type, name, tier, points, partner_needed FROM zones WHERE id='%s'",
                                        (id,))
            if data[5] == 1:
                mysql.query.execute("UPDATE zones SET partner_needed='%s' WHERE id='%s'", (0, int(auth['id'])))
                esc.tell(userid, "#255,51,0[#0,137,255 Timer #255,51,0] #snowPartner needed is now set to: #245,61,0No")
            else:
                mysql.query.execute("UPDATE zones SET partner_needed='%s' WHERE id='%s'", (1, int(auth['id'])))
                esc.tell(userid,
                         "#255,51,0[#0,137,255 Timer #255,51,0] #snowPartner needed is now set to: #245,61,0Yes")
            Menu.zones_modify(userid, id)
            auth['vaild'] = es.getplayersteamid(userid)

        elif int(choice) == 6:
            Menu.zones_create(userid, id, "start")
            zones["temp_start_%s" % str(id)] = es.getplayerlocation(userid)
            drawbox(userid, str(id), zones["temp_start_%s" % str(id)], "start", None)
            esc.tell(userid, "#255,51,0[#0,137,255 Timer #255,51,0] #snowPlease show the coordinates!")

        elif int(choice) == 7:
            data = mysql.query.fetchone("SELECT id, type, name, tier, points, partner_needed FROM zones WHERE id='%s'",
                                        (id,))
            if data[1] == "timer":
                Menu.zones_create(userid, id, "end")
                zones["temp_end_%s" % str(id)] = es.getplayerlocation(userid)
                drawbox(userid, str(id), zones["temp_end_%s" % str(id)], "end", None)
                esc.tell(userid, "#255,51,0[#0,137,255 Timer #255,51,0] #snowPlease show the coordinates!")
            else:
                esc.tell(userid, "#255,51,0[#0,137,255 Timer #255,51,0] #snowPlease change zone type!")
                Menu.zones_modify(userid, id)

        elif int(choice) == 8:
            esc.tell(userid,
                     "#255,51,0[#0,137,255 Timer #255,51,0] #snowYou have now added teleport location for this zone")
            mysql.query.execute("UPDATE zones SET restart_loc='%s' WHERE id='%s'",
                                (FormatZone(es.getplayerlocation(userid)), id))
            load_zones(current_map)
            Menu.zones_modify(userid, id)

        elif int(choice) == 9:
            Menu.zones_menu(userid)

    def zones_create(self, userid, id, case):
        zones['case'] = case
        info = popuplib.create('zones_create')
        info.addline('| Timer Management |')
        info.addline('Adding zone for ID: %s' % id)
        info.addline('->1. Save the zone')
        info.addline(' ')
        info.addline(' ')
        info.addline(' ')
        info.addline(' ')
        info.addline(' ')
        info.addline('->8. Back')
        info.enablekeys = "18"
        info.unsend(userid)
        info.send(userid)
        info.delete()
        info.menuselect = self.zones_create_select

    def zones_create_select(self, userid, choice, popupid):
        id = auth['id']
        if int(choice) == 1:
            if zones['case'] == "start":
                esc.tell(userid, '#255,51,0[#0,137,255 Timer #255,51,0] #snowYou added zone coordinates!')
                gamethread.cancelDelayed('drawbox_%s' % str(id))
                drawbox(userid, str(id), zones["temp_start_%s" % str(id)], "start", es.getplayerlocation(userid))
                mysql.query.execute("UPDATE zones SET location_1='%s', location_2='%s' WHERE id='%s'", (
                    FormatZone(zones["temp_start_%s" % str(id)]), FormatZone(es.getplayerlocation(userid)), id))
                load_zones(current_map)
                Menu.zones_modify(userid, id)
            else:
                esc.tell(userid, '#255,51,0[#0,137,255 Timer #255,51,0] #snowYou added zone coordinates!')
                gamethread.cancelDelayed('drawbox_%s' % str(id))
                drawbox(userid, str(id), zones["temp_end_%s" % str(id)], "end", es.getplayerlocation(userid))
                mysql.query.execute("UPDATE zones SET location_3='%s', location_4='%s' WHERE id='%s'", (
                    FormatZone(zones["temp_end_%s" % str(id)]), FormatZone(es.getplayerlocation(userid)), id))
                load_zones(current_map)
                Menu.zones_modify(userid, id)
        elif int(choice) == 8:
            Menu.zones_modify(userid, id)

    def zones_create_command(self, userid, text, steamid, name):
        if auth['vaild']:
            if auth_zones() == "True":
                if auth['vaild'] == steamid:

                    get_len = len(text)
                    mysql.query.execute(
                        "INSERT INTO zones (map, name, tier, points, type, partner_needed, location_1, location_2, location_3, location_4, restart_loc, match_key, comment) VALUES ('%s', '%s', 0, 0, 'none', 0, '0', '0', '0', '0', '0', 0, '0')",
                        (
                            str(current_map), text[4:int(get_len)]))
                    auth['id'] = int(auth_zones())
                    Menu.zones_modify(userid, auth['id'])
                    esc.tell(userid,
                             "#255,51,0[#0,137,255 Timer #255,51,0] #snowYou have a created zone #yellow%s " % text[
                                                                                                               4:int(
                                                                                                                   get_len)])

                else:
                    esc.tell(userid,
                             "#255,51,0[#0,137,255 Timer #255,51,0] #snowA zone is already in progress, you are not authorized to make changes right now")
            else:
                esc.tell(userid,
                         "#255,51,0[#0,137,255 Timer #255,51,0] #snowYou must finish editing this #yellowzone#snow, before creating a new one!")
                auth['id'] = auth_zones()
                Menu.zones_modify(userid, auth['id'])

        else:
            esc.tell(userid,
                     "#255,51,0[#0,137,255 Timer #255,51,0] #snowThere are no #yellowzones#snow is in progress!")

    def zones_points_command(self, userid, text, steamid, name):
        if auth['vaild']:
            if auth['vaild'] == steamid:
                get_len = len(text)
                esc.tell(userid,
                         "#255,51,0[#0,137,255 Timer #255,51,0] #snowYou have changed the points to #yellow#yellow%s " % text[
                                                                                                                         5:int(
                                                                                                                             get_len)])
                mysql.query.execute("UPDATE zones SET points='%s' WHERE id='%s'",
                                    (int(text[5:int(get_len)]), auth['id']))
                Menu.zones_modify(userid, auth['id'])
            else:
                esc.tell(userid,
                         "#255,51,0[#0,137,255 Timer #255,51,0] #snowA zone is already in progress, you are not authorized to make changes right now")

        else:
            esc.tell(userid,
                     "#255,51,0[#0,137,255 Timer #255,51,0] #snowThere are no #yellowzones#snow is in progress!")

    def zones_tier_command(self, userid, text, steamid, name):
        if auth['vaild']:
            if auth['vaild'] == steamid:

                get_len = len(text)
                esc.tell(userid,
                         "#255,51,0[#0,137,255 Timer #255,51,0] #245,0,61You have succesfully changed the tier to #yellow%s " % text[
                                                                                                                                5:int(
                                                                                                                                    get_len)])
                mysql.query.execute("UPDATE zones SET tier='%s' WHERE id='%s'",
                                    (int(text[5:int(get_len)]), auth['id']))
                Menu.zones_modify(userid, auth['id'])
            else:
                esc.tell(userid,
                         "#255,51,0[#0,137,255 Timer #255,51,0] #snowA zone is already in progress, you are not authorized to make changes right now")

        else:
            esc.tell(userid,
                     "#255,51,0[#0,137,255 Timer #255,51,0] #snowThere are no #yellowzones#snow is in progress!")

    def zones_rename_command(self, userid, text, steamid, name):
        if auth['vaild']:
            if auth['vaild'] == steamid:
                get_len = len(text)
                esc.tell(userid,
                         "#255,51,0[#0,137,255 Timer #255,51,0] #245,0,61You have succesfully changed the name to #yellow%s " % text[
                                                                                                                                5:int(
                                                                                                                                    get_len)])
                mysql.query.execute("UPDATE zones SET name='%s' WHERE id='%s'",
                                    (text[5:int(get_len)], str(auth['id'])))
                Menu.zones_modify(userid, auth['id'])

            else:
                esc.tell(userid,
                         "#255,51,0[#0,137,255 Timer #255,51,0] #snowA zone is already in progress, you are not authorized to make changes right now")

        else:
            esc.tell(userid,
                     "#255,51,0[#0,137,255 Timer #255,51,0] #snowThere are no #yellowzones#snow is in progress!")

    def zones_modify_type(self, userid, id):
        auth['id'] = int(id)
        info = popuplib.create('zones_modify_type')
        info.addline('| Timer Management |')
        info.addline(':: Zones Modify')
        info.addline('Change zone type')
        info.addline(' ')
        info.addline('->1. Timer')
        info.addline('->2. Speed')
        info.addline('->3. Stop Timer')
        info.addline('->4. Respawn player')
        info.addline('->5. Allow FlashBot')
        info.addline('->6. No Flash')
        info.addline('->7. Tournament')
        info.addline(' ')
        info.addline('->8. Back')
        info.addline('0. Exit')
        info.enablekeys = "123456708"
        info.unsend(userid)
        info.send(userid)
        info.delete()
        info.menuselect = self.zones_modify_type_select

    def zones_modify_type_select(self, userid, choice, popupid):
        steamid = es.getplayersteamid(userid)
        id = auth['id']
        if int(choice) == 1:
            esc.tell(userid, "#255,51,0[#0,137,255 Timer #255,51,0] #snowYou have succesfully changed the type")
            mysql.query.execute("UPDATE zones SET type='%s' WHERE id='%s'", ("timer", auth['id']))
            Menu.zones_modify(userid, id)

        elif int(choice) == 2:
            esc.tell(userid, "#255,51,0[#0,137,255 Timer #255,51,0] #snowYou have succesfully changed the type")
            mysql.query.execute("UPDATE zones SET type='%s' WHERE id='%s'", ("speed", auth['id']))
            Menu.zones_modify(userid, id)

        elif int(choice) == 3:
            esc.tell(userid, "#255,51,0[#0,137,255 Timer #255,51,0] #snowYou have succesfully changed the type")
            mysql.query.execute("UPDATE zones SET type='%s' WHERE id='%s'", ("cheat", auth['id']))
            Menu.zones_modify(userid, id)

        elif int(choice) == 4:
            esc.tell(userid, "#255,51,0[#0,137,255 Timer #255,51,0] #snowYou have succesfully changed the type")
            mysql.query.execute("UPDATE zones SET type='%s' WHERE id='%s'", ("respawn", auth['id']))
            Menu.zones_modify(userid, id)

        elif int(choice) == 5:
            esc.tell(userid, "#255,51,0[#0,137,255 Timer #255,51,0] #snowYou have succesfully changed the type")
            mysql.query.execute("UPDATE zones SET type='%s' WHERE id='%s'", ("flashbot", auth['id']))
            Menu.zones_modify(userid, id)

        elif int(choice) == 6:
            esc.tell(userid, "#255,51,0[#0,137,255 Timer #255,51,0] #snowYou have succesfully changed the type")
            mysql.query.execute("UPDATE zones SET type='%s' WHERE id='%s'", ("noflash", auth['id']))
            Menu.zones_modify(userid, id)

        elif int(choice) == 7:
            esc.tell(userid, "#255,51,0[#0,137,255 Timer #255,51,0] #snowYou have succesfully changed the type")
            mysql.query.execute("UPDATE zones SET type='%s' WHERE id='%s'", ("tournament", auth['id']))
            Menu.zones_modify(userid, id)

        elif int(choice) == 8:
            Menu.zones_modify(userid, id)

    def partner_menu(self, userid):
        steamid = es.getplayersteamid(userid)
        info = popuplib.easymenu(str(steamid) + 'partner', None, self.partner_menu_select)
        info.settitle("Choose who you wanna partner up with")
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

    def partner_menu_select(self, userid, choice, popupid):
        steamid = es.getplayersteamid(userid)
        steamid_partner = es.getplayersteamid(choice)
        name = es.getplayername(userid)
        player[steamid]["partner"] = choice
        if str(player[steamid_partner]["partner"]) == str(userid):
            TimerPartner_Stop(userid)
            TimerSolo_Stop(userid)
            player[steamid_partner]["timer_id"] = timer_unique()
            player[steamid]["timer_id"] = player[steamid_partner]["timer_id"]
            timer[player[steamid_partner]["timer_id"]] = {'partner_needed': 1,
                                                          'time': time.time(),
                                                          'flashbangs': 0,
                                                          'jumps': 0,
                                                          'strafes': 0,
                                                          'style': "Normal",
                                                          'id': player[steamid]["id"],
                                                          'state': 0}

            esc.tell(userid,
                     '#255,51,0[#0,137,255 Timer #255,51,0] #snowYou are now partnered with %s' % es.getplayername(
                         choice))
            esc.tell(choice, '#255,51,0[#0,137,255 Timer #255,51,0] #snowYou are now partnered with %s' % name)
        else:
            esc.tell(userid,
                     '#255,51,0[#0,137,255 Timer #255,51,0] #snowWaiting for the other player... will select you..')
            esc.tell(choice,
                     '#255,51,0[#0,137,255 Timer #255,51,0] #snow#245,61,0%s #snowwants to partner up with you! Please type !partner and choose him' % (
                         name))

    def zones_object(self, userid):
        steamid = es.getplayersteamid(userid)
        case = player[steamid]["case"]
        info = popuplib.easymenu(steamid + 'Object', None, self.zones_object_select)
        info.settitle("[ Timer ] Available timers to view")
        info.c_beginsep = "Normal Usage: !<command> <zone name>\n "
        info.c_pagesep = " "
        for object in sorted(commands, reverse=True):
            if zones[str(commands[object])]["type"] == "timer":
                if case == "ttop":
                    if zones[str(commands[object])]["partner_needed"] == 1:
                        info.addoption(zones[str(commands[object])]["name"], "%s Timer" % (object))
                elif case == "ptop":
                    info.addoption(zones[str(commands[object])]["name"], "%s Timer" % (object))

        info.send(userid)

    def zones_object_select(self, userid, choice, popupid):
        steamid = es.getplayersteamid(userid)
        case = player[steamid]["case"]

        if case == "ptop":
            Menu.ptop(steamid, userid, choice, "Normal", str(current_map))
        elif case == "ttop":
            Menu.ttop(steamid, userid, choice, "Normal", str(current_map))

    def wrtop(self, steamid, userid, type, style, map_choose, personal=False):
        index = 0
        full_top = popuplib.easymenu(steamid + 'wrtop', None, self.wrtop_select)
        full_top.settitle("Showing %s records\nMap: %s\n%s\nSeason 3" % (type, map_choose, style))
        # full_top.submenu(10, 'Main Guild')
        full_top.c_beginsep = " "
        full_top.c_pagesep = " "
        full_top.enablekeys = "12098"
        full_top.addoption([1, steamid, userid, type, style, map_choose, personal], "View Season 1")
        full_top.addoption([2, steamid, userid, type, style, map_choose, personal], "View Season 2")
        full_top.addoption([3, steamid, userid, type, style, map_choose, personal], "Current Season 3", state=False)
        if personal:
            partner = mysql.query.fetchall(
                "SELECT time, name FROM completed_personal WHERE map='%s' AND type='%s' AND style='%s' AND season='%s' ORDER BY time ASC LIMIT 100",
                (str(map_choose), str(type), str(style), c_season))
            for item in partner:
                index += 1
                full_top.addoption(index, ("#%s: %s - %s" % (index, TimeFormat(float(item[0])), item[1])))
        else:
            partner = mysql.query.fetchall(
                "SELECT time, name, name_partner, points FROM completed WHERE map='%s' AND type='%s' AND style='%s' AND season='%s' ORDER BY time ASC LIMIT 100",
                (str(map_choose), str(type), str(style), c_season))
            for item in partner:
                index += 1
                full_top.addoption(index,
                                   ("#%s: %s - ( %s | %s ) [points: %s]" % (
                                   index, TimeFormat(float(item[0])), item[1], item[2], item[3])))
        full_top.send(userid)

    def wrtop_select(self, userid, choice, popupid):
        Menu.wrtop_season(choice[0], choice[1], choice[2], choice[3], choice[4], choice[5], choice[6])

    """ OLD SEASON """

    def wrtop_season(self, season, steamid, userid, type, style, map_choose, personal=False):
        index = 0
        full_top = popuplib.easymenu(steamid + 'wrtop_season', None, None)
        full_top.settitle(
            "Showing %s records\nMap: %s\n%s\nSeason %s\n- OLD RECRODS -" % (type, map_choose, style, season))
        # full_top.submenu(10, 'Main Guild')
        full_top.c_beginsep = " "
        full_top.c_pagesep = " "
        full_top.enablekeys = "098"
        if personal:
            partner = mysql.query.fetchall(
                "SELECT time, name FROM completed_personal WHERE map='%s' AND type='%s' AND style='%s' AND season='%s' ORDER BY time ASC LIMIT 100",
                (str(map_choose), str(type), str(style), season))
            for item in partner:
                index += 1
                full_top.addoption(index, ("#%s: %s - %s" % (index, TimeFormat(float(item[0])), item[1])))
        else:
            partner = mysql.query.fetchall(
                "SELECT time, name, name_partner, points FROM completed WHERE map='%s' AND type='%s' AND style='%s' AND season='%s' ORDER BY time ASC LIMIT 100",
                (str(map_choose), str(type), str(style), season))
            for item in partner:
                index += 1
                full_top.addoption(index,
                                   ("#%s: %s - ( %s | %s ) [points: %s]" % (
                                   index, TimeFormat(float(item[0])), item[1], item[2], item[3])))
        full_top.send(userid)

    def wrselect(self, steamid, userid, type, style, map_choose, personal=False):
        index = 0
        full_top = popuplib.easymenu(steamid + 'wrselect', None, self.wrselect_select)
        full_top.settitle("%s timer | Select a style \nMap: %s" % (type, map_choose))
        full_top.c_beginsep = " "
        full_top.c_pagesep = " "
        full_top.enablekeys = "0123490"
        data = mysql.query.fetchone("SELECT partner_needed, points FROM zones WHERE map='%s' AND name='%s'",
                                    (map_choose, type))
        if bool(data):
            if int(data[0]) == 0:
                personal = True
        # full_top.addoption([steamid, userid, type, "Tournament", map_choose, personal], "Tournament")
        full_top.addoption([steamid, userid, type, "Normal", map_choose, personal], "Normal")
        full_top.addoption([steamid, userid, type, "Sideways", map_choose, personal], "Sidways")
        full_top.addoption([steamid, userid, type, "Half-Sideways", map_choose, personal], "Half-Sideways")
        full_top.addoption([steamid, userid, type, "W-Only", map_choose, personal], "W-Only")

        full_top.send(userid)

    def wrselect_select(self, userid, choice, popupid):
        Menu.wrtop(choice[0], choice[1], choice[2], choice[3], choice[4], choice[5])

    def bwrselect(self, steamid, userid, type, style, map_choose, personal=False):
        index = 0
        full_top = popuplib.easymenu(steamid + 'bwrselect', None, self.bwrselect_select)
        full_top.settitle("Select a bonus to view\nMap: %s" % (map_choose))
        full_top.c_beginsep = " "
        full_top.c_pagesep = " "
        full_top.enablekeys = "0123490"
        data = mysql.query.fetchall("SELECT name, points FROM zones WHERE map='%s' AND type='timer' ORDER BY name ASC",
                                    (map_choose,))
        if bool(data):
            for item in data:
                if not item[0] == "Map":
                    full_top.addoption([steamid, userid, str(item[0]), None, map_choose, personal], "%s" % str(item[0]))

        full_top.send(userid)

    def bwrselect_select(self, userid, choice, popupid):
        Menu.wrselect(choice[0], choice[1], choice[2], choice[3], choice[4], choice[5])

    def ptop(self, steamid, userid, type, style, map_choose):
        index = 0
        full_top = popuplib.easymenu(steamid + 'Ptop', None, self.ptop_select)
        full_top.settitle("Trikz Timer [Top 100]\n%s (%s Timer, %s)\nSeason %s\nPersonal world records.." % (
        map_choose, type, style, c_season))
        # full_top.submenu(10, 'Main Guild')
        full_top.c_beginsep = " "
        full_top.c_pagesep = " "
        full_top.enablekeys = "12098"
        full_top.addoption([1, steamid, userid, type, style, map_choose], "View Season 1")
        full_top.addoption([2, steamid, userid, type, style, map_choose], "View Season 2")
        full_top.addoption([3, steamid, userid, type, style, map_choose], "Current Season 3", state=False)
        partner = mysql.query.fetchall(
            "SELECT steamid, time, name FROM completed_personal WHERE map='%s' AND type='%s' AND style='%s' AND season='%s' ORDER BY time ASC LIMIT 100",
            (str(map_choose), str(type), str(style), c_season))
        for item in partner:
            index += 1

            full_top.addoption(item[0], ("#%s: %s - %s" % (index, TimeFormat(float(item[1])), item[2])))
        full_top.send(userid)

    def ptop_select(self, userid, choice, popupid):
        Menu.ptop_season(choice[0], choice[1], choice[2], choice[3], choice[4], choice[5], choice[6])

    """ OLD SESAON """

    def ptop_season(self, season, steamid, userid, type, style, map_choose):
        index = 0
        full_top = popuplib.easymenu(steamid + 'Ptop', None, self.ptop_select)
        full_top.settitle(
            "Trikz Timer [Top 100]\n%s (%s Timer, %s)\nSeason %s\nPersonal world records..\n - OLD RECORDS -" % (
            map_choose, type, style, c_season))
        # full_top.submenu(10, 'Main Guild')
        full_top.c_beginsep = " "
        full_top.c_pagesep = " "
        full_top.enablekeys = "098"

        partner = mysql.query.fetchall(
            "SELECT steamid, time, name FROM completed_personal WHERE map='%s' AND type='%s' AND style='%s' AND season='%s' ORDER BY time ASC LIMIT 100",
            (str(map_choose), str(type), str(style), season))
        for item in partner:
            index += 1

            full_top.addoption(item[0], ("#%s: %s - %s " % (index, TimeFormat(float(item[1])), item[2])))
        full_top.send(userid)

    def btop(self, steamid, userid, type, style, map_choose):
        index = 0
        full_top = popuplib.easymenu(steamid + 'btop', None, self.btop_select)
        full_top.settitle(
            "Trikz Timer [Top 100]\n%s (%s Timer, %s)\nPersonal world records.." % (map_choose, type, style))
        # full_top.submenu(10, 'Main Guild')
        full_top.c_beginsep = " "
        full_top.c_pagesep = " "
        full_top.enablekeys = "12098"
        full_top.addoption([1, steamid, userid, type, style, map_choose], "View Season 1")
        full_top.addoption([2, steamid, userid, type, style, map_choose], "View Season 2")
        full_top.addoption([3, steamid, userid, type, style, map_choose], "Current Season 3", state=False)

        partner = mysql.query.fetchall(
            "SELECT steamid, time, name FROM completed_personal WHERE map='%s' AND type='%s' AND style='%s' AND season='%s' ORDER BY time ASC LIMIT 100",
            (str(map_choose), str(type), str(style), c_season))
        for item in partner:
            index += 1

            full_top.addoption(item[0], ("#%s: %s - %s" % (index, TimeFormat(float(item[1])), item[2])))
        full_top.send(userid)

    def btop_select(self, userid, choice, popupid):
        Menu.btop_season(choice[0], choice[1], choice[2], choice[3], choice[4], choice[5], choice[6])

    """ OLD SEASON"""

    def btop_season(self, steamid, userid, type, style, map_choose):
        index = 0
        full_top = popuplib.easymenu(steamid + 'btop', None, self.btop_select)
        full_top.settitle("Trikz Timer [Top 100]\n%s (%s Timer, %s)\nPersonal world records..\n- OLD RECORDS -" % (
        map_choose, type, style))
        # full_top.submenu(10, 'Main Guild')
        full_top.c_beginsep = " "
        full_top.c_pagesep = " "
        full_top.enablekeys = "098"

        partner = mysql.query.fetchall(
            "SELECT steamid, time, name FROM completed_personal WHERE map='%s' AND type='%s' AND style='%s' AND season='%s' ORDER BY time ASC LIMIT 100",
            (str(map_choose), str(type), str(style), c_season))
        for item in partner:
            index += 1

            full_top.addoption(item[0], ("#%s: %s - %s" % (index, TimeFormat(float(item[1])), item[2])))
        full_top.send(userid)

    def top(self, steamid, userid, country=None):
        index = 0
        full_top = popuplib.easymenu(steamid + 'Top', None, None)
        if not country:
            full_top.settitle("Trikz Timer [Top 100]\nShowing points top overall")
        else:
            full_top.settitle("Trikz Timer [Top 100]\nShowing points top in %s" % country)

        # full_top.submenu(10, 'Main Guild')
        full_top.c_beginsep = " "
        full_top.c_pagesep = " "
        full_top.enablekeys = "098"
        if country:
            partner = mysql.query.fetchall(
                "SELECT steamid, name, points FROM stats WHERE country='%s' ORDER BY points DESC LIMIT 100", (country,))
        else:
            partner = mysql.query.fetchall(
                "SELECT steamid, name, points, country FROM stats ORDER BY points DESC LIMIT 100")

        for item in partner:
            index += 1
            if country:
                full_top.addoption(item[0], ("#%s: %s points: - %s" % (index, item[2], item[1])))
            else:
                full_top.addoption(item[0], ("#%s: (%s) %s points: - %s" % (index, item[3], item[2], item[1])))
        full_top.send(userid)

    def mode(self, userid):
        steamid = es.getplayersteamid(userid)
        id = player[steamid]['timer_id']
        info = popuplib.create('timer_mode')
        if id in timer and CheckPartner(userid):
            info.addline('Style - Partner timer')
            if timer[id]["style"] == "Normal":
                info.addline('1. Normal')
            else:
                info.addline('->1. Normal')

            if timer[id]["style"] == "Sideways":
                info.addline('2. Sideways')
            else:
                info.addline('->2. Sideways')

            if timer[id]["style"] == "W-Only":
                info.addline('3. W-Only')
            else:
                info.addline('->3. W-Only')

            if timer[id]["style"] == "Backwards":
                info.addline('4. Backwards')
            else:
                info.addline('->4. Backwards')
            info.addline(' ')
            info.addline(' ')
            info.addline(' ')
            info.addline(' ')
            info.addline('0. Exit')
        else:

            info.addline('Style - Solo timer')
            if timer[steamid]["style"] == "Normal":
                info.addline('1. Normal')
            else:
                info.addline('->1. Normal')

            if timer[steamid]["style"] == "Sideways":
                info.addline('2. Sideways')
            else:
                info.addline('->2. Sideways')

            if timer[steamid]["style"] == "Half-Sideways":
                info.addline('3. Half-Sideways')
            else:
                info.addline('->3. Half-Sideways')

            if timer[steamid]["style"] == "W-Only":
                info.addline('4. W-Only')
            else:
                info.addline('->4. W-Only')
            info.addline(' ')
            info.addline(' ')
            info.addline(' ')
            info.addline(' ')
            info.addline('0. Exit')

        info.enablekeys = "12340"
        info.unsend(userid)
        info.send(userid)
        info.delete()
        info.menuselect = self.mode_select

    def mode_select(self, userid, choice, popupid):
        steamid = es.getplayersteamid(userid)
        name = es.getplayername(userid)
        id = player[steamid]['timer_id']
        if int(choice) == 1:
            if id in timer and CheckPartner(userid):
                if not timer[id]["style"] == "Normal":
                    timer[id]["style"] = "Normal"
                    esc.tell(userid,
                             '#255,51,0[#0,137,255 Timer #255,51,0] #snowYou have changed the mode to #tomatoNormal')
                    esc.tell(player[steamid]["partner"],
                             '#255,51,0[#0,137,255 Timer #255,51,0] #snowYou partner #245,61,0 %s #snowhas recently changed the mode to #tomatoNormal' % (
                                 name))
                    TimerSolo_Stop(userid)
                    TimerPartner_Stop(userid)
            else:
                if not timer[steamid]["style"] == "Normal":
                    timer[steamid]["style"] = "Normal"
                    esc.tell(userid,
                             '#255,51,0[#0,137,255 Timer #255,51,0] #snowYou have changed the mode to #tomatoNormal')
                    TimerSolo_Stop(userid)
                    TimerPartner_Stop(userid)
            Menu.mode(userid)
        elif int(choice) == 2:
            if id in timer and CheckPartner(userid):
                if not timer[id]["style"] == "Sideways":
                    timer[id]["style"] = "Sideways"
                    esc.tell(userid,
                             '#255,51,0[#0,137,255 Timer #255,51,0] #snowYou have changed the mode to #tomatoSideways')
                    esc.tell(player[steamid]["partner"],
                             '#255,51,0[#0,137,255 Timer #255,51,0] #snowYou partner #245,61,0 %s #snowhas recently changed the mode to #tomatoSideways' % (
                                 name))
                    TimerSolo_Stop(userid)
                    TimerPartner_Stop(userid)
            else:
                if not timer[steamid]["style"] == "Sideways":
                    timer[steamid]["style"] = "Sideways"
                    esc.tell(userid,
                             '#255,51,0[#0,137,255 Timer #255,51,0] #snowYou have changed the mode to #tomatoSideways')
                    TimerSolo_Stop(userid)
                    TimerPartner_Stop(userid)
            Menu.mode(userid)

        elif int(choice) == 3:
            if id in timer and CheckPartner(userid):
                if not timer[id]["style"] == "Half-Sideways":
                    timer[id]["style"] = "Half-Sideways"
                    esc.tell(userid,
                             '#255,51,0[#0,137,255 Timer #255,51,0] #snowYou have changed the mode to #tomatoHalf-Sideways')
                    esc.tell(player[steamid]["partner"],
                             '#255,51,0[#0,137,255 Timer #255,51,0] #snowYou partner #245,61,0 %s #snowhas recently changed the mode to #tomatoHalf-Sideways' % (
                                 name))
                    TimerSolo_Stop(userid)
                    TimerPartner_Stop(userid)
            else:
                if not timer[steamid]["style"] == "Half-Sideways":
                    timer[steamid]["style"] = "Half-Sideways"
                    esc.tell(userid,
                             '#255,51,0[#0,137,255 Timer #255,51,0] #snowYou have changed the mode to #tomatoHalf-Sideways')
                    TimerSolo_Stop(userid)
                    TimerPartner_Stop(userid)
            Menu.mode(userid)

        elif int(choice) == 4:
            if id in timer and CheckPartner(userid):
                if not timer[id]["style"] == "W-Only":
                    timer[id]["style"] = "W-Only"
                    esc.tell(userid,
                             '#255,51,0[#0,137,255 Timer #255,51,0] #snowYou have changed the mode to #tomatoW-Only')
                    esc.tell(player[steamid]["partner"],
                             '#255,51,0[#0,137,255 Timer #255,51,0] #snowYou partner #245,61,0 %s #snowhas recently changed the mode to #tomatoW-Only' % (
                                 name))
                    TimerSolo_Stop(userid)
                    TimerPartner_Stop(userid)
            else:
                if not timer[steamid]["style"] == "W-Only":
                    timer[steamid]["style"] = "W-Only"
                    esc.tell(userid,
                             '#255,51,0[#0,137,255 Timer #255,51,0] #snowYou have changed the mode to #tomatoW-Only')
                    TimerSolo_Stop(userid)
                    TimerPartner_Stop(userid)
            Menu.mode(userid)

    def settings(self, userid):
        steamid = es.getplayersteamid(userid)
        info = popuplib.create('settings')
        info.addline('Trikz Timer')
        info.addline('=> Settings')
        info.addline(' ')
        if player[steamid]["disabled"] == 1:
            info.addline('->1. Timer [Disabled]')
        else:
            info.addline('->1. Timer [Enabled]')
        info.addline(' ')
        if player[steamid]["disabled_keyhint"] == 1:
            info.addline('->2. Text Right Side [Disabled]')
        elif player[steamid]["disabled_keyhint"] == 2:
            info.addline('->2. Text Right-Side [Only Spectators]')
        else:
            if player[steamid]["disabled_keyhint"] == 0:
                info.addline('->2. Text Right Side [Enabled]')

        if player[steamid]["settings_hudhint"] == 1:
            info.addline('->3. Text Middle-Bottom [Enabled]')
        else:
            info.addline('->3. Text Middle-Bottom [Disabled]')

        if player[steamid]["settings_jumps"] == 1:
            info.addline('->4. Show Jumps [On]')
        else:
            info.addline('->4. Show Jumps [Off]')
        if player[steamid]["settings_flashbangs"] == 1:
            info.addline('->5. Show Flashbangs [On]')
        else:
            info.addline('->5. Show Flashbangs [Off]')
        if player[steamid]["settings_strafes"] == 1:
            info.addline('->6. Show Strafes [On]')
        else:
            info.addline('->6. Show Strafes [Off]')
        if player[steamid]["settings_speedmeter"] == 1:
            info.addline('->7. Show SpeedMeter [On]')
        else:
            info.addline('->7. Show SpeedMeter [Off]')
        if player[steamid]["settings_macro"] == 1:
            info.addline('->8. DOLGs Macro [On]')
        else:
            info.addline('->8. DOLGs Macro [Off]')
        info.addline(' ')
        info.addline(' ')
        info.addline('0. Exit')
        info.enablekeys = "123456780"
        info.unsend(userid)
        info.send(userid)
        info.delete()
        info.menuselect = self.settings_select

    def settings_select(self, userid, choice, popupid):
        steamid = es.getplayersteamid(userid)
        if int(choice) == 1:
            if player[steamid]["disabled"] == 0:
                player[steamid]["disabled"] = 1
                client_pref[steamid]["disabled"] = 1
                esc.tell(userid, '#255,51,0[#0,137,255 Timer #255,51,0] #snowYou have #yellowdisabled #245,61,0timer')
            else:
                player[steamid]["disabled"] = 0
                client_pref[steamid]["disabled"] = 0
                esc.tell(userid, '#255,51,0[#0,137,255 Timer #255,51,0] #snowYou have #yellowenabled #245,61,0timer')

        elif int(choice) == 2:
            if player[steamid]["disabled_keyhint"] == 0:

                player[steamid]["disabled_keyhint"] = 1
                client_pref[steamid]["disabled_keyhint"] = 1

                esc.tell(userid,
                         '#255,51,0[#0,137,255 Timer #255,51,0] #snowYour #245,61,0keyhint #snowwill no longer be #yellowdisplayed!')

            elif player[steamid]["disabled_keyhint"] == 1:

                player[steamid]["disabled_keyhint"] = 2
                client_pref[steamid]["disabled_keyhint"] = 2

                esc.tell(userid,
                         '#255,51,0[#0,137,255 Timer #255,51,0] #snowYour #245,61,0keyhint #snowwill only show #yellowspectators')
            else:

                player[steamid]["disabled_keyhint"] = 0
                client_pref[steamid]["disabled_keyhint"] = 0

                esc.tell(userid,
                         '#255,51,0[#0,137,255 Timer #255,51,0] #snowYour #245,61,0keyhint #snowwill now #yellowshow!')



        elif int(choice) == 3:
            if player[steamid]["settings_hudhint"] == 0:

                player[steamid]["settings_hudhint"] = 1
                client_pref[steamid]["settings_hudhint"] = 1
                esc.tell(userid,
                         '#255,51,0[#0,137,255 Timer #255,51,0] #snowYou can now see your #245,61,0hudhint #snowagain!')
            else:

                player[steamid]["settings_hudhint"] = 0
                client_pref[steamid]["settings_hudhint"] = 0
                esc.tell(userid,
                         '#255,51,0[#0,137,255 Timer #255,51,0] #snowYour #245,61,0hudhint #snowwill no longer be #yellowdisplayed!')

        elif int(choice) == 4:
            if player[steamid]["settings_jumps"] == 0:
                player[steamid]["settings_jumps"] = 1
                esc.tell(userid,
                         '#255,51,0[#0,137,255 Timer #255,51,0] #245,61,0Jumps #snowwill now be displayed in your #yellowhudhint')
            else:
                player[steamid]["settings_jumps"] = 0
                esc.tell(userid,
                         '#255,51,0[#0,137,255 Timer #255,51,0] #245,61,0Jumps #snowwill no longer be displayed in your #yellowhudhint')

        elif int(choice) == 5:
            if player[steamid]["settings_flashbangs"] == 0:
                player[steamid]["settings_flashbangs"] = 1
                esc.tell(userid,
                         '#255,51,0[#0,137,255 Timer #255,51,0] #245,61,0Flashbangs #snowwill now be displayed in your #yellowhudhint')
            else:
                player[steamid]["settings_flashbangs"] = 0
                esc.tell(userid,
                         '#255,51,0[#0,137,255 Timer #255,51,0] #245,61,0Flashbangs #snowwill no longer be displayed in your #yellowhudhint')

        elif int(choice) == 6:
            if player[steamid]["settings_strafes"] == 0:
                player[steamid]["settings_strafes"] = 1
                esc.tell(userid,
                         '#255,51,0[#0,137,255 Timer #255,51,0] #245,61,0Strafes #snowwill now be displayed in your #yellowhudhint')
            else:
                player[steamid]["settings_strafes"] = 0
                esc.tell(userid,
                         '#255,51,0[#0,137,255 Timer #255,51,0] #245,61,0Strafes #snowwill no longer be displayed in your #yellowhudhint')

        elif int(choice) == 7:
            if player[steamid]["settings_speedmeter"] == 0:
                player[steamid]["settings_speedmeter"] = 1
                esc.tell(userid,
                         '#255,51,0[#0,137,255 Timer #255,51,0] #245,61,0Speedmeter #snowwill now be displayed in your #yellowhudhint')
            else:
                player[steamid]["settings_speedmeter"] = 0
                esc.tell(userid,
                         '#255,51,0[#0,137,255 Timer #255,51,0] #245,61,0Speedmeter #snowwill no longer be displayed in your #yellowhudhint')

        elif int(choice) == 8:

            if steamid == "[U:1:27015871]" or steamid == "[U:1:42504738]" or steamid == "[U:1:11635]":
                if client_pref[steamid]["settings_macro"] == 0:
                    client_pref[steamid]["settings_macro"] = 1
                    player[steamid]["settings_macro"] = 1
                    es.cexec(userid, 'sm_macro')
                    esc.tell(userid,
                             '#255,51,0[#0,137,255 Timer #255,51,0] #245,61,0Your custom macro has been #yellowenabled!')
                else:
                    client_pref[steamid]["settings_macro"] = 0
                    player[steamid]["settings_macro"] = 0
                    es.cexec(userid, 'sm_macro')
                    esc.tell(userid,
                             '#255,51,0[#0,137,255 Timer #255,51,0] #245,61,0Your custom macro has been #yellowdisabled!')

        if choice in (1, 2, 3, 4, 5, 6, 7, 8):
            Menu.settings(userid)


Menu = Menu()


class Notify:
    def __init__(self):
        pass

    def Country_rank(self, userid, text, steamid, name):
        word = text.split(" ")
        if len(word) == 1:
            country = iptocountry.get_country(playerlib.getPlayer(userid).address.split(':')[0])[0]
            points = displayPoints(steamid)
            rank = displayRank(steamid, country)
            length = displayLen(country)
            esc.msg(
                '#255,51,0[#0,137,255 Timer #255,51,0]#245,61,0 %s #snowis ranked#245,0,61 %s #snow/#245,0,61 %s #snowin#245,61,0 %s #snowwith#245,0,61 %s #snowpoints ' % (
                    name, rank, length, country, points))
        else:
            index = 0
            string = ""
            for x in word:
                if index >= 1:
                    string += x
                index += 1
            target = es.getuserid(string)
            if target:
                name = es.getplayername(target)
                steamid = es.getplayersteamid(target)
                country = iptocountry.get_country(playerlib.getPlayer(target).address.split(':')[0])[0]
                points = displayPoints(steamid)
                rank = displayRank(steamid, country)
                length = displayLen(country)
                esc.msg(
                    '#255,51,0[#0,137,255 Timer #255,51,0] #snowPlayer#245,61,0 %s #snowis ranked#245,0,61 %s #snow/#245,0,61 %s #snowin#245,61,0 %s #snowwith#245,0,61 %s #snowpoints ' % (
                        name, rank, length, country, points))
            else:
                esc.tell(userid,
                         "#255,51,0[#0,137,255 Timer #255,51,0] #snowCouldn't find player, we tried every possible match and combination.")

    def rank(self, userid, text, steamid, name):
        word = text.split(" ")
        if len(word) == 1:
            points = displayPoints(steamid)
            rank = displayRank(steamid)
            length = displayLen()
            esc.msg(
                '#255,51,0[#0,137,255 Timer #255,51,0]#245,61,0 %s #snowis ranked #245,0,61 %s #snow/#245,0,61 %s #snowworldwide with #245,0,61 %s #snowpoints ' % (
                    name, rank, length, points))
        else:
            index = 0
            string = ""
            for x in word:
                if index >= 1:
                    string += x
                index += 1

            target = es.getuserid(string)
            if target:
                name = es.getplayername(target)
                steamid = es.getplayersteamid(target)
                points = displayPoints(steamid)
                rank = displayRank(steamid)
                length = displayLen()
                esc.msg(
                    '#255,51,0[#0,137,255 Timer #255,51,0] #snowPlayer: #245,61,0 %s #snowis ranked#245,0,61 %s #snow/#245,0,61 %s #snowworldwide with#245,0,61 %s #snowpoints ' % (
                        name, rank, length, points))
            else:
                esc.tell(userid,
                         "#255,51,0[#0,137,255 Timer #255,51,0] #snowCouldn't find player, we tried every possible match and combination.")

    def Timer_Stop(self, userid):
        TimerPartner_Stop(userid)
        TimerSolo_Stop(userid)
        esc.tell(userid, '#255,51,0[#0,137,255 Timer #255,51,0] #snowYour timer has been #yellowstopped!')

    def challenge_points(self, userid, text, steamid, name):
        map_choose = str(current_map)
        word = text.split(" ")

        if len(word) > 1:
            map_choose = word[1]

        full_top = popuplib.easymenu(steamid + 'points', None, None)
        full_top.settitle("Points for challenges\nMap: %s" % (map_choose))
        full_top.c_beginsep = " "
        full_top.c_pagesep = " "
        full_top.enablekeys = "098"

        zone_details = mysql.query.fetchall("SELECT name, points FROM zones WHERE map='%s' AND type='timer'",
                                            (map_choose,))

        for item in zone_details:
            full_top.addoption(str(item), ("%s - %s points" % (item[0], item[1])))

        full_top.send(userid)

    def wr(self, userid, text, steamid, name):
        word = text.split(" ")
        if len(word) > 1:
            Menu.wrselect(steamid, userid, "Map", None, str(word[1]))

        else:
            Menu.wrselect(steamid, userid, "Map", None, str(current_map))

    def bwr(self, userid, text, steamid, name):
        word = text.split(" ")
        if len(word) > 1:
            Menu.bwrselect(steamid, userid, "Bonus 1", None, str(word[1]))
        else:
            Menu.bwrselect(steamid, userid, "Bonus 1", None, str(current_map))

    def unpartner(self, userid):
        steamid = es.getplayersteamid(userid)
        if CheckPartner(userid):
            esc.tell(userid,
                     '#255,51,0[#0,137,255 Timer #255,51,0] #snowYou are no longer partnered with#yellow %s' % es.getplayername(
                         player[steamid]["partner"]))
            esc.tell(player[steamid]["partner"],
                     '#255,51,0[#0,137,255 Timer #255,51,0] #snowYou are no longer partnered with#yellow %s' % es.getplayername(
                         userid))
            player[steamid]["partner"] = None

    def ctop(self, userid, text, steamid, name):
        text = text.lower()
        word = text.split(" ")
        if text > 6 and len(word) == 2:
            Menu.top(steamid, userid, str(word[1].capitalize()))
        elif text > 6 and len(word) == 3:
            Menu.top(steamid, userid, str(word[1].capitalize() + " " + str(word[2].capitalize())))
        else:
            Menu.top(steamid, userid)

    def top(self, userid, text, steamid, name):
        Menu.top(steamid, userid)


Notify = Notify()


class Tournament:
    def __init__(self):
        pass

    def register(self, steamid, userid):
        index = 0
        full_top = popuplib.easymenu(steamid + 'tournament', None, self.register_select)
        full_top.settitle("[ Tournament ] %s\nRegister your team to compete!" % str(time.strftime("%d/%m/%Y")))
        # full_top.submenu(10, 'Main Guild')
        full_top.c_beginsep = " "
        full_top.c_pagesep = " "
        full_top.enablekeys = "1098"
        full_top.addoption("signup", "Sign my team up!")
        if len(tournament["queue"]) == 0:
            full_top.addoption("signup", "No teams has signed up yet!", state=False)
        else:
            tplayer = 0
            tplayer_2 = 0
            index = 0
            for team in tournament["queue"]:
                tplayer = tournament["queue"][team][0]
                tplayer_2 = tournament["queue"][team][1]
                index += 30
                if tplayer["steamid"]:
                    full_top.addoption("signup", ("%s | %s (in %s mins)" % (tplayer["name"], tplayer_2["name"], index)),
                                       state=False)
                else:
                    full_top.addoption("signup", ("%s | %s (Finished)" % (tplayer["name"], tplayer_2["name"])),
                                       state=False)

        full_top.send(userid)

    def CheckRegister(self, steamid):
        state = False
        position_in_queue = len(tournament["queue"])
        if position_in_queue > 0:
            for team in tournament["queue"]:
                tplayer = tournament["queue"][team][0]
                tplayer_2 = tournament["queue"][team][1]
                if tplayer['steamid'] == steamid or tplayer_2['steamid'] == steamid:
                    state = True

        return state

    def register_select(self, userid, choice, popupid):
        steamid = es.getplayersteamid(userid)
        name = es.getplayername(userid)
        if choice == "signup":
            if CheckPartner(userid):

                partner_userid = player[steamid]["partner"]
                steamid_partner = es.getplayersteamid(partner_userid)
                name_partner = es.getplayername(partner_userid)

                if not self.CheckRegister(steamid) and not self.CheckRegister(steamid_partner):
                    position_in_queue = len(tournament["queue"])
                    esc.tell(userid, str(position_in_queue))
                    tournament["queue"][position_in_queue] = [
                        {'steamid': steamid, 'name': name, 'time': position_in_queue * 1800},
                        {'steamid': steamid_partner, 'name': name_partner, 'time': position_in_queue * 1800}]
                    esc.tell(userid,
                             '#255,51,0[#0,137,255 Tournament #255,51,0] #snowYou have now signed up with#yellow %s #snow(Waiting time is approx: ??)' % es.getplayername(
                                 player[steamid]["partner"]))
                    esc.tell(partner_userid,
                             "#255,51,0[#0,137,255 Tournament #255,51,0] #snowYour partner#yellow %s have just signed up for tournament. Good luck!" % name)
                    esc.tell(userid,
                             '#255,51,0[#0,137,255 Tournament #255,51,0] #255,0,0You do not need to be in the server while waiting, just come back when it is your turn!')
                else:
                    esc.tell(userid,
                             '#255,51,0[#0,137,255 Tournament #255,51,0] #snowWow! You already registered!. You can register again after you finished your turn!')

            else:
                esc.tell(userid,
                         '#255,51,0[#0,137,255 Tournament #255,51,0] #snowYou need a partner before you can sign up!#')

    def signup(self, userid, text, steamid, name):
        TSet.register(steamid, userid)

    def teleport(self, userid):
        if tournament["status"] == 1:
            steamid = es.getplayersteamid(userid)
            if tournament["turn"] in tournament["queue"]:
                if steamid == tournament["queue"][tournament["turn"]][0]["steamid"] or steamid == \
                        tournament["queue"][tournament["turn"]][1]["steamid"]:
                    return
                else:
                    if "Tournament" in commands:
                        if not zones[str(commands["Tournament"])]['restart_loc'] == "none":
                            restart_location = zones[str(commands["Tournament"])]['restart_loc']
                            es.server.queuecmd(
                                'es_setpos %s %s %s %s' % (
                                    userid, restart_location[0], restart_location[1], restart_location[2]))
                            TimerSolo_Stop(userid)
                            TimerPartner_Stop(userid)
                            esc.tell(userid,
                                     "#255,0,0#255,51,0[#0,137,255 Tournament #255,51,0] #snowYou are not allowed to be here during tournament mode, please consider signing up first using #yellow!register #snowor #yellow!signup")

            else:
                if "Tournament" in commands:
                    if not zones[str(commands["Tournament"])]['restart_loc'] == "none":
                        restart_location = zones[str(commands["Tournament"])]['restart_loc']
                        es.server.queuecmd(
                            'es_setpos %s %s %s %s' % (
                                userid, restart_location[0], restart_location[1], restart_location[2]))
                        TimerSolo_Stop(userid)
                        TimerPartner_Stop(userid)
                        esc.tell(userid,
                                 "#255,0,0#255,51,0[#0,137,255 Tournament #255,51,0] #snowYou are not allowed to be here during tournament mode, please consider signing up first using #yellow!register #snowor #yellow!signup")

    def event(self):
        if len(tournament["queue"]) > 0:

            if tournament["time"] == 0:
                """ RESET """
                tournament["queue"][tournament["turn"]][0]["steamid"] = None
                tournament["queue"][tournament["turn"]][1]["steamid"] = None
                tournament["turn"] += 1
                tournament["time"] = 1800





            else:
                if tournament["turn"] in tournament["queue"]:
                    tournament["time"] -= 1
                    position = tournament["turn"]
                    w_steamid = tournament["queue"][position][0]["steamid"]
                    w_steamid_partner = tournament["queue"][position][1]["steamid"]

                    active_players = []
                    for userid in es.getUseridList():
                        steamid = es.getplayersteamid(userid)
                        active_players.append(steamid)

                    if w_steamid in active_players and not w_steamid_partner in active_players:
                        tournament["disconnect"] -= 1
                        for userid in es.getUseridList():
                            steamid = es.getplayersteamid(userid)
                            if w_steamid == steamid:
                                es.centertell(userid,
                                              "You partner is disconnected!\nYour partner has %s mins to connect again!" % (
                                              TimeFormat(tournament["disconnect"], None, True)))


                    elif w_steamid_partner in active_players and not w_steamid in active_players:
                        tournament["disconnect"] -= 1
                        for userid in es.getUseridList():
                            steamid = es.getplayersteamid(userid)
                            if w_steamid_partner == steamid:
                                es.centertell(userid,
                                              "You partner is disconnected\nYour partner has %s mins to connect again!" % (
                                              TimeFormat(tournament["disconnect"], None, True)))

                    if tournament["disconnect"] == 0:
                        tournament["time"] = 0
                        tournament["disconnect"] = 120

                    # AUTOPARTNER NOT WORKING
                    if w_steamid and w_steamid_partner in active_players:
                        auto_partner = {}

                        for userid in es.getUseridList():
                            steamid = es.getplayersteamid(userid)
                            if w_steamid == steamid:
                                auto_partner[w_steamid] = userid
                            elif w_steamid_partner == steamid:
                                auto_partner[w_steamid_partner] = userid

                        if w_steamid in auto_partner and w_steamid_partner in auto_partner:
                            if player[w_steamid]["timer_id"] == None or player[w_steamid_partner]["timer_id"] == None:
                                player[w_steamid]["partner"] = auto_partner[w_steamid_partner]
                                player[w_steamid_partner]["partner"] = auto_partner[w_steamid]

                                player[w_steamid_partner]["timer_id"] = timer_unique()
                                player[w_steamid]["timer_id"] = player[w_steamid_partner]["timer_id"]
                                timer[player[w_steamid_partner]["timer_id"]] = {'partner_needed': 1,
                                                                                'time': time.time(),
                                                                                'flashbangs': 0,
                                                                                'jumps': 0,
                                                                                'strafes': 0,
                                                                                'style': "Normal",
                                                                                'id': player[w_steamid]["id"],
                                                                                'state': 0}
                                esc.tell(auto_partner[w_steamid_partner],
                                         '#255,51,0[#0,137,255 Tournament #255,51,0] #yellowYou partner has rejoined! You are automatic partned again!')
                                esc.tell(auto_partner[w_steamid],
                                         '#255,51,0[#0,137,255 Tournament #255,51,0] #yellowYou partner has rejoined! You are automatic partned again!')

                        id = player[w_steamid]['timer_id']
                        timer[id]["style"] = "Tournament"

        gamethread.delayedname(1, "event", self.event)


TSet = Tournament()
# TSet.event()


