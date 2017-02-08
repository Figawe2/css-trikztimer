import es, esc, effectlib, gamethread, time
from usermsg import hudhint
from velohook import chat
import vecmath
from vecmath import vector
from math import sqrt
import playerlib
import popuplib
from configobj import ConfigObj
import psyco

psyco.full()

nospam = dict()
client = {}
analysis = {}
bullet = {'loc': 0, 'loc2': 0, 'n': 0}


def load():
    chat.hook("window.chat", None)
    es.doblock('corelib/noisy_on')
    chat.registerPublicCommand("!lj", lj_toggle, True)
    chat.registerPublicCommand("!ljstats", lj_toggle, True)
    chat.registerPublicCommand("!rb", lj_toggle, True)
    chat.registerPublicCommand("!rbstats", lj_toggle, True)
    chat.registerHiddenCommand('/lj', lj_toggle, True)
    chat.registerHiddenCommand('/ljstats', lj_toggle, True)
    chat.registerHiddenCommand('/rb', lj_toggle, True)
    chat.registerHiddenCommand('/rbstats', lj_toggle, True)

def lj_toggle(userid):
    steamid = es.getplayersteamid(userid)
    if not steamid in client:
        client[steamid] = {'loc': es.getplayerlocation(userid),
                              'loc2': (0, 0, 0),
                              'lj': 0,
                              'time': 0,
                              'avs': [],
                              'pre': 0,
                              'strafes': 0}
        analysis[steamid] = {'move': 0,
                             'view_angle_0': [],
                             'view_angle_1': [],
                             'velocity': [],
                             'intervals': [],
                             'onground': 0,
                             'location': (0, 0, 0),
                             'msg': 0,
                             'strafes': 0,
                             'time': 0,
                             'cheated': 0,
                             'loyal': 0}

    if client[steamid]['lj'] == 0:
        client[steamid]['lj'] = 1
        esc.tell(userid,
                 "#255,51,0[#255,137,0LJStats#255,51,0] #snowYou are now tracking your jumps.")
        Set_Location(userid)

    else:
        gamethread.cancelDelayed("Set_Location_%s" % userid)
        client[steamid]['lj'] = 0
        esc.tell(userid, "#255,51,0[#255,137,0LJStats#255,51,0] #snowYou are no longer tracking your jumps.")

def compass(userid):
    player = playerlib.getPlayer(userid)
    view_angles = player.viewVector()

    view_x = player.viewVector()[0] * 360

    if view_x >= 300:
        return True


def playerOnTop(userid):
    # Player X-X width = 64.0625 units
    # Player Y-Y width = 64.2360839844
    # Player height = 62.03125 units
    alive = es.getlivingplayercount()
    if alive > 1:
        player = playerlib.getPlayer(userid)
        player_pos = es.getplayerlocation(userid)
        target = playerlib.getPlayer(player.getClosestPlayer(team=None)[1])
        if bool(target):
            target_distance = player.getClosestPlayer(team=None)[0]
            onground = target.onGround()
            target_pos = es.getplayerlocation(target)
            if player_pos[2] - target_pos[2] > 62 and player_pos[2] - target_pos[2] < 65 and target_distance < 80:
                return ["True", onground, target]
            else:
                return ["False", onground, target]
        else:
            return ["False", None, None]

    return ["False", None, None]


def Check_When_Grounded(userid, bhop, runboost):
    name = es.getplayername(userid)
    steamid = es.getplayersteamid(userid)
    velocity = int(round(vector((float(es.getplayerprop(userid, 'CBasePlayer.localdata.m_vecVelocity[0]')),
                                 float(es.getplayerprop(userid, 'CBasePlayer.localdata.m_vecVelocity[1]')),
                                 float(es.getplayerprop(userid, 'CBasePlayer.localdata.m_vecVelocity[2]')))).length(),
                         2))

    client[steamid]["time"] += 0.01
    client[steamid]["avs"].append(velocity)
    check = es.getplayerprop(userid, 'CBasePlayer.m_fFlags')
    if check & 1:
        location = es.getplayerlocation(userid)
        player = playerlib.getPlayer(userid)
        distance = (vecmath.distance((float(client[steamid]['loc'][0]), float(client[steamid]['loc'][1])),
                                     (float(location[0]), float(location[1])))) + 32
        index = 0
        add = 0
        for item in client[steamid]["avs"]:
            add += item
            index += 1
            break

        av = add / index

        time = (client[steamid]["time"])

        checker = float(client[steamid]['loc'][2]) - float(location[2])

        average = 0
        index = 1
        for item in analysis[steamid]["view_angle_0"]:
            index += 1
            average += item

        tell_average = float(average) / float(index)

        detections = 0
        for x in analysis[steamid]["view_angle_0"]:

            if (x - tell_average) >= -1 and (x - tell_average) <= 4:
                detections -= 2

            else:
                detections += 0.843

        if detections < 0:
            detections = 0


        if not runboost:
            if not bhop:
                if distance > 264 and distance < 280 and client[steamid]["time"] < 0.9 and client[steamid]["time"] > 0.68:
                    esc.tell(userid, '#snowPrestrafe:#255,137,0 %s u/s #snow| Strafes#255,137,0 %s' % (client[steamid]["pre"], analysis[steamid]["strafes"]))
                    esc.tell(userid, '#snowAverage Speed:#255,137,0 %s u/s #snowand air time:#255,137,0 %s seconds' % (av, client[steamid]["time"]))
                    esc.tell(userid, '#snowDistance:#255,137,0 %s units' % (round(distance, 3)))

                elif distance < 280 and client[steamid]["time"] < 0.9 and distance > 240 and client[steamid]["time"] > 0.68:
                    esc.tell(userid, '#snowPrestrafe:#255,137,0 %s u/s #snow| Strafes#255,137,0 %s' % (client[steamid]["pre"], analysis[steamid]["strafes"]))
                    esc.tell(userid, '#snowAverage Speed:#255,137,0 %s u/s #snowand air time:#255,137,0 %s seconds' % (av, client[steamid]["time"]))
                    esc.tell(userid, '#snowDistance:#255,137,0 %s units' % (round(distance, 3)))


        else:
            if distance >= 485 and distance <= 580:
                esc.tell(userid, '#yellow- RUNBOOST -')
                esc.tell(userid, '#snowPrestrafe:#255,137,0 %s u/s #snow| Strafes#255,137,0 %s' % (
                client[steamid]["pre"], analysis[steamid]["strafes"]))
                esc.tell(userid, '#snowAverage Speed:#255,137,0 %s u/s #snowand air time:#255,137,0 %s seconds' % (
                av, client[steamid]["time"]))
                esc.tell(userid, '#snowDistance:#255,137,0 %s units' % (round(distance, 3)))

        analysis[steamid] = {'move': 0,
                             'view_angle_0': [],
                             'view_angle_1': [],
                             'velocity': [],
                             'intervals': [],
                             'onground': 0,
                             'location': (0, 0, 0),
                             'msg': 0,
                             'strafes': 0,
                             'time': 0,
                             'cheated': 0,
                             'loyal': 0}
        Set_Location(userid)

        return



    gamethread.delayedname(0.001, 'Check_Ground_%s' % userid, Check_When_Grounded, args=(userid, bhop, runboost))


def Check_Runboost(userid):
    location = es.getplayerlocation(userid)
    steamid = es.getplayersteamid(userid)
    velocity = int(round(vector((float(es.getplayerprop(userid, 'CBasePlayer.localdata.m_vecVelocity[0]')),
                                 float(es.getplayerprop(userid, 'CBasePlayer.localdata.m_vecVelocity[1]')),
                                 float(es.getplayerprop(userid, 'CBasePlayer.localdata.m_vecVelocity[2]')))).length(),
                         2))
    gamethread.cancelDelayed("Check_Ground_%s" % userid)
    if playerOnTop(userid)[0] == "True":
        client[steamid]['loc'] = location
        client[steamid]['time'] = 0
        client[steamid]['avs'] = []
        client[steamid]['pre'] = velocity
    else:
        gamethread.cancelDelayed("Check_Ground_%s" % userid)
        Check_When_Grounded(userid, False, True)
        return

    gamethread.delayedname(0.001, 'Check_Runboost_%s' % userid, Check_Runboost, args=(userid))


def Set_Location(userid):
    check = es.getplayerprop(userid, 'CBasePlayer.m_fFlags')
    location = es.getplayerlocation(userid)
    steamid = es.getplayersteamid(userid)
    player = playerlib.getPlayer(userid)
    velocity = int(round(vector((float(es.getplayerprop(userid, 'CBasePlayer.localdata.m_vecVelocity[0]')),
                                 float(es.getplayerprop(userid, 'CBasePlayer.localdata.m_vecVelocity[1]')),
                                 float(es.getplayerprop(userid, 'CBasePlayer.localdata.m_vecVelocity[2]')))).length(),
                         2))
    if not check & 1:
        if not playerOnTop(userid)[0] == "True":
            if velocity < 400:
                gamethread.cancelDelayed("Check_Runboost_%s" % userid)
                gamethread.cancelDelayed("Check_Ground_%s" % userid)
                Check_When_Grounded(userid, False, False)

            else:
                gamethread.cancelDelayed("Check_Runboost_%s" % userid)
                gamethread.cancelDelayed("Check_Ground_%s" % userid)
                Check_When_Grounded(userid, True, False)
        else:
            gamethread.cancelDelayed("Check_Runboost_%s" % userid)
            gamethread.cancelDelayed("Check_Ground_%s" % userid)
            Check_Runboost(userid)

        return
    else:
        client[steamid]['loc'] = location
        client[steamid]['time'] = 0
        client[steamid]['avs'] = []
        client[steamid]['pre'] = velocity
        gamethread.cancelDelayed("Check_Runboost_%s" % userid)
        gamethread.cancelDelayed("Check_Ground_%s" % userid)

    if player.isdead:
        gamethread.cancelDelayed("Check_Runboost_%s" % userid)
        gamethread.cancelDelayed("Check_Ground_%s" % userid)
        gamethread.cancelDelayed("Set_Location_%s" % userid)
        esc.tell(userid, "#255,51,0[#255,137,0LJStats#255,51,0] #snowis no longer tracking you!")
        client[steamid]['lj'] = 0
        return

    gamethread.delayedname(0.001, 'Set_Location_%s' % userid, Set_Location, args=(userid))


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
        velocity = int(vector(float(es.getplayerprop(userid, 'CBasePlayer.localdata.m_vecVelocity[0]')),
                              float(es.getplayerprop(userid, 'CBasePlayer.localdata.m_vecVelocity[1]'))).length())
        steamid = es.getplayersteamid(userid)
        check = es.getplayerprop(userid, 'CBasePlayer.m_fFlags')
        if not check & 1:
            if ev["command"] == 'IN_MOVELEFT':
                if analysis[steamid]['move'] == 0:
                    analysis[steamid]['move'] = 1
                    analysis[steamid]['view_angle_0'].append(ply.getViewAngle()[0])
                    analysis[steamid]['view_angle_1'].append(ply.getViewAngle()[1])
                    analysis[steamid]['intervals'].append(time.time())
                    analysis[steamid]['velocity'].append(velocity)
                    analysis[steamid]['strafes'] += 1


            if ev['command'] == 'IN_MOVERIGHT':
                if analysis[steamid]['move'] == 1:
                    analysis[steamid]['move'] = 0
                    analysis[steamid]['view_angle_0'].append(ply.getViewAngle()[0])
                    analysis[steamid]['view_angle_1'].append(ply.getViewAngle()[1])
                    analysis[steamid]['intervals'].append(time.time())
                    analysis[steamid]['velocity'].append(velocity)
                    analysis[steamid]['strafes'] += 1
        else:


            analysis[steamid] = {'move': 0,
                                 'view_angle_0': [],
                                 'view_angle_1': [],
                                 'velocity': [],
                                 'intervals': [],
                                 'onground': 0,
                                 'location': (0, 0, 0),
                                 'msg': 0,
                                 'strafes': 0,
                                 'time': 0,
                                 'cheated': 0,
                                 'loyal': 0}