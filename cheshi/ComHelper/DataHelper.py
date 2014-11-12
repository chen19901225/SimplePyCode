import numbers
#coding=utf-8
from UserService.CheShiHelper.UserHelper import get_login_obj
#from ComHelper.dbHelper  import  get_cursor
try:
    get_cursor()
except Exception as e:
    from ComHelper.dbHelper import  get_cursor, getsingle
get_session_base_sql="""
select sessionid from TB_LoginInfo  where logoutTime is null and  ltype!=1
"""

active_session_list=[]

def get_active_session_list():
    global  active_session_list
    if not active_session_list:
        inner_query_active_session_list()
    return active_session_list

def inner_query_active_session_list():
    del active_session_list[:]
    get_action_session_sql_str=get_session_base_sql+" LIMIT 10 "
    get_cursor().execute(get_action_session_sql_str)
    for line in get_cursor():
        active_session_list.append(line.values()[0])


def get_sessionid_by_cardid(param_cardid):
    "通过名片ID获取登陆的用户ID"
    cardid=0
    if isinstance(param_cardid,(int,long)):
        cardid=param_cardid
    else:
        cardid=param_cardid.Id or param_cardid.id

    get_usrinfo_sql="""
    select u.uid,u.mobile,u.pwd
    from TB_User u ,TB_Card c
    where u.uid=c.uid and c.cid={0} and u.disable=0
    """.format(cardid)
    get_cursor().execute(get_usrinfo_sql)
    db_dict=get_cursor().fetchone()
    assert db_dict is not None,cardid +"名片的的用户不存在或者被禁用"

    get_session_sql="""
    {session_sql_base}
    and uid={Uid}
    LIMIT 1
    """.format(session_sql_base=get_session_base_sql,Uid=db_dict["uid"])

    get_cursor().execute(get_session_sql)
    session_dict=get_cursor().fetchone()

    if not session_dict:#用户未登录
        login_user=get_login_obj(db_dict["mobile"],db_dict["pwd"])
        return login_user.Sessionid
    else:
        return session_dict["sessionid"]


def get_uid_by_session(sessionid):
    get_sql="""select uid
    from TB_LoginInfo where sessionid={session_id}
    """.format(session_id=sessionid)
    return getsingle(get_sql)



if __name__=="__main__":
    assert len(get_active_session_list())>0,'没有活动用户了'
    get_sessionid_by_cardid(2493)


