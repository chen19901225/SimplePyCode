#coding=utf-8
import datetime
from ComHelper.ConvertHelper import   get_db_return_obj
from ComHelper.otherCommon import getMD5, wrap_after_action
from class_def import TB_User_Class_Name
import class_def


class TB_User(object):
    def __init__(self,**kwargs):
        self.Uid=0
        self.Uaccount=""
        self.Nickname=""
        self.Pwd=""
        self.Mobile=""
        self.Iconid=0
        self.Role=0
        self.Disable=0
        self.CreateTime=datetime.datetime.now()
        self.Memo=""
        self.__dict__.update(**kwargs)

    def isavailable_return(self):
        success_return=True
        if not  self.Uid or  not self.Nickname or  self.Disable:
            success_return=False
        return success_return
    def __unicode__(self):
        return self.Mobile

static_available_user=None

user_sql_base="""
 select
      a.uid as Uid,
      a.uaccount as Uaccount,
      a.pwd as Pwd,
      a.nickname as Nickname,
      a.mobile as Mobile,
      a.iconid as Iconid ,
      a.role as Role,
      a.memo as Memo
      from TB_User a
"""

def get_user_bydb(param_sql):
    return get_db_return_obj(class_def.TB_User_Class_Name,param_sql)

def get_user_available_slice(table_alias):
    table_alias='a' if  not table_alias else table_alias

    return '{0}.disable=0 '.format(table_alias)

def get_available_user():
    global  static_available_user
    if not  static_available_user:
        get_available_user_sql="""
        select
      a.uid as Uid,
      a.uaccount as Uaccount,
      a.pwd as Pwd,
      a.nickname as Nickname,
      a.mobile as Mobile,
      a.iconid as Iconid ,
      a.role as Role,
      a.memo as Memo
      from TB_User a where   a.disable=0 and a.Role=5
      LIMIT 1
        """
        static_available_user=get_db_return_obj(TB_User_Class_Name,get_available_user_sql)
    return static_available_user

def get_user_by_mobile(mobile):
    if not mobile:
        mobile=mobile.strip()
    assert mobile not in (None,''),"手机号不能为空"

    get_user_sql="""
    select
      a.uid as Uid,
      a.uaccount as Uaccount,
      a.pwd as Pwd,
      a.nickname as Nickname,
      a.mobile as Mobile,
      a.iconid as Iconid ,
      a.role as Role,
      a.memo as Memo
      from TB_User a
      where {user_available} and mobile={mobile}
    """.format(user_available=get_user_available_slice(),mobile=mobile)

    local_user=get_user_bydb(get_user_sql)

    assert local_user is not None,"手机号对应的帐户不存在"

    return local_user

def get_user_withRole_byMobile(mobile,role):
    local_user=get_user_by_mobile(mobile)
    if local_user.Role==role:
        return local_user
    else:
        return None


def get_user_RoleMerchant_by_mobile(mobile):

    return get_user_withRole_byMobile(mobile,5)
















class RegUser(object):
    def __init__(self,**kwargs):
        self.CellPhone=""
        self.Pwd=""
        self.Name=""
        self.ImgIndex=0
        self.VCode=""
        self.__dict__.update(kwargs)

if __name__=="__main__":
    assert get_available_user().isavailable_return()==True,"获取用户的数据失败"

