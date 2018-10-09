#encoding:utf-8
"""
Manage MySQL database
Select: default 'distinct select'
"""
import ConfigParser
import MySQLdb
import os

class MysqlManage:
    conf = ConfigParser.ConfigParser()
    conf.read("configuration.conf")

    def __init__(self, rawtable='sys_rawdata',db_name=''):
        self.name = MysqlManage.conf.get('db', 'name')
        self.host = MysqlManage.conf.get('db', 'host')
        self.user = MysqlManage.conf.get('db', 'user')
        self.password = MysqlManage.conf.get('db', 'password')
        self.charset = MysqlManage.conf.get('db', 'charset')
        self.rawtable = rawtable

    # Establish the connection to database
    def connect(self):
        conn = MySQLdb.connect(
            db=self.name,
            host=self.host,
            user=self.user,
            passwd=self.password,
            charset=self.charset
        )
        return conn

    # The argument conlumns is a string like 'apkName, versionCode, versionName'
    def select(self, columns='', condition=''):
        db = self.connect()
	table=self.rawtable
        mysql_contents = ()
        cursor = db.cursor()
        if condition == '':
            sql = "select " + columns + "  from " + table
        else:
            sql = "select " + columns + "  from " + table + " where " + condition
        cursor.execute(sql)
        mysql_contents = cursor.fetchall()
        db.close()
        return mysql_contents

    def insert(self, column, value):
        db = self.connect()
        cur = db.cursor()
        sql = 'INSERT INTO ' + self.rawtable + column
        try:
            cur.execute(sql % value)
            db.commit()

        except Exception as e:
            print e
            db.rollback()
        db.close()

if __name__ == '__main__':
    columns = 'apkName'
    mysql_manage = MysqlManage()
    apkname = mysql_manage.select(columns)
    for name in apkname:
        print name[0]
