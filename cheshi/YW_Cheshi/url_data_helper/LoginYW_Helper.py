#coding:utf-8
from ComHelper.ConvertHelper import get_url_return_obj, getclass, get_url_return_dict, get_obj_bydict
from UserService.UrlHelper.UserDataHelper import get_available_user
from class_def import Login_YW_path, TB_User_Class_Name

__author__ = 'Administrator'


def get_loginwithYW_obj(mobile,pwd):
    local_dict=get_loginwithYW_dict(mobile,pwd)
    local_loged_user=get_obj_bydict(Login_YW_path,local_dict)#获取登录对象
    return local_loged_user
def get_loginwithYW_dict(mobile,pwd):
    login_url="""
    YellowPageMap/Usermanage.ashx?a=Login_YW&data={{"n":"{0}","pwd":"{1}","logtype":4}}
    """.format(mobile,
               pwd)
    local_dict=get_url_return_dict(login_url)
    return local_dict

def cheshi_loginwiYW_byUrl_Success():
    #db_user=get_available_user() if not user else user

    mobile,pwd='22222222222','E10ADC3949BA59ABBE56E057F20F883E'
    #mobile,pwd='13060655073','E10ADC3949BA59ABBE56E057F20F883E'
    local_loged_user=get_loginwithYW_obj(mobile,pwd)
    assert  local_loged_user.isavailable_return()==True,"用户登录失败"
    assert local_loged_user.isavailable_return_YW()==True,"有味商户的商户类型不应该为0"
    get_logedinfo_Bykey_url="""
    YellowPageMap/Usermanage.ashx?a=GetLogInfoByKey_YW&data={{"key":"{0}","Logtype":4}}
    """.format(local_loged_user.Key)
    second_get_loged_user=get_url_return_obj(Login_YW_path,get_logedinfo_Bykey_url)#通过会话ID获取登录信息
    assert second_get_loged_user.isavailable_return()==True,"用户获取登陆信息失败"
    assert local_loged_user.loginInfo_isequal(second_get_loged_user,False)==True,"用户获取登陆信息，与用户登录时获取的信息不一致"
    return local_loged_user


def cheshi_loginwiYW_byUrleshi_Failure():
    mobile,pwd='15914354390','E10ADC3949BA59ABBE56E057F20F883E'
    local_loged_user=get_loginwithYW_obj(mobile,pwd)

    assert  local_loged_user.isavailable_return()==True,"用户登录失败"
    assert local_loged_user.isavailable_return_YW()==False,"有味商户的商户类型不应该为0"
    get_logedinfo_Bykey_url="""
    YellowPageMap/Usermanage.ashx?a=GetLogInfoByKey_YW&data={{"key":"{0}"}}
    """.format(local_loged_user.Key)
    second_get_loged_user=get_url_return_obj(Login_YW_path,get_logedinfo_Bykey_url)#通过会话ID获取登录信息
    assert second_get_loged_user.isavailable_return()==True,"用户获取登陆信息失败"
    assert local_loged_user.loginInfo_isequal(second_get_loged_user,False)==True,"用户获取登陆信息，与用户登录时获取的信息不一致"

def get_key_byMerchantAndlogtype(merchantId,logtype=4):
    pass


def cheshi_login_YW_YWType(user=None):
    pass

def cheshi_getuserInfobykey_YW(key=None):
    pass


if __name__=="__main__":

    cheshi_loginwiYW_byUrl_Success()
    cheshi_loginwiYW_byUrleshi_Failure()

