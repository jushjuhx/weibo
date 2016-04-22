import pymysql , configparser
import time
class dbMysql:
    #获取config配置文件def getConfig(section, key). 设置database 信息
    __config = configparser.ConfigParser()
    __config.read('config.ini')
    __dbhost = __config.get('database', 'dbhost')
    __dbport = __config.get('database', 'dbport')
    __dbname = __config.get('database', 'dbname')
    __dbuser = __config.get('database', 'dbuser')
    __dbpass = __config.get('database', 'dbpass')
    __conn = None
    __cur = None
    def executeInsert(self , sql, paras):
        self.__conn = pymysql.connect(host = self.__dbhost , user = self.__dbuser, passwd = self.__dbpass, db = self.__dbname, charset='UTF8')
        try:
            with self.__conn.cursor() as cursor:
                # Create a new record
                cursor.execute(sql, paras)
            # connection is not autocommit by default. So you must commit to save
            # your changes.
            self.__conn.commit()
        finally:
            self.__conn.close()
    def executeSelect(self , sql):
        self.__conn = pymysql.connect(host = self.__dbhost , user = self.__dbuser, passwd = self.__dbpass, db = self.__dbname, charset='UTF8')
        try:
            with self.__conn.cursor() as cursor:
                # Read a single record
                cursor.execute(sql)
                result = cursor.fetchone()
                print(result)
        finally:
            self.__conn.close()



