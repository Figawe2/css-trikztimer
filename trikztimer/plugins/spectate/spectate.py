import es
import playerlib
from usermsg import hudhint
from usermsg import keyhint
import gamethread
from vecmath import vector



specs = {}


class Player(object):

    def __init__(self, userid):
        self.userid = userid
        self.target = None

    def update(self):
        timer = es.import_addon('trikztimer/plugins/timer')
        """
        Update the player's message showing his targets ranks.
        """
        if not es.exists('userid', self.userid):
            return

        #if not es.exists('userid', self.target):
          #   return

        if es.getplayerteam(self.userid) in (2, 3):
            if not playerlib.getPlayer(self.userid).isdead:
                Player(self.userid).delspec(self.userid, self.target, 1)
                return

        target = self.getspec()
        if target != -1:

                self.target = target

                steamid = es.getplayersteamid(self.target)
                name = es.getplayername(self.target)
                # PARTNER TIMER

                velocity = round(vector(float(es.getplayerprop(self.target, 'CBasePlayer.localdata.m_vecVelocity[0]')), float(es.getplayerprop(self.target, 'CBasePlayer.localdata.m_vecVelocity[1]'))).length(), 2)

                Player(self.userid).addspec(self.userid, self.target)

                Player(self.userid).delspec(self.userid, self.target, 2)


                specs[self.userid]["last_spec"] = self.target

                if steamid in timer.player:
                    string = timer.player[steamid]["text_display"]
                    if timer.CheckPartner(self.target):
                        string += "\n(Partnered)"
                    else:
                        string += "\n(Solo)"

                    timer.player[steamid]['spectators'] = specs[self.target]['n']

                if not es.isbot(target):
                    hudhint(self.userid, "- %s -\nVel: %s\n%s" % (name,velocity, string))



                name_list = ""
                if len(specs[self.target]['n']) > 0:
                    for object in specs[self.target]['n']:
                                s_name = str(es.getplayername(object))
                                if len(s_name) > 12:
                                    s_name = str(es.getplayername(object))[0:12] + "..."
                                name_list += "\n" + s_name

                if timer.tournament["status"] == 0:
                    keyhint(self.userid, "%s's Spectators: %s\n%s" % (name, len(specs[self.target]['n']), name_list))
                else:
                    string = ""
                    string += "-- Tournament Mode --\n "
                    if timer.tournament["turn"] in timer.tournament["queue"] > 0:
                        turn = timer.tournament["turn"]
                        string += "\n %s | %s is playing..\n \n Next couple in: %s \n \n \n" % (
                        timer.tournament["queue"][turn][0]["name"], timer.tournament["queue"][turn][1]["name"],
                        timer.TimeFormat(timer.tournament["time"], None, True))
                    else:
                        string += "\nNo teams available yet!\n \n"


                    keyhint(self.userid, "Spectators: %s\n%s" % (string, name, len(specs[self.target]['n']), name_list))


        else:
            Player(self.userid).delspec(self.userid, self.target, 2)



    def hide(self):
        """
        Hides the hint box during game play.
        """
        gamethread.cancelDelayed('spectarget_loop_%s' % self.userid)

    def getspec(self):
        """
        Gets the handle of the player that the user is spectating.
        """
        handle = es.getplayerprop(self.userid, "CCSPlayer.baseclass.m_hObserverTarget")
        for tuserid in es.getUseridList():
            thandle = es.getplayerhandle(tuserid)
            if thandle == handle:
                return tuserid

        return -1



    def delspec(self, userid, target, case):
        timer = es.import_addon('trikztimer/plugins/timer')
        if not userid in specs:
            specs[userid] = {}
            specs[userid]["last_spec"] = None
            specs[userid]["n"] = []
        last_spec = specs[userid]["last_spec"]
        if case == 1:
            if not last_spec == None:
                if userid in specs[last_spec]['n']:
                    steamid = es.getplayersteamid(target)
                    specs[last_spec]['n'].remove(userid)
                    timer.player[steamid]['spectators'] = specs[target]['n']
                    #es.msg('Del spec1')
        else:
             if not last_spec == None and not last_spec == target:
                if userid in specs[last_spec]['n']:
                    steamid = es.getplayersteamid(target)
                    specs[last_spec]['n'].remove(userid)
                    timer.player[steamid]['spectators'] = specs[target]['n']
                    #es.msg('Del spec2')




    def addspec(self, userid, target):
         if not userid in specs:
            specs[userid] = {}
            specs[userid]["last_spec"] = None
            specs[userid]["n"] = []
         if target in specs:
             if not userid in specs[target]['n']:
                   specs[target]['n'].append(userid)
                   #es.msg('Added spec')




players = {}
def getPlayer(userid):
    userid = int(userid)
    if userid not in players:
        players[userid] = Player(userid)

    return players[userid]

def unload():
    """
    Fires when the script is unloaded.
    """
    for userid in es.getUseridList():
        gamethread.cancelDelayed('spectarget_loop')


def load():
        global specs
        gamethread.cancelDelayed('spectarget_loop')
        loop()


def es_map_start(ev):
    specs.clear()
    gamethread.cancelDelayed('spectarget_loop')
    loop()


def player_spawn(ev):
    userid = ev["userid"]
    steamid = es.getplayersteamid(userid)

    if userid in specs:
        specs[userid]["n"] = []
    else:
        specs[userid] = {}
        specs[userid]["last_spec"] = None
        specs[userid]["n"] = []


    timer = es.import_addon('trikztimer/plugins/timer')
    if steamid in timer.player:
        timer.player[steamid]['spectators'] = []


def loop():
    timer = es.import_addon('trikztimer/plugins/timer')
    for userid in es.getUseridList():
        if not userid in specs:
            specs[userid] = {}
            specs[userid]["last_spec"] = None
            specs[userid]["n"] = []
        getPlayer(userid).update()


    for n in specs:
       a = specs[n]['n']
       for spec in a:
           if not es.exists("userid", spec):
               a.remove(spec)
               if es.getplayersteamid(n) in timer.player:
                timer.player[es.getplayersteamid(n)]['spectators'] = a




    gamethread.delayedname(0.1, ('spectarget_loop'), loop)


