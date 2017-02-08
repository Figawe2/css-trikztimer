from __future__ import division
import es
import playerlib
import esc
import gamethread
import time
import vecmath
from vecmath import vector


analysis = {}

def load():
    for userid in es.getUseridList():
        steamid = es.getplayersteamid(userid)
        analysis[steamid] = {'move':0,
                             'view_angle_0':[],
                             'view_angle_1':[],
                             'velocity':[],
                             'intervals':[],
                             'onground':0,
                             'location':(0,0,0),
                             'msg':0,
                             'strafes':0,
                             'time':0,
                             'cheated':0,
                             'loyal':0}
    gamethread.cancelDelayed("server_loop")
    Serverloop()


def player_activate(ev):
    userid = ev["userid"]
    steamid = es.getplayersteamid(userid)
    analysis[steamid] = {'move': 0,
                         'view_angle_0': [],
                         'view_angle_1': [],
                         'velocity': [],
                         'intervals':[],
                         'onground': 0,
                         'location': (0, 0, 0),
                         'msg': 0,
                         'strafes': 0,
                         'time': 0,
                         'cheated': 0,
                         'loyal':0}

def es_map_start(ev):
    gamethread.cancelDelayed("server_loop")
    Serverloop()


def Serverloop():
    for userid in es.getUseridList():
        if not es.isbot(userid):
            steamid = es.getplayersteamid(userid)
            player  = playerlib.getPlayer(userid)
            if not player.isdead:
                if not player.onGround():
                    analysis[steamid]['onground'] = 0
                    analysis[steamid]['msg'] = 1
                    if time.time() - analysis[steamid]['time'] > 1.8:
                        Average(userid)
    
    
    
                else:
                    analysis[steamid]['onground'] = 1
                    if analysis[steamid]['msg'] == 1:
                        Average(userid)
                    analysis[steamid]['msg'] = 0
                    analysis[steamid]['location'] = es.getplayerlocation(userid)
                    analysis[steamid]['time'] = time.time()




    gamethread.delayedname(0.01, "server_loop", Serverloop)


def list_duplicates(a):
  result = dict((i, a.count(i)) for i in a)
  return result


def player_jump(ev):
    userid = ev["userid"]
    steamid = es.getplayersteamid(userid)
    if not es.isbot(userid):
        analysis[steamid]["view_angle_0"] = []
        analysis[steamid]["view_angle_1"] = []
        analysis[steamid]["velocity"] = []
        velocity = int(vector(float(es.getplayerprop(userid, 'CBasePlayer.localdata.m_vecVelocity[0]')),
                          float(es.getplayerprop(userid, 'CBasePlayer.localdata.m_vecVelocity[1]'))).length())
    
        analysis[steamid]["velocity"].append(velocity)

def StopSpeed(userid):
    velocity_x = float(es.getplayerprop(userid, 'CBasePlayer.localdata.m_vecVelocity[0]'))
    velocity_y = float(es.getplayerprop(userid, 'CBasePlayer.localdata.m_vecVelocity[1]'))
    velocity_z = float(es.getplayerprop(userid, 'CBasePlayer.localdata.m_vecVelocity[2]'))
    myNewVector2 = es.createvectorstring(-velocity_x, -velocity_y, -velocity_z)

    es.setplayerprop(userid, "CBasePlayer.localdata.m_vecBaseVelocity", myNewVector2)

def Average(userid):
    steamid = es.getplayersteamid(userid)
    anti_cheat = 0
    speed_detection = 0
    detections = 0
    case = []
    analysis[steamid]["velocity"].append(250)
    if time.time() - analysis[steamid]["time"] < 2:
        if analysis[steamid]["msg"] == 1:
            duplicates = list_duplicates(analysis[steamid]["view_angle_0"])
            for dup in duplicates:

                        if duplicates[dup] >= 4 and duplicates[dup] <= len(analysis[steamid]["view_angle_0"]) * 0.8:
                            detections += duplicates[dup]
                            case.append(1)



            duplicates = list_duplicates(analysis[steamid]["view_angle_1"])
            for dup in duplicates:
                        if duplicates[dup] >= 4 and duplicates[dup] <= len(analysis[steamid]["view_angle_1"]) * 0.8:
                            detections += duplicates[dup]
                            case.append(2)


            start = analysis[steamid]["velocity"][0]
            checks = []
            aw = 0
            for vel in analysis[steamid]["velocity"]:
                if len(analysis[steamid]["velocity"]) > aw+1:
                    checks.append(analysis[steamid]["velocity"][aw+1]-vel)
                aw += 1


            intervals = []
            ai = 0
            for ena in analysis[steamid]["intervals"]:
                if len(analysis[steamid]["intervals"]) > ai+1:
                    intervals.append(analysis[steamid]["intervals"][ai+1] - ena)
                ai += 1



            aintervals = []
            aix = 0
            for q in intervals:
                if len(intervals) > aix+1:
                    aintervals.append(float(round(intervals[aix+1], 5) - float(round(q, 5))))
                aix += 1

            quelz = 0
            for f in aintervals:
                if abs(f) < 0.009:
                    detections += 2
                    quelz += 2
                else:
                    detections -= 1
                    quelz -= 1
            for q in checks:
                if q >= 5 and q <= 75:
                    speed_detection += 1
                else:
                    speed_detection -= 1


            if time.time() - analysis[steamid]["time"] > 1:
                speed_detection = speed_detection * (time.time() - analysis[steamid]["time"])
            average = 0
            index = 1



            for item in analysis[steamid]["view_angle_0"]:
                index += 1
                average += item

            tell_average = float(average) / float(index)

            collect_data = []
            for x in analysis[steamid]["view_angle_0"]:

                if (x - tell_average) >= -1 and (x - tell_average) <= 4:
                    detections += 0.4

                else:
                    detections -= 1



                collect_data.append(x - tell_average)




            if speed_detection <= 0:
                detections += speed_detection

            if detections >= 5:
                es.server.queuecmd('es_setpos %s %s %s %s' % (
                userid, analysis[steamid]["location"][0], analysis[steamid]["location"][1],
                analysis[steamid]["location"][2]))
                StopSpeed(userid)
                if anti_cheat == 0:
                    esc.tell(userid, "#255,51,0[#255,137,0Anti-Cheat#255,51,0] #snowYeah... No")
                    case.append(3)
                    anti_cheat = 1


            distance = vecmath.distance(analysis[steamid]["location"], es.getplayerlocation(userid)) + 32

            if distance > 250 and analysis[steamid]["strafes"] <= 2 and analysis[steamid]["location"][2] - es.getplayerlocation(userid)[2] >= -5 and analysis[steamid]["location"][2] - es.getplayerlocation(userid)[2] <= 5 and distance < 280:
                if time.time() - analysis[steamid]["time"] >= 0.70 and time.time() - analysis[steamid]["time"] <= 0.9:

                    es.server.queuecmd('es_setpos %s %s %s %s' % (userid, analysis[steamid]["location"][0], analysis[steamid]["location"][1],
                    analysis[steamid]["location"][2]))
                    StopSpeed(userid)
                    if anti_cheat == 0:
                        esc.tell(userid, "#255,51,0[#255,137,0Anti-Cheat#255,51,0] #snowFalse positive - your data has been logged. Thank you for improving the anti-cheat")
                        #esc.msg(
                        #    "#255,51,0[#255,137,0Anti-Cheat#255,51,0]#snow %s is using silent-strafes" % (es.getplayername(userid)))
                        anti_cheat = 1
                        case.append(4)

            if anti_cheat == 1:
                esc.msg("#255,51,0[#255,137,0Anti-Cheat#255,51,0]#yellow %s #snowis cheating" % (es.getplayername(userid)))
                analysis[steamid]["cheated"] = 1
                esc.tell(userid, "#255,51,0[#255,137,0Anti-Cheat#255,51,0] #snowTotal detections %s | %s | C#: %s" % (
                detections, speed_detection, str(case)))
                dump_data_to_file(userid, case, detections, collect_data, checks, speed_detection)
            else:
                analysis[steamid]["loyal"] += 1

            if analysis[steamid]["loyal"] >= 300:
                analysis[steamid]["loyal"] = 1

                esc.tell(userid, "#255,51,0[#255,137,0Anti-Cheat#255,51,0] #snowYour data has been logged. Thank you for improving the anti-cheat! The machine is learning from you!")


        analysis[steamid]["intervals"] = []
        analysis[steamid]["time"] = time.time()
        analysis[steamid]["velocity"] = []
        analysis[steamid]["view_angle_0"] = []
        analysis[steamid]["view_angle_1"] = []


def dump_data_to_file(userid, case, detections, data, velocity, speed_dections):
    addonpath = es.getAddonPath("trikztimer").replace("\\", "/")
    f = open(addonpath + '/plugins/anticheat/log.txt', 'ab')
    f.write('STEAMID: %s\n' % es.getplayersteamid(userid))
    f.write('NAME: %s\n' % es.getplayername(userid))
    f.write('CASES: %s\n' % case)
    f.write('DETECTIONS: %s | Speed detections %s\n' % (detections, speed_dections))
    for x in data:
            f.write('A-X: %s\n' % (x))
    for y in velocity:
            f.write('S: %s\n' % (y))
    f.write('--------------------------------------------------------------------------------------------------------\n')

    f.close()


def sm2es_keyPress(ev):
    userid = ev["userid"]
    if es.exists("userid", userid):

        if ev['status'] == '0':
            return
        if es.isbot(userid):
            return

        ply = playerlib.getPlayer(userid)

        if ply.isdead:
            return

        velocity_x = float(es.getplayerprop(userid, 'CBasePlayer.localdata.m_vecVelocity[0]'))
        velocity_y = float(es.getplayerprop(userid, 'CBasePlayer.localdata.m_vecVelocity[1]'))
        velocity = int(vector(float(es.getplayerprop(userid, 'CBasePlayer.localdata.m_vecVelocity[0]')),
                              float(es.getplayerprop(userid, 'CBasePlayer.localdata.m_vecVelocity[1]'))).length())
        steamid = es.getplayersteamid(userid)
        if analysis[steamid]['onground'] == 0:
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

