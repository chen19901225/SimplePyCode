__author__ = 'Administrator'
#coding=utf-8
from ComHelper.PathHelper import Get_Auth_User_class_Name
from UserService.UrlHelper.UserDataHelper import get_available_user
from ComHelper.ConvertHelper import   get_url_return_obj
Auth_User_class_Name="UserService.Login.Login"

def get_login_obj(mobile,pwd):
    login_url="""
    YellowPageMap/Usermanage.ashx?a=Login&data={{"n":"{0}","pwd":"{1}"}}
    """.format(mobile,
               pwd)

    local_loged_user=get_url_return_obj(Get_Auth_User_class_Name(),login_url)#获取登录对象
    return local_loged_user


def cheshi_login_byUrl(user=None):
    db_user=get_available_user() if not user else user
    local_loged_user=get_login_obj(db_user.Mobile,db_user.Pwd)
    assert  local_loged_user.isavailable_return()==True,"用户登录失败"
    get_logedinfo_Bykey_url="""
    YellowPageMap/Usermanage.ashx?a=GetLogInfoByKey&data={{"key":"{0}"}}
    """.format(local_loged_user.Key)
    second_get_loged_user=get_url_return_obj(Auth_User_class_Name,get_logedinfo_Bykey_url)#通过会话ID获取登录信息
    assert second_get_loged_user.isavailable_return()==True,"用户获取登陆信息失败"
    assert local_loged_user.loginInfo_isequal(second_get_loged_user,False)==True,"用户获取登陆信息，与用户登录时获取的信息不一致"



def cheshi_register_byUrl():
    pass




if __name__=="__main__":
    cheshi_login_byUrl()