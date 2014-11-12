#encoding=utf-8
import functools

import urllib2
import requests

__author__ = 'Administrator'

from ComHelper import PathHelper
from ComHelper.dbHelper import get_cursor, cursor_close
import LogHelper
import urllib,json,re
from setreader import get_static_setting_reader

def get_url_return_obj(obj_class_name,param_url):
    url_return_dict=get_url_return_dict(param_url)
    assert url_return_dict["Status"]==0,"网页获取信息失败"
    return get_obj_bydict(obj_class_name,url_return_dict)


def get_obj_bydict(obj_class_name,url_dict):
    local_class=getclass(obj_class_name)
    return_obj=local_class(**url_dict)
    return return_obj



def get_url_return_objlist(param_url,des_cls_name,collection_prop_name="collection_infos"):
    return_dict=get_url_return_dict(param_url)
    assert return_dict["Status"]==0,"获取网页信息失败"
    collection_list=return_dict.get(collection_prop_name,[])
    collection_list=[] if not collection_list else collection_list
    return exactlist_fromdict(collection_list,lambda  param_dict:get_obj_bydict(des_cls_name,param_dict) )


def get_url_return_dict(param_url):
    url=param_url.strip()
    if  not is_contain_domain(url) and not  url.startswith('icypmweb.jhnavi.com'):
        url=path_join(get_static_setting_reader().domain_url,url)

    #send_url=urllib.quote(url)
    LogHelper.loginfo(url)#记录日志
    if not isinstance(url,unicode):
        url=url.decode('utf-8')
    #send_url= urllib.quote(url,":?=/&%")
    url_hood=requests.get(url)
    url_return_str=url_hood.text
    url_return_dict=json.loads(url_return_str)
    return url_return_dict

def url_action_success(param_url):
    url_res_dict=get_url_return_dict(param_url)
    action_succs=url_res_dict.get('Status',-1)
    return action_succs

def assert_url_action_success(param_url):
    action_status=url_action_success(param_url)
    assert  action_status==0,"该次请求失败!status:"+str(action_status)

def get_add_action_id(param_url):
    url_res_dict=get_url_return_dict(param_url)
    action_success=url_res_dict.get('Status',-1)
    assert action_success==0,"该次请求失败!status:"+action_success

    inserted_id= url_res_dict.get("Id",-1)
    assert inserted_id>0,"插入操作失败"
    return inserted_id


def is_contain_domain(url):
    "判断一个链接是否含有域名"
    is_contain=True
    if url.startswith('/'):
        in_contain=False
    elif not  re.match('^[^":]+://.*',url):
        first_sep_index=url.index('/')
        if not  '.' in url[:first_sep_index]:
            is_contain=False
    return is_contain
def path_join(domain_url, extend):
    out_url=domain_url
    if not  domain_url.endswith('/'):
        out_url=out_url+'/'
    if extend.startswith('/'):
        extend=extend[1:]

    out_url=out_url+extend
    return out_url


def get_db_return_obj(obj_class_name,param_sql):
    re_list=get_db_return_list(obj_class_name,param_sql)
    if not re_list:
        return None
    else:
        return re_list[0]



def get_db_return_list(obj_class_name,param_sql):
    get_cursor().execute(param_sql)
    local_class=getclass(obj_class_name)
    re_list=[]
    for record in get_cursor():
        re_list.append(local_class(**record))
    get_cursor().connection.commit()
    get_cursor(True)
    return re_list

def getclass(obj_class_name):
    """
    根据类的路径，获取类对象
    """
    class_split_index=obj_class_name.rindex('.')
    model_name=obj_class_name[:class_split_index]
    class_name=obj_class_name[class_split_index+1:]

    _model=__import__(model_name)
    model_split_index=obj_class_name.index('.')
    path_arr=obj_class_name[model_split_index+1:].split('.')

    def  iter_get_class_(arr_index,param_model):
        if arr_index==len(path_arr)-1:
            return getattr(param_model,path_arr[arr_index])
        else:
            return iter_get_class_(arr_index+1,getattr(param_model,path_arr[arr_index]))
    return iter_get_class_(0,_model)

def Validate_UrlReturnObj(obj_class_name,param_url):
    return_obj=get_url_return_obj(obj_class_name,param_url)
    url_get_success=False
    if hasattr(return_obj,"isavailable_return"):
        url_get_success=return_obj.isavailable_return()
    else:
        raise  NameError,"该类没有实现isavailable_return方法"
    return url_get_success


def wrap_sendUrlNoneQuery(description_name='该次'):
    def wrap_function(fn):
        @functools.wraps(fn)
        def wrapped(*args,**kwargs):
            action_url=fn(*args,**kwargs)
            action_success=url_action_success(action_url)
            assert action_success==0,description_name+"操作不成功"
        return wrapped
    return wrap_function

def exactlist_fromdict(source_dict,funcname):
    if not source_dict:
        dict_list=[]
    obj_list=[]
    for inner_dict  in source_dict:
        obj_list.append(funcname(inner_dict))
    return obj_list

if __name__=="__main__":
    #TB_User_Class_Name="UserService.UrlHelper.UserDataHelper.TB_User"
    print  getclass(PathHelper.Get_TB_User_Path())

