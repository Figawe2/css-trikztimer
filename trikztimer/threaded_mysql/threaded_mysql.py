from listeners.tick import Repeat, Delay
from queue import Queue
from messages import SayText2
from events import Event
import pymysql.cursors




q_sql = Queue()

q_timer = Queue()

class Gamethread:
    def __init__(self):
        self.gamethread = Repeat(self._queuehandler)
        self.safe_thread_start = False
        self._callback = None
        self._tick_delay = 0
        self._active = False
        self.connection = None

    def execute(self, query, args=None, callback=None, data_pack=None, seconds=0.2):
        # If callback = None assuming insert into statement
        q_sql.put([query, args, callback, 0, data_pack])
        q_timer.put(seconds)

    def fetchone(self, query, args=None, callback=None, data_pack=None, seconds=0.2):
        # If callback = None assuming insert into statement
        q_sql.put([query, args, callback, 1, data_pack])
        q_timer.put(seconds)

    def fetchall(self, query, args=None, callback=None, data_pack=None, seconds=0.2):
        # If callback = None assuming insert into statement
        q_sql.put([query, args, callback, 2, data_pack])
        q_timer.put(seconds)

    def handlequeue_start(self):
        if self.connection:
            if not self.safe_thread_start:
                self.safe_thread_start = True
                self.gamethread.start(0.1)
                print('threaded_mysql: Queue handler started')
            else: print('threaded_mysql: Queue handler already started, use queuehandler_stop(self)')
        else: raise ValueError("threaded_mysql: You must connect to mysql first")

    def handlequeue_stop(self):
        self.gamethread.stop()
        self.safe_thread_start = False
        print('threaded_mysql: Queue handler already started, use queuehandler_stop(self)')

    def connect(self,host,user,password,db,charset,cursorclass=pymysql.cursors.DictCursor):
        self.connection = pymysql.connect(host=host,
                                         user=user,
                                         password=password,
                                         db=db,
                                         charset=charset,
                                         cursorclass=cursorclass)
        self.cursor = self.connection.cursor()


    def _safe_fetch(self, worker):
        data_pack = worker[4]
        func_callback = worker[2]
        data = self.cursor.fetchone()

        if data_pack:
            func_callback(data, data_pack)
        else: func_callback(data)

    def _safe_fetchall(self, data_pack=None):
        pass

    def _queuehandler(self):
        if self._tick_delay <= 0:
            if self._active:
                if q_sql.qsize() > 0:

                    try:
                        work = q_sql.get()
                        data_pack = work[4]
                        if work[3] == 0:
                            if work[1]:
                                self.cursor.execute(work[0], work[1])
                                if work[2]:
                                    if data_pack:
                                        work[2](data_pack)
                                    else:
                                        work[2]()
                            else:
                                self.cursor.execute(work[0])
                                if work[2]:
                                    if data_pack:
                                        work[2](data_pack)
                                    else:
                                        work[2]()

                        if work[3] == 1:
                            if work[1]:
                                self.cursor.execute(work[0], work[1])
                                if work[2]:
                                    Delay(0.1, self._safe_fetch, (work,))
                            else:
                                self.cursor.fetchone(work[0])
                                if work[2]:
                                    Delay(0.1, self._safe_fetch, (work,))

                        if work[3] == 2:
                            if work[1]:
                                data = self.cursor.fetchall(work[0], work[1])
                                if work[2]:
                                    if data_pack:
                                        work[2](data, data_pack)
                                    else:
                                        work[2](data)
                            else:
                                data = self.cursor.fetchall(work[0])
                                if work[2]:
                                    if data_pack:
                                        work[2](data, data_pack)
                                    else:
                                        work[2](data)
                    except:
                        pass
                self._active = False

            if q_timer.qsize() > 0:
                self._tick_delay = q_timer.get()
                self._active = True

        self._tick_delay -= 0.1

    def execute(self, sql):
        data = self.cursor.execute(sql)


        return self.cursor.fetchone()





test = Gamethread()

test.connect('localhost', 'root', '123pass', 'trikz_server', 'utf8')

test.handlequeue_start()



def hello(data):
    SayText2("Name: %s" % str(data)[:180]).send()



@Event('player_say')
def on_player_say(game_event):
        text = game_event['text']
        userid = game_event['userid']
        if text == '!q':
            test.fetchone('SELECT name FROM stats ORDER BY points', callback=hello)
            SayText2('Hello').send()

