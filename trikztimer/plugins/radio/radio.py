import es
import esc
import popuplib
import gamethread
import usermsg



radio = {'song':"", 'title':"", 'duration':0, 'current_duration':0}
TSQL = es.import_addon("trikztimer/threaded_mysql")
mysql = es.import_addon('trikztimer/mysql')
client = {}


def load():
    esc.msg('#255,0,0Radio load')
    for userid in es.getUseridList():
        steamid = es.getplayersteamid(userid)
        if not steamid in client:
            client[steamid] = {'radio': 0}
    jukebox_loop()


def player_activate(ev):
    userid = ev['userid']
    steamid = es.getplayersteamid(userid)
    if not steamid in client:
        client[steamid] = {'radio':0}
    else:
        client[steamid]['radio'] = 0


def es_map_start(ev):
    userid = ev['userid']
    steamid = es.getplayersteamid(userid)
    if not steamid in client:
        client[steamid] = {'radio':0}
    else:
        client[steamid]['radio'] = 0

def player_disconnect(ev):
    userid = ev['userid']
    steamid = es.getplayersteamid(userid)
    client[steamid]['radio'] = 0

def data_to_menu_callback(data, data_pack):
    userid = data_pack['userid']
    radio_menu(userid, data)


def player_say(ev):
    text = ev['text']
    userid = ev['userid']
    data_pack = {'userid': userid, 'text': text}
    if text.startswith("!radio"):
        TSQL.Query.fetchall("SELECT title FROM playlist ORDER BY date DESC", callback=data_to_menu_callback,
                            data_pack=data_pack)

    if text == "!songname":
        esc.msg('#50,50,50[Radio] #snowCurrently playing: %s' % radio['title'] + "#50,50,50|#snow duration: %s" % radio['duration'])

    if text == "!youtube":
        usermsg.motd(userid, 2, 'Add a song..', "http://dreamaboutnow.com/youtube",
                     visible=True)
        
    if text == "!skip":
        radio['current_duration'] = 5000
        esc.msg('#50,50,50[Radio] #snowSong has been skipped!')
        
def radio_menu(userid, data):
    steamid = es.getplayersteamid(userid)
    info = popuplib.easymenu(str(steamid) + 'radio', None, radio_menu_select)
    info.settitle("Trikz Cafe Radio\nPlaying: %s" % radio['title'])
    info.c_beginsep = " "
    info.c_pagesep = " "
    if client[steamid]['radio']:
        info.addoption("tune_in", "Tune in: On")
    else:
        info.addoption("tune_in", "Tune in: Off")

    for item in data:
        info.addoption(item[0], item[0], False)

    info.send(userid)


def radio_menu_select(userid, choice, popupid):
    steamid = es.getplayersteamid(userid)

    data_pack = {'steamid':userid, 'userid':userid}
    if choice == "tune_in":
        if client[steamid]['radio']:
            client[steamid]['radio'] = 0
            esc.tell(userid, '#50,50,50[Radio] #snowYou have turned radio #50,50,50off')
            usermsg.motd(userid, 2, 'Cafe Radio - Youtube', "http://www.google.com",
                         visible=False)
        else:
            client[steamid]['radio'] = 1
            esc.tell(userid, '#50,50,50[Radio] #snowYou have turned radio #50,50,50on')
            my_song = str(radio['song']) + "&feature=youtu.be&t=" + str(radio['current_duration'])
            usermsg.motd(userid, 2, 'Cafe Radio - Youtube', my_song,
                         visible=False)
        TSQL.Query.fetchall("SELECT title FROM playlist ORDER BY date DESC", callback=data_to_menu_callback,
                            data_pack=data_pack)





def get_time(duration):

    n = duration.split(':')

    if int(n[0]) == 0:
        return False

    if len(n) > 2:
        return False

    timestr = duration

    ftr = [60,1]

    return int(sum([a*b for a,b in zip(ftr, map(int,timestr.split(':')))]))




def jukebox_loop():


    if radio['current_duration'] >= radio['duration']:

        data = mysql.query.fetchone("SELECT title, duration, url, id FROM playlist ORDER BY date ASC")
        if bool(data):

            if not data[2] == None or not data[0] == None:
                radio['song'] = data[2]
                radio['title'] = data[0]
                radio['duration'] = get_time(data[1])
                radio['current_duration'] = 0

                for userid in es.getUseridList():
                    steamid = es.getplayersteamid(userid)
                    if client[steamid]['radio']:
                        usermsg.motd(userid, 2, 'Cafe Radio - Youtube', radio['song'],
                                     visible=False)


                esc.msg('#50,50,50[Radio] #snowTune it with !radio')
                esc.msg('#50,50,50[Radio] #snowNow playing: #50,50,50%s' % radio['title'])
            else:
                radio['song'] = ""
                radio['title'] = ""
                radio['duration'] = 0
                radio['current_duration'] = 0

            mysql.query.execute("DELETE FROM playlist WHERE id='%s'" % data[3])

        else:
            radio['song'] = ""
            radio['title'] = ""
            radio['duration'] = 0
            radio['current_duration'] = 0

    radio['current_duration'] += 1



    gamethread.delayedname(1, "jukebox_loop", jukebox_loop)

