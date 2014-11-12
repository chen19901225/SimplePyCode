import collections
import re

__author__ = 'cqh'
def getIndexItem_Or_LastItem(param_list,param_index):
    if param_index>=len(param_list):
        return  param_list[-1]
    else:
        return param_list[param_index]

def getList(in_arg):
    if isinstance(in_arg,collections.Iterable) and hasattr(in_arg,'__iter__'):

        return in_arg
    else:
        if re.match(r'\[[^]]+\]',in_arg):
            return getList(eval(in_arg))
        else:
            return [in_arg]


def update_option(in_options,include_key=None,in_func=None):
    if not in_func:
        return
    else:
        update_key_list=include_key or in_options.keys()
        for key in in_options:
            if key in update_key_list:
                in_options[key]=in_func(in_options[key])

def get_childOrderDict(parent_dict,child_keys):
    re_dict=collections.OrderedDict()
    for key in child_keys:
        if key in parent_dict:
            re_dict[key]=parent_dict[key]
    return re_dict