import es, esc
import gamethread
from Queue import Queue

mysql = es.import_addon("queue_timer/mysql")

q_sql = Queue()
q_timer = Queue()


class ThreadedSQL:
    def __init__(self):
        self.callback = None
        self.tick_delay = 0
        self.active = False

    def execute(self, query, args=None, callback=None, data_pack=None, seconds=0.1):
        # If callback = None assuming insert into statement
        q_sql.put([query, args, callback, 0, data_pack])
        q_timer.put(seconds)

    def fetchone(self, query, args=None, callback=None, data_pack=None, seconds=0.1):
        # If callback = None assuming insert into statement
        q_sql.put([query, args, callback, 1, data_pack])
        q_timer.put(seconds)

    def fetchall(self, query, args=None, callback=None, data_pack=None, seconds=0.1):
        # If callback = None assuming insert into statement
        q_sql.put([query, args, callback, 2, data_pack])
        q_timer.put(seconds)

    def handleQueue(self):
        if self.tick_delay <= 0:
            if self.active:
                if q_sql.qsize() > 0:

                    try:
                        work = q_sql.get()
                        data_pack = work[4]
                        if work[3] == 0:
                            if work[1]:
                                mysql.query.execute(work[0], work[1])
                                if work[2]:
                                    if data_pack:
                                        work[2](data_pack)
                                    else:
                                        work[2]()
                            else:
                                mysql.query.execute(work[0])
                                if work[2]:
                                    if data_pack:
                                        work[2](data_pack)
                                    else:
                                        work[2]()

                        if work[3] == 1:
                            if work[1]:
                                data = mysql.query.fetchone(work[0], work[1])
                                if work[2]:
                                    if data_pack:
                                        work[2](data, data_pack)
                                    else:
                                        work[2](data)
                            else:
                                data = mysql.query.fetchone(work[0])
                                if work[2]:
                                    if data_pack:
                                        work[2](data, data_pack)
                                    else:
                                        work[2](data)

                        if work[3] == 2:
                            if work[1]:
                                data = mysql.query.fetchall(work[0], work[1])
                                if work[2]:
                                    if data_pack:
                                        work[2](data, data_pack)
                                    else:
                                        work[2](data)
                            else:
                                data = mysql.query.fetchall(work[0])
                                if work[2]:
                                    if data_pack:
                                        work[2](data, data_pack)
                                    else:
                                        work[2](data)
                    except:
                        pass
                self.active = False

        if q_timer.qsize() > 0:
            self.tick_delay = q_timer.get()
            self.active = True

        self.tick_delay -= 0.1

        gamethread.delayedname(0.1, "threaded_sql", self.handleQueue)


Query = ThreadedSQL()
Query.handleQueue()

