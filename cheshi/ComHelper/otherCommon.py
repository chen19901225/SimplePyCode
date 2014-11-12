#coding=utf-8
import functools
import math
import random
import urllib,json
import CardService

import UserService
import LogHelper
from datetime import datetime
import re
import string
import numbers
import struct

null=""
def string_isequal(str1,str2,ignore=True):
    if not  ignore:
        return  str1==str2
    else:
        return string_isequal(str1.lower(),str2.lower(),False)


def get_child_dict(source_dict,keytupe):
    ret_dict=dict()
    for key in keytupe:
        ret_dict[key]=get_matched_value_fromDict(source_dict,key)
    return ret_dict

def get_matched_value_fromDict(source_dict,key):
    if key in source_dict:
        return source_dict[key]
    for  source_key,value in source_dict.iteritems():
        if string_isequal(key,source_key,True):
            return value
    return None

def convert_datetime(time_str):
    time_re=re.compile('^(?P<Year>\d{4})-(?P<Month>\d{1,2})-(?P<Day>\d{1,2})\s+(?P<Hour>\d{1,2}):(?P<Minute>\d{1,2}):(?P<Seond>\d{1,2})$')
    if not  time_re.match(time_str):
        return None
    else:
        return datetime.strptime(time_str,"%Y-%m-%d %H:%M:%S")

def isbasicinstance(value):
    return isinstance(value,(numbers,basestring) )


def get_basevalue(**kwargs):
    assert len(kwargs)==1,"获取基础属性一次只允许获取一个"
    for key,value in kwargs.iteritems():
        if isbasicinstance(value):
            return value
        else:
            prop_name=key
            prop_pair=prop_name.split('_')
            prop_name=prop_pair[-1]#获取到属性名

            if hasattr(value,prop_name):
                return getattr(value,prop_name)
            prop_name=string.capitalize(prop_name)
            assert hasattr(value,prop_name),"对象不含有属性"+prop_name
            return getattr(value,prop_name)

def is_keys_equal(keys,dict1,dict2):
    if  not isinstance(dict1,dict):
        inner_dict1=dict1.__dict__
    else:
        inner_dict1=dict1
    if not isinstance(dict2,dict):
        inner_dict2=dict2.__dict__
    else:
        inner_dict2=dict2
    for key in keys:
        value1=inner_dict1.get(key,None)
        value2=inner_dict2.get(key,None)
        if  not value1 and not value2:
            continue
        if  value1!=value2:
            return False
    return True


def getbitvalue(str_value):
    if isinstance(str_value,(int)):
        return str_value
    return ord(str_value)

def wraper_cheshi_get(fn,validate_name=None):
    fn_name=fn.__name__
    maybe_validate_name=fn_name.split('_')[-1]
    if string_isequal(fn_name.split('_')[-2],'cheshi')==True:
        maybe_validate_name=None
    validate_name=validate_name or maybe_validate_name
    assert validate_name is not None,"验证方法必须要有"
    @functools.wraps(fn)
    def inner_wrapper(*args,**kwargs):
        pass_value=get_final_value(*args,**kwargs)
        ret_obj=fn(pass_value)
        assert  getattr(ret_obj,validate_name)()==True,"验证失败"
        return ret_obj
    return inner_wrapper


def get_final_value(*args,**kwargs):
    final_value=0
    assert len(args)<=1,"不能超过1个参数"
    if len(args)==1:
        prob_value=args[0]
        if isinstance(prob_value,(int,long,float,bool)):
            final_value=prob_value
        else:
            for key  in ("Id","ID","id","iD"):
                if hasattr(prob_value,key):
                    final_value=getattr(prob_value,key)
                    break

    else:
        assert len(kwargs)==1,"不能超过一个键值对"
        if len(kwargs)==1:
            key_name=kwargs.keys()[0].strip()
            attr_name=key_name.split('_')[-1]
            dict_value=kwargs.values()[0]
            assert hasattr(dict_value,attr_name)==True,"字典里面必须含有对应属性"

            final_value=getattr(dict_value,attr_name)



    return final_value

def product_random_str(param_str):
    if not param_str:
        return str(random.randint(0,9))
    else:
        prefix=param_str[:-1]
        return prefix+product_random_str("")


def wrap_after_action(after_function_name):
    def real_decorator(fn):
        @functools.wraps(fn)
        def wrapped(*args,**kwds):
            fn(*args,**kwds)
            target_func_code=after_function_name.func_code
            #target_func_code.co_argcount
            after_function_name(*args[0:target_func_code.co_argcount],**kwds)
        return wrapped
    return real_decorator

def randchoice(param_choices):
    choices= tuple(param_choices) if isinstance(param_choices,set) else param_choices
    index=int(math.floor(random.random()*(len(choices)-1)))
    return choices[index]





def getMD5(param_str):
    import hashlib
    hash=hashlib.md5()
    hash.update(param_str)
    re_str=hash.hexdigest()
    return string.upper(re_str)

def is_twolist_equal(list1,list2):
    assert len(list1)==len(list2),"两个列表长度不相等"

    for index1,value1 in enumerate(list1):
        assert value1==list2[index1], str(value1)+"不等于"+str(list2[index1])


def get_matched_list(source_list,filter_func):
    """
    for  source_element in source_list:
        if filter_func(source_element)==True:
            yield  source_element
    """
    return (source_ele for source_ele in source_list if filter_func(source_ele)==True)









def get_firstElement_ByProp(source_list,**kwargs):
    def func_getFirst(re_list):
        for for_obj in re_list:
            return for_obj

    return handler_list_withCondition(source_list,lambda  re_list:iter(re_list).next(),**kwargs)



def handler_list_withCondition(source_list,result_handler,**kwargs):
    def filter_func(obj):
        for prop_name,prop_value in  kwargs.iteritems():
            if obj.__getattribute__(prop_name)!=prop_value:
                return False
        return True
    return Funcfilter_ResultHandle(source_list,result_handler,filter_func)


def Funcfilter_ResultHandle(source_list,result_handler,filter_func):
    result_list=get_matched_list(source_list,filter_func)
    return result_handler(result_list)




def exist_Element_MatchCondition(source_list,**kwargs):

    def exist_element_func(re_list):
        for for_ele in re_list:
            return True
        return False

    return handler_list_withCondition(source_list,exist_element_func ,**kwargs )












if __name__=="__main__":
    struct.unpack(r'\x00')









