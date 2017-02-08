import pymysql

# CONFIGS
host = 'localhost'
user = 'your_username'
password = 'your_password'
database = 'your_database'
charset = 'utf8mb4'
create_tables = False

class MySQL:
    def __init__(self):
        # Connect to the database
        self.connection = pymysql.connect(host=host,
                                          user=user,
                                          passwd=password,
                                          db=database)
                                          #cursorclass=pymysql.cursors.DictCursor)
        self.connection.charset = "utf8"
        self.cursor = self.connection.cursor()
        self.cursor.execute("USE %s" % database)
        if create_tables:
            self.execute("""\
                CREATE TABLE IF NOT EXISTS stats (
                steamid VARCHAR(30) PRIMARY KEY NOT NULL,
                points INTEGER DEFAULT 0,
                name VARCHAR(30) NOT NULL,
                country VARCHAR(40) NOT NULL,
                beta_tester INTEGER DEFAULT 0
                )""")

            self.execute("""\
                CREATE TABLE IF NOT EXISTS completed (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                map VARCHAR(30),
                steamid VARCHAR(30),
                steamid_partner VARCHAR(30),
                name VARCHAR(30),
                name_partner VARCHAR(30),
                country VARCHAR(30),
                country_partner VARCHAR(30),
                style VARCHAR(100),
                type VARCHAR(100),
                time FLOAT(50),
                jumps INTEGER DEFAULT 0,
                flashbangs INTEGER DEFAULT 0,
                strafes INTEGER DEFAULT 0,
                date VARCHAR(30),
                points INTEGER DEFAULT 0)
                """)

            self.execute("""\
                CREATE TABLE IF NOT EXISTS completed_personal (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                map VARCHAR(30),
                steamid VARCHAR(30),
                name VARCHAR(30),
                country VARCHAR(30),
                style VARCHAR(100),
                type VARCHAR(100),
                time FLOAT(50),
                jumps INTEGER DEFAULT 0,
                flashbangs INTEGER DEFAULT 0,
                strafes INTEGER DEFAULT 0,
                date VARCHAR(30),
                points INTEGER DEFAULT 0)
                """)

            self.execute("""\
                CREATE TABLE IF NOT EXISTS maps (
                map VARCHAR(30) PRIMARY KEY NOT NULL,
                points INTEGER DEFAULT 0,
                tier INTEGER DEFAULT 0,
                restart_loc VARCHAR(300)
                )""")

            self.execute("""\
                CREATE TABLE IF NOT EXISTS zones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                map VARCHAR(30),
                name VARCHAR(30),
                tier INTEGER DEFAULT 0,
                points INTEGER DEFAULT 0,
                type VARCHAR(100),
                partner_needed INTEGER DEFAULT 1,
                location_1 VARCHAR(100),
                location_2 VARCHAR(100),
                location_3 VARCHAR(100),
                location_4 VARCHAR(100),
                restart_loc VARCHAR(300),
                match_key INTEGER DEFAULT 0,
                comment VARCHAR(100)
                )""")

            self.execute("""\
                CREATE TABLE IF NOT EXISTS tournament (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                map VARCHAR(30),
                start INTEGER DEFAULT 0,
                end INTEGER DEFAULT 0,
                partner_needed INTEGER DEFAULT 0,
                location_1 VARCHAR(100),
                location_2 VARCHAR(100),
                location_3 VARCHAR(100),
                location_4 VARCHAR(100),
                restart_loc VARCHAR(300),
                match_key INTEGER DEFAULT 0,
                comment VARCHAR(100)
                )""")


    def execute(self, sql, args=None):
        result = None
        sql = sql.replace('?', '%s')
        if args:
            self.cursor.execute(sql, args)
        else:
            self.cursor.execute(sql)


    def fetchone(self, sql, args=None):
        result = None
        sql = sql.replace('?', '%s')
        # Create a new record
        if args:
            self.cursor.execute(sql, args)
        else:
            self.cursor.execute(sql)

        return self.cursor.fetchone()


    def fetchall(self, sql, args=None):
        result = None
        sql = sql.replace('?', '%s')
        if args:
            self.cursor.execute(sql, args)
        else:
            self.cursor.execute(sql)

        return self.cursor.fetchall()


    def execute_cc(self, sql, args=None):
        sql = sql.replace('?', '%s')
        if args:
            self.cursor.execute(sql, args)
        else:
            self.cursor.execute(sql)

        # connection is not autocommit by default. So you must commit to save
        # your changes.
        self.connection.commit()
        self.connection.close()


    def fetchone_cc(self, sql, args=None):
        result = None
        sql = sql.replace('?', '%s')
        # Create a new record
        if args:
            self.cursor.execute(sql, args)
        else:
            self.cursor.execute(sql)

        result = self.cursor.fetchone()
        self.connection.commit()
        self.connection.close()
        return result


    def fetchall_cc(self, sql, args=None):
        result = None
        sql = sql.replace('?', '%s')
        if args:
            self.cursor.execute(sql, args)
        else:
            self.cursor.execute(sql)

        result = self.cursor.fetchall()

        # connection is not autocommit by default. So you must commit to save
        # your changes.
        self.connection.commit()

        self.connection.close()

    def save(self):
        self.connection.commit()
    
    def close(self):
        self.connection.commit()
        self.close()


query = MySQL()


