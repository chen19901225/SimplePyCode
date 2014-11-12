#coding:utf-8
import datetime
from ComHelper import otherCommon
from ComHelper.ConvertHelper import get_url_return_objlist, assert_url_action_success, get_add_action_id
from ComHelper.otherCommon import get_firstElement_ByProp
from YW_Cheshi.model.DeliveryAddress import DeliveryAddress
from YW_Cheshi.url_data_helper.LoginYW_Helper import cheshi_loginwiYW_byUrl_Success
import class_def
import json


address_set=set((u"天天向上学校",u"快乐大本营",u"越策越开心",u"暨南大学",u"中南大学",u"华南理工大学"))
contactman_set=set((u"冷叔",u"奶子D",u"刘皇叔",u"小八",u"赵洁",u"2009"))
contacttel_set=set((u"13242868033",u"1364031951",u"13750010200"))


def get_deliveryAddressList_byUrl(url):
    return get_url_return_objlist(url,class_def.Cls_DeliveryAddress)

def get_DeliveryAddress(merchant,**kwargs):
    assert len(kwargs)==1,"现在只支持一个参数"
    prop,value=kwargs.items()[0]
    create_DeliveryAddresslist=cheshi_getalldeliveryAddress(merchant)
    #return [ for_DeliveryAddress for for_DeliveryAddress in create_DeliveryAddresslist if for_DeliveryAddress.__getattribute__(prop)==value][0]

    return get_firstElement_ByProp(create_DeliveryAddresslist,**kwargs)




def exists_defaultDeliveryAddress(merchant):
    created_deliveryAddress_List=cheshi_getalldeliveryAddress(merchant)
    return otherCommon.exist_Element_MatchCondition(created_deliveryAddress_List,isdefault=1)





def get_NoneDefault_DeliveryAddress(merchant):
    return get_DeliveryAddress(merchant,isdefault=0)

def get_Default_DeliveryAddress(merchant):
    return get_DeliveryAddress(merchant,isdefault=1)







def cheshi_getalldeliveryAddress(merchant):
    getAllDeliveryAddress_url="""
    %s?a=getalladdresses&data={"key":"%s"}
        """%(class_def.base_deliveryaddress_url,merchant.Key)

    return get_deliveryAddressList_byUrl(getAllDeliveryAddress_url)

def cheshi_add_deliveryAddress(merchant,param_newAddress):
    old_deliveryAddress_list=cheshi_getalldeliveryAddress(merchant)



    add_deliveryAddress_url="""
    %s?a=addaddress&data={"key":"%s",%s}
    """%(class_def.base_deliveryaddress_url,merchant.Key,json.dumps(param_newAddress.__dict__).strip('{}'))

    inserted_id=get_add_action_id(add_deliveryAddress_url)

    param_newAddress.id=inserted_id

    new_deliveryAddress_list=cheshi_getalldeliveryAddress(merchant)

    if len(new_deliveryAddress_list)==1:#表示创建第一个送餐地址
       param_newAddress.isdefault=1

    old_deliveryAddress_list.insert(0,param_newAddress)
    otherCommon.is_twolist_equal(old_deliveryAddress_list,new_deliveryAddress_list)


def cheshi_update_NTN_DeliveryAddress(merchant):


    NoneDefault_DeliveryAddress=get_NoneDefault_DeliveryAddress(merchant)

    NoneDefault_DeliveryAddress=produce_randinfo(NoneDefault_DeliveryAddress)

    cheshi_update_deliveryAddress(merchant,updated_DeliveryAddress=NoneDefault_DeliveryAddress)

def cheshi_update_NTD_DeliveryAddress(merchant):



    NoneDefault_DeliveryAddress=get_NoneDefault_DeliveryAddress(merchant)

    NoneDefault_DeliveryAddress=produce_randinfo(NoneDefault_DeliveryAddress)

    NoneDefault_DeliveryAddress.isdefault=1

    cheshi_update_deliveryAddress(merchant,updated_DeliveryAddress=NoneDefault_DeliveryAddress)

def cheshi_update_DTD_DeliveryAddress(merchant):

    Default_DeliveryAddress=get_Default_DeliveryAddress(merchant)
    Default_DeliveryAddress=produce_randinfo(Default_DeliveryAddress)
    cheshi_update_deliveryAddress(merchant,updated_DeliveryAddress=Default_DeliveryAddress)

def cheshi_update_DTN_DeliveryAddress(merchant):

    Default_DeliveryAddress=get_Default_DeliveryAddress(merchant)
    Default_DeliveryAddress=produce_randinfo(Default_DeliveryAddress)
    Default_DeliveryAddress.isdefault=0
    cheshi_update_deliveryAddress(merchant,updated_DeliveryAddress=Default_DeliveryAddress)

def cheshi_update_deliveryAddress(merchant,updated_DeliveryAddress):
    update_DeliveryAddress_url="""
    %s?a=updateaddress&data={"key":"%s",%s}
    """%(class_def.base_deliveryaddress_url,merchant.Key,json.dumps(updated_DeliveryAddress.__dict__).strip('{}'))

    assert_url_action_success(update_DeliveryAddress_url)
    create_deliveryAddress_list=cheshi_getalldeliveryAddress(merchant)

    if updated_DeliveryAddress.isdefault ==1:
        count_default=0
        count_default=len(filter(lambda x:x.isdefault==1,create_deliveryAddress_list))
        assert count_default==1,"更新导致默认地址数不对"


    #matched_DeliveryAddress=[for_deliveryAddress for  for_deliveryAddress in create_deliveryAddress_list if for_deliveryAddress.id==updated_DeliveryAddress.id][0]
    matched_DeliveryAddress=get_firstElement_ByProp(create_deliveryAddress_list,id=updated_DeliveryAddress.id)
    assert matched_DeliveryAddress==updated_DeliveryAddress,"更新失败了"


def cheshi_del_DeliveryAddress(merchant,*del_DeliveryAddress_list):

    DeliveryAddressList_beforeDel=cheshi_getalldeliveryAddress(merchant)

    del_ids=list(set([ for_DeliveryAddress.id for  for_DeliveryAddress in del_DeliveryAddress_list]))
    url_del="""
    %s?a=deladdress&data={"key":"%s","ids":%s}
    """%(class_def.base_deliveryaddress_url,merchant.Key,str(del_ids))

    assert_url_action_success(url_del)

    DeliveryAddressList_AfterDel=cheshi_getalldeliveryAddress(merchant)

    assert len(DeliveryAddressList_AfterDel)+len(del_ids)==len(DeliveryAddressList_beforeDel),"删除送餐地址的数目不对"

    if any(afterdel_DeliveryAddress.id in del_ids  for afterdel_DeliveryAddress in DeliveryAddressList_AfterDel ):
        raise ValueError,"要被删除的送餐地址有些没有被删除"
    remain_DeliveryAddress=cheshi_getalldeliveryAddress(merchant)
    if remain_DeliveryAddress is not None and len(remain_DeliveryAddress)>0:
        assert exists_defaultDeliveryAddress(merchant)==True,"删除默认送餐地址导致没有默认送餐地址了"







def cheshi_del_ND_DeliveryAddress(merchant):

    NoneDefault_DeliveryAddress=get_NoneDefault_DeliveryAddress(merchant)

    cheshi_del_DeliveryAddress(merchant,NoneDefault_DeliveryAddress)

def cheshi_del_D_DeliveryAddress(merchant):
    Default_DeliveryAddress=get_Default_DeliveryAddress(merchant)

    cheshi_del_DeliveryAddress(merchant,Default_DeliveryAddress)

def cheshi_del_listWithD_DeliveryAddress(merchant):
    NoneDefault_DeliveryAddress=get_NoneDefault_DeliveryAddress(merchant)
    Default_DeliveryAddress=get_Default_DeliveryAddress(merchant)

    cheshi_del_DeliveryAddress(merchant,NoneDefault_DeliveryAddress,Default_DeliveryAddress)

def cheshi_clear_DeliveryAddress(merchant):

    cheshi_del_DeliveryAddress(merchant,*cheshi_getalldeliveryAddress(merchant))




def produce_base_newDeliveryAddress(user):

    new_deAddress_dict=dict(uid=user.Uid,
                            address=u"天天向上酒吧",
                            contacttel=u"13242868033",
                            contactman=u"陈清和")
    return DeliveryAddress(**new_deAddress_dict)


def produce_randinfo(new_base_deAddress):
    global  address_set,contactman_set
    new_base_deAddress.address=otherCommon.randchoice(address_set-set(new_base_deAddress.address))
    new_base_deAddress.contactman=otherCommon.randchoice(contactman_set-set(new_base_deAddress.contactman))
    new_base_deAddress.contacttel=otherCommon.randchoice(contactman_set-set(new_base_deAddress.contacttel))
    return new_base_deAddress


def produce_newDeliveryAddress(user):

    new_base_DeliveryAddress=produce_base_newDeliveryAddress(user)
    return produce_randinfo(new_base_DeliveryAddress)



def produce_SomeDeliveryAddress_Data(user):

    for add_index in xrange(6):
        tmp_DeliveryAddress=produce_newDeliveryAddress(user)
        cheshi_add_deliveryAddress(user,tmp_DeliveryAddress)


    cheshi_update_NTD_DeliveryAddress(user)
    cheshi_update_DTD_DeliveryAddress(user)
    cheshi_update_NTD_DeliveryAddress(user)
    cheshi_update_NTN_DeliveryAddress(user)




    cheshi_del_ND_DeliveryAddress(user)
    cheshi_del_D_DeliveryAddress(user)
    cheshi_del_listWithD_DeliveryAddress(user)
    cheshi_clear_DeliveryAddress(user)








if __name__=="__main__":
    time_start=datetime.datetime.now()
    active_user=cheshi_loginwiYW_byUrl_Success()
    
    deliveryAddress_list=cheshi_getalldeliveryAddress(active_user)

    produce_SomeDeliveryAddress_Data(active_user)


    deliveryAddress_list=cheshi_getalldeliveryAddress(active_user)


    time_end=datetime.datetime.now()
    print time_end-time_start,"秒"

    print "Over"
