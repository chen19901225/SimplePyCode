#coding:utf-8
from collections import OrderedDict
import datetime
import json
import random

import string
from ComHelper.ConvertHelper import get_url_return_dict, get_obj_bydict, url_action_success, \
    exactlist_fromdict
from ComHelper.otherCommon import randchoice
from DateTimeJsonEncoder import DatetimeJsonEncoder
from YW_Cheshi.model.Food import Food

from YW_Cheshi.url_data_helper.LoginYW_Helper import cheshi_loginwiYW_byUrl_Success
import class_def
import setreader

__author__ = 'Administrator'

def get_MenuLabel_bydict(parm_dict):
    return get_obj_bydict(class_def.TB_MenuLabel_Name,parm_dict)

def Replace_FoodList(menulabelList,old_stri,new_str):
    for menulabel in menulabelList:
        menulabel.tags=string.replace(menulabel.tags,old_stri,new_str)

def get_first_menuLabel(merchant):
    return cheshi_getAllMenuLabel_ByMerchant(merchant)[0]

def Update_MenuLabel_List(Source_ML_list,update_id,new_menuname):
    for  temp_menulabel in Source_ML_list:
        if  temp_menulabel.id==update_id:
            temp_menulabel.lname=new_menuname



def isequal_list(old_menu_list,new_menu_list):


    assert len(old_menu_list)==len(new_menu_list),"更改导致标签数发生了改变"

    #assert old_menu_list==new_menu_list,"更新成功了"
    for index,old_menu_obj in enumerate(old_menu_list):
        new_menu_obj=new_menu_list[index]
        assert old_menu_obj==new_menu_obj,"更新没有成功"

def get_exist_count(lname,menu_list):
    e_count=0
    for menu_obj in menu_list:
        if lname==menu_obj.lname:
            e_count+=1
    return e_count

def get_menuLabel_byMLid(merchant,mlid):
    return [ menulabel for  menulabel in cheshi_getAllMenuLabel_ByMerchant(merchant) if menulabel.id==mlid][0]


def exact_tags_byIndexes(indexs,menulabel_list):
    matched_menulist=[ menulabel for index,menulabel in enumerate(menulabel_list) if index in indexs]
    return [menulabel.id for menulabel in matched_menulist],' '.join([ str(menulabel.id)+'.'+menulabel.lname for menulabel in matched_menulist])


def exact_list_from_dict(param_dict):

    #获取数组对象
    dict_list=param_dict.get('collection_infos',[])
    return exactlist_fromdict(dict_list,get_MenuLabel_bydict)


def get_menulabellist_byUrl(param_url):
    "通过URL获取菜式标签数组"
    url_res_dict=get_url_return_dict(param_url)
    assert url_res_dict.get("Status","-1")==0,"获取菜式标签失败"
    return exact_list_from_dict(url_res_dict)



def cheshi_getAllMenuLabel(key):
    getallMenuLabel_url="""
    %s/YouWeiMerchant/MenuLabel.ashx?a=getallmenulabel&data={"key":"%s"}
    """%(class_def.YW_URL_Base,key)
    menul_list=get_menulabellist_byUrl(getallMenuLabel_url)
    return menul_list


def cheshi_getAllMenuLabel_ByMerchant(merchant):
    "根据商户获取所有 自己的菜式标签"
    #obj_list= cheshi_getAllMenuLabel(merchant.Key)

    second_list=cheshi_getAllMenuLabel_ByMid(merchant,merchant.MerchantId)
    #isequal_list(obj_list,second_list)
    return second_list


def cheshi_getAllMenuLabel_ByMid(merchant,mid):
    "根据商户ID获取所有的菜式标签"
    get_allmenulabel_byMid_str="""
     %s/YouWeiMerchant/MenuLabel.ashx?a=getallmenulabel&data={"mid":%s}
    """%(class_def.YW_URL_Base,mid)

    return get_menulabellist_byUrl(get_allmenulabel_byMid_str)





def cheshi_AddMenuLabel_ByMerchant(merchant,lname=None,old_menu_list=None):
    assert lname is not None,"菜式标签不能为空"

    inner_old_menu_list=old_menu_list
    if not inner_old_menu_list:
        inner_old_menu_list=cheshi_getAllMenuLabel_ByMerchant(merchant)

    if any(lname in  menulabel.lname  for menulabel in inner_old_menu_list):
        print "该标签已经存在，请添加其他标签"
        return old_menu_list

    addMenuLabel_url="""
    %s/YouWeiMerchant/MenuLabel.ashx?a=addmenulabel&data={"key":"%s","lname":"%s"}
    """%(class_def.YW_URL_Base,merchant.Key,lname)

    action_result=url_action_success(addMenuLabel_url)
    assert action_result==0,"添加菜式标签不成功"


    new_menu_list=cheshi_getAllMenuLabel_ByMerchant(merchant)

    old_lname_count=get_exist_count(lname,inner_old_menu_list)

    new_lname_count=get_exist_count(lname,new_menu_list)
    assert old_lname_count+1==new_lname_count
    return new_menu_list
    pass



def cheshi_update_firstMenuLabel(merchant,new_name,old_menu_list):
    #更新自己的的第一个菜式标签
    """

    :param merchant: 会话ID
    :param new_name:该菜式标签要更新的的新名称
    :param old_menu_list: 旧的菜式标签数组
    :return: 返回新的菜式标签数组
    """


    update_menu_id=old_menu_list[0].id
    #old_menu_list[0].lname=new_name

    return cheshi_updateMLabel_ByMLidAndMerchant(merchant,new_name,update_menu_id,old_menu_list)


def cheshi_updateMLabel_ByMLidAndMerchant(merchant,new_name,update_id,old_menu_list):
    """
    更新某个菜式标签的名称
    :param merchant:活动商户
    :param new_name: 更新后的菜式标签名称
    :param update_id:要更新的菜式标签ID
    :param old_menu_list: 旧的菜式标签数组
    :return:新的菜式标签数组
    """
    assert new_name is not None,"标签更新不能为空"

    if any(new_name in old_menulabel.lname  for old_menulabel in  old_menu_list):
        print "更新的标签名跟现有标签名存在冲突！"
        return old_menu_list

    Update_MenuLabel_List(old_menu_list,update_id,new_name)

    old_food_list=cheshi_getallFood(merchant,update_id)[1] #获取所有的菜式数组

    update_menu_obj=get_menuLabel_byMLid(merchant,update_id)

    Replace_FoodList(old_food_list,update_menu_obj.lname,new_name)

    update_menuLabel_url="""
    %s/YouWeiMerchant/MenuLabel.ashx?a=updatemenulabel&data={"key":"%s","lname":"%s","id":%s}
    """%(class_def.YW_URL_Base,merchant.Key,new_name,update_id)

    action_result=url_action_success(update_menuLabel_url)
    assert action_result==0,"添加菜式标签不成功"

    new_menu_list=cheshi_getAllMenuLabel_ByMerchant(merchant)

    local_old_menu_list=old_menu_list
    isequal_list(old_menu_list,new_menu_list)
    new_food_list=cheshi_getallFood(merchant,update_id)[1] #获取新的菜式数组

    isequal_list(old_food_list,new_food_list)

    return old_menu_list







def cheshi_delMlLabel_byMlidAndMerchant(merchant,deleteid,old_menu_list):
    """
    通过菜式标签ID以及活动商户来删除菜式标签
    :param merchant: 活动商户
    :param deleteid: 要删除的菜式标签ID
    :param old_menu_list: 旧的菜式标签数组
    :return:新的菜式标签数组
    """

    old_FoodList=cheshi_getallFood(merchant,deleteid)[1]

    delete_obj=get_menuLabel_byMLid(merchant,deleteid)

    del old_FoodList[:]

    Replace_FoodList(old_FoodList,delete_obj.lname,"")

    #new_Menulabellist=cheshi_delMlLabel_byMlidAndMerchant(merchant,deleteid,old_menu_list)

    del_mlid_url="""
    %s/YouWeiMerchant/MenuLabel.ashx?a=deletemenulabel&data={"key":"%s","ids":[%s]}
    """%(class_def.YW_URL_Base,merchant.Key,deleteid)

    del_success=url_action_success(del_mlid_url)
    assert del_success==0,"此次操作失败"

    new_FoodList=cheshi_getallFood(merchant,deleteid)[1]

    if any(delete_obj.lname in new_Food.tags  for  new_Food in new_FoodList):
        raise ValueError,"菜式上的标签没有更改掉"
    isequal_list(old_FoodList,new_FoodList)
    return cheshi_getAllMenuLabel_ByMerchant(merchant)



def cheshi_getFoodInfo(merchant,foodId):

    getfoodInfo_url="""
    %s/YouWeiFood/MerchantFood.ashx?a=GetFoodInfo &data={"key":"%s","id":%s, "isedit":0}
        """%(class_def.YW_URL_Base,merchant.key,foodId)
    pass


def cheshi_addFood(merchant,param_food,ml_list):
    """
    添加食品
    :param merchant:活动商户
    :param param_food: 要添加的食品
    :param ml_list:要添加的菜式标签ID数组
    :return:None
    """
    old_foodlist_dict=OrderedDict()
    for ml_id in ml_list:
        old_foodlist_dict[ml_id]=cheshi_getallFood(merchant,ml_id)[0]

    food_str=json.dumps(param_food.__dict__,cls=DatetimeJsonEncoder)
    addFood_url="""
    %s/YouWeiFood/MerchantFood.ashx?a=SendFood&data={"key":"%s","id":0, "p":%s}
    """%(class_def.YW_URL_Base,merchant.Key,food_str)
    action_success=url_action_success(addFood_url)
    assert action_success==0,"添加菜式不成功"

    new_foodlist_dict=OrderedDict()
    for ml_id in ml_list:
        new_foodlist_dict[ml_id]=cheshi_getallFood(merchant,ml_id)[0]

    if any(new_foodlist_dict.get(ml_id,0)!=old_foodcount+1  for ml_id,old_foodcount in old_foodlist_dict.iteritems()):
        raise ValueError,"添加菜式失败"


def cheshi_getallFood(merchant,menulabel_id=0):
    getallFoodList_url="""
    %s/YouWeiFood/MerchantFood.ashx?a=GetMFoodList&data={"key":"%s","mid":%s,"lid":%s,"index":1,"size":500}
    """%(class_def.YW_URL_Base,merchant.Key,merchant.MerchantId,menulabel_id)
    url_res_dict=get_url_return_dict(getallFoodList_url)
    assert url_res_dict["Status"]==0,"获取所有菜单失败"

    all_Food_dict=url_res_dict.get("Publishes",[])
    if not all_Food_dict:
        all_Food_dict=[]

    Count,FoodList=url_res_dict["Count"],exactlist_fromdict(all_Food_dict,lambda innerdict:  get_obj_bydict(class_def.Cls_Food_Name,innerdict))
    assert Count==len(FoodList),"菜式数目对不上"
    return Count,FoodList

def product_BasicFoodData(active_user):
    """
    产生食品的基本数据
    :param active_user:活动商户
    :return:食品
    """
    new_food_dict=dict(
        mid=cur_user.MerchantId,
        price=123,
        memo="",
        pubtime=datetime.datetime.now(),
        starttime=datetime.datetime.now(),
        endtime=datetime.datetime(2036,1,1),
        tags=""
    )

    return Food(**new_food_dict)

def product_FoodData_Collection(cur_user):
    #添加测试数据

    all_menu_label=cheshi_getAllMenuLabel_ByMerchant(cur_user)#获取所有的菜式标签
    food_basic=datetime.datetime.now().strftime("%d-%H-%M")
    food_index=0
    for ml_index,menu_label in enumerate(all_menu_label):
        food_index+=1
        new_Food=product_BasicFoodData(cur_user)
        addfood_menulabel_list,new_Food.tags=exact_tags_byIndexes([ml_index],all_menu_label)

        new_Food.pname=food_basic+str(food_index)
        cheshi_addFood(merchant=cur_user,param_food=new_Food,ml_list=addfood_menulabel_list)

    print "添加菜式数据已经完成"


def cheshi_del_firstmenulabel(merchant,old_menu_list):
    local_menu_list=old_menu_list
    delete_menu_obj=local_menu_list.pop(0)
    #return cheshi_delMLabel_bymlidAndKey(delete_menu_obj.id, key, local_menu_list)
    return cheshi_delMlLabel_byMlidAndMerchant(merchant,delete_menu_obj.id,local_menu_list)








def cheshi_clearMenuLabel(merchant):

    del_menulabel_url="""
    %s/YouWeiMerchant/MenuLabel.ashx?a=deletemenulabel&data={"key":"%s","ids":[]}
    """%(class_def.YW_URL_Base,merchant.Key)

    action_result=url_action_success(del_menulabel_url)
    assert action_result==0,"清空菜式标签不成功"

    new_menu_list=cheshi_getAllMenuLabel(merchant.Key)

    assert new_menu_list in (None,[]),"清空菜式标签失败"
    return []



def Product_MLData_Collection(merchant):
    first_menu = u'标签一'
    second_menu = u'标签二'
    menu_list = [second_menu, first_menu]
    cheshi_AddMenuLabel_ByMerchant(merchant,first_menu,old_menu_list=None)
    # 清空所有菜式标签
    #old_menu_list=cheshi_clearmenuLabel(key)
    old_menu_list = cheshi_getAllMenuLabel_ByMerchant(merchant)
    #old_menu_list = cheshi_getAllMenuLabel_ByMerchant(merchant, first_menu, old_menu_list=old_menu_list)
    #更新标签
    old_menu_name = old_menu_list[0].lname
    new_menu_name = product_new_menu_name(old_menu_name)
    old_menu_list = cheshi_update_firstMenuLabel(merchant, new_menu_name, old_menu_list=old_menu_list)
    cheshi_del_firstmenulabel(merchant, old_menu_list)
    insert_menu_list = [u"小吃", u"早餐", u"酸辣粉", u"麻辣烫"]
    for for_menulabel in insert_menu_list:
        old_menu_list = cheshi_AddMenuLabel_ByMerchant(merchant, for_menulabel, old_menu_list)


def product_new_menu_name(old_ml_name):

    if len(old_ml_name)>4:
        new_ml_name=old_ml_name[:-1]+randchoice(string.ascii_letters)
        if old_ml_name==new_ml_name:
            return product_new_menu_name(old_ml_name)
    else:
        new_ml_name=old_ml_name+randchoice(string.ascii_letters)
    return new_ml_name


if __name__=="__main__":
    cur_user=cheshi_loginwiYW_byUrl_Success()
    key=cur_user.Key




    Product_MLData_Collection(cur_user)

    #Product_MLData_Collection(key)
    #product_FoodData_Collection(cur_user)



    #old_menu_list=cheshi_delMlLabel_byMlidAndMerchant(cur_user,78,old_menu_list)



    first_menulabel=get_first_menuLabel(cur_user)
    #print first_menulabel.lname

    new_name=product_new_menu_name(first_menulabel.lname)

    print new_name
    old_menu_list=cheshi_getAllMenuLabel_ByMerchant(cur_user)

    cheshi_update_firstMenuLabel(cur_user,new_name,old_menu_list)






    all_Food=cheshi_getallFood(cur_user,0)
    #Product_CheshiData()







    print "OK"
