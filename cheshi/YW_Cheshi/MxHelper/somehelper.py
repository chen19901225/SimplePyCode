#coding=utf-8
import datetime
from ComHelper.dbHelper import executeNoQuery_sql

from ComHelper.otherCommon import getMD5, wrap_after_action
from UserService.CheShiHelper.UserHelper import get_login_obj

__author__ = 'Administrator'


def RegisterUser_ByDB_orginpwd(mobile,pwd,Role=4):
    encrypt_pwd=getMD5(pwd)

    RegisterUser_ByDB(mobile,encrypt_pwd,Role)

    print "插入成功"

@wrap_after_action(get_login_obj)
def RegisterUser_ByDB(mobile,pwd,Role=4):
    insert_user_sql="""
    insert into TB_User(mobile,pwd,role,iconid,disable,createtime) value('{mobile}','{pwd}',{role},0,0,'{createtime}')
    """.format(mobile=mobile,pwd=pwd,role=Role,createtime=datetime.datetime.now())

    executeNoQuery_sql(insert_user_sql)


if __name__=="__main__":
     RegisterUser_ByDB_orginpwd('15876958440','123456')