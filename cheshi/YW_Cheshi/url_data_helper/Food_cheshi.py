#coding:utf-8
from collections import OrderedDict
import datetime
from ComHelper.ConvertHelper import url_action_success, wrap_sendUrlNoneQuery, get_url_return_dict, exactlist_fromdict, \
    get_obj_bydict
from DateTimeJsonEncoder import DatetimeJsonEncoder
from YW_Cheshi.model.Food import Food
from YW_Cheshi.url_data_helper.LoginYW_Helper import cheshi_loginwiYW_byUrl_Success
from YW_Cheshi.url_data_helper.cheshi_MenuLabel import cheshi_getAllMenuLabel_ByMerchant, exact_tags_byIndexes
import class_def
import json
__author__ = 'Administrator'






if __name__=="__main__":
    cur_user=cheshi_loginwiYW_byUrl_Success()
    oldcount,oldFoodList=cheshi_getallFood(cur_user,0)
    assert oldcount>0
    product_someData_forCheshi(cur_user)







    print "Over"








