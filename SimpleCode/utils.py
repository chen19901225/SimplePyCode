#coding:utf-8
from codecs import StreamReaderWriter
from collections import Iterable
import os
import re
import string


def try_get_list(inItem):
    if isinstance(inItem,Iterable) and not isinstance(inItem,basestring):
        return inItem
    else:
        return (inItem,)

def serial_func(func_list,**kwargs):
    result=kwargs
    for func in func_list:
        result=func(**result)
    return result

def serial_func_for_oneItem(func_list,param_item):
    result_item=param_item
    for func in func_list:
        result_item=func(result_item)
    return result_item



def try_get_childDict(sourcedict,*keyname):
    new_dict=dict.fromkeys(keyname)
    for key in keyname:
        new_dict[key]=sourcedict[key]
    return new_dict



def try_get_containedElement(search_string,key_tuple):
    found,element=False,None
    for key in key_tuple:
        if key in search_string:
            found,element=True,key
            break
    return found,element


class MergedStreamReadWriter(StreamReaderWriter):
    def __init__(self,*instreams):
        self._streams=instreams

    def write(self, data):
        for stream in  self._streams:
            stream.write(data)

def get_line_with_indent(py_line):
    """

    py_line:文件行
    return: 一个元祖,(缩进，去掉缩进的代码行)
    """
    if not py_line:
        return None,None
    for index in range(len(py_line)):
        if py_line[index] in   string.whitespace:
            continue
        else:
            break
    if index==0:
        return '',py_line
    else:
        return py_line[:index-1],py_line[index:]


condition_re=re.compile(r'^((?:[^\[]+)?)(?:\[([^\]]+)\])?$')



def get_element_from(a,ele_name):
    if isinstance(a,dict):
        return a[ele_name]
    else:
        getattr(a,ele_name)


#only for dict
def get_value_by_search_path(dataitem,search_path):
    #if not isinstance(search_path,unicode):
        #search_path=search_path.decode('utf-8')
    search_path_list=search_path.strip().split('.')

    def get_result_of_slice(param_data,search_slice):
        search_match=condition_re.search(search_slice)
        if not search_match:
            raise ValueError,search_slice+"不匹配"
        else:
            _attribute,_condition=None,None
            if len(search_match.groups())>1:
                _attribute,_condition=search_match.groups()
            else:
                _attribute=search_match.groups()[0]
            if _attribute:
                param_data=get_element_from(param_data,_attribute)
            if _condition:
                assert isinstance(param_data,Iterable),str(param_data)+"不是可迭代的"
                search_name,matched_value=re.sub('\s+','',_condition).split('=')
                if matched_value.startswith('"') and matched_value.endswith('"'):
                    matched_value=matched_value.strip('"')
                else:
                    matched_value=float(matched_value)

                for param_item in param_data:
                    if get_element_from(param_item,search_name)==matched_value:
                        return param_item
                raise ValueError,"条件:"+_condition+" not exist!"
            else:
                return param_data

    for search_path_slice in search_path_list:
        dataitem=get_result_of_slice(dataitem,search_path_slice)

    return dataitem

def walk_generator_list(*generator_list):
    for walk_generator in generator_list:
        for walk_item in walk_generator:
            yield walk_item




def print_all_item(item):

    def get_str(item):
        return_str=""
        if isinstance(item,Iterable) and not isinstance(item,basestring):
            for inner_item in item:
                return_str+=get_str(inner_item)
        else:
            return_str+=str(item)+' '
        return return_str

    p_str=get_str(item)

    print p_str





def find_meeted_files(dir_name,match_filter_func,handler_result_func=print_all_item):

    for walk_root,walk_dir_list,walk_file_list in os.walk(dir_name):
        #yield (yield find_uncommit_files_underDir(walk_root,walk_dir_list))
        #yield (yield find_uncommit_files_underDir(walk_root,walk_file_list))
        for  matched_item in walk_generator_list(match_filter_func(walk_root,walk_file_list)):
              handler_result_func(matched_item)



if __name__=="__main__":
    d={"l1":[{"name":"a","value":"chen"},{"name":"b","value":"bbbbbb"},{"name":"c","value":"cfun"}],"lv2":"My Name is chenqinghe"}
    print get_value_by_search_path(d,'l1[name="c"].value')





