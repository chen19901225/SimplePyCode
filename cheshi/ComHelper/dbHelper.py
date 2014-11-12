__author__ = 'Administrator'
#coding=utf-8
import MySQLdb
import MySQLdb.cursors
from setreader import get_static_setting_reader
from ComHelper.otherCommon import   get_child_dict

class dbHelper(object):
    def __init__(self,host='192.168.1.180',user='root',passwd='jhnavigzjh',db='DBICYPM',port=3306,charset='utf8',cursorclass=MySQLdb.cursors.DictCursor):
        self.conn=MySQLdb.connect(host=host,user=user,passwd=passwd,db=db,port=port,charset=charset,cursorclass=cursorclass)
        self.cursor=None
        #self.cursorclass=cursorclass
    def Get_cursor(self,no_cache=False):
        if not self.cursor or no_cache:
            self.cursor=self.conn.cursor()
        return self.cursor
static_db_keyword=('host','user','passwd','db','port','charset')
static_dbhelper=None

def get_dbhelper(no_cache=False):
    global  static_dbhelper
    if not static_dbhelper or no_cache:
        if static_dbhelper:
            static_dbhelper.conn.close()
            static_dbhelper=None
        local_setting_reader_instance=get_static_setting_reader()
        static_db_keyword_dict=get_child_dict(local_setting_reader_instance.__dict__,static_db_keyword)
        #static_db_keyword_dict['port']=int(static_db_keyword_dict['port'])
        static_dbhelper=dbHelper(**static_db_keyword_dict)
    return static_dbhelper

def get_cursor(no_cache=False):
    local_dbhelper=get_dbhelper(no_cache)
    local_cursor= local_dbhelper.Get_cursor(no_cache)
    return local_cursor
def get_conn(no_cache=False):
    return get_dbhelper(no_cache).conn

def cursor_close():
    get_cursor().close()
def get_conn():
    local_dbhelper=get_dbhelper()
    return local_dbhelper.conn
def getsingle(exec_sql):
    get_cursor().execute(exec_sql)

    ret_dict=get_cursor().fetchone()
    if not ret_dict:
        return None
    return ret_dict.values()[0]

def executeNoQuery_sql(param_sql):
    get_cursor().execute(param_sql)
    get_conn().commit()

if __name__=="__main__":
    local_static_dbhelper=get_dbhelper()
    assert local_static_dbhelper!=None





