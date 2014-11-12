#coding=utf-8
import datetime
import functools
from ComHelper.ConvertHelper import Validate_UrlReturnObj, get_url_return_obj, get_url_return_dict
from ComHelper import PathHelper
import inspect
import json
from CardService.Model.GetCardDetail import  CardDetail
from ComHelper.otherCommon import wraper_cheshi_get
from  setreader import get_static_setting_reader
from ComHelper.CardDataHelper import  get_available_card, get_expiry_card, get_card_merchant_deleted, get_card_CanReply
from ComHelper.DataHelper import   get_active_session_list, get_sessionid_by_cardid


CardDetail_Path='CardService.Model.GetCardDetail.CardDetail'

def get_CardDetail(id,key="0"):
    url_str="""
    YellowPageMap/Cardmanage.ashx?a=nokeygetcard&data={{"key":"{0}","cardid":{1} }}
    """.format(
               key,id)
    return get_url_return_obj(PathHelper.Get_CardDetail_Path(),url_str)


@wraper_cheshi_get
def cheshi_GetCardDetailById_IsAvailableCard(param_id=0):
    id=get_available_card() if not param_id else param_id
    url_return_obj=get_CardDetail(id)
    return url_return_obj


@wraper_cheshi_get
def cheshi_CardDetail_card_IsMerchantDeletedAndAvailable():
    card_merchatn_deleted=get_CardDetail(get_card_merchant_deleted().Id)
    return card_merchatn_deleted


@wraper_cheshi_get
def cheshi_get_CardDetail_ById_IsExpiryCard(param_id=0):
    id= get_expiry_card().Id if param_id==0 else param_id #又复制了。。有什么办法不复制的？
    return get_CardDetail(id)

@wraper_cheshi_get
def cheshi_get_CardDetail_IsCanReplyCard(param_id=0):
    active_session=get_active_session_list()[0]
    canreply_cardid=get_card_CanReply().Id if not param_id else param_id
    return get_CardDetail(canreply_cardid)


if __name__=="__main__":
    #cheshi_GetCardDetailById_ByUrl(2493)
    #cheshi_get_ExpiryCardDetail_ById_ByUrl()
    #cheshi_CardDetail_card_merchant_deleted()
    #get_CardDetail(608,u'0')
    #cheshi_CardUpdate_expiry_to_noexpiry_byComname()
    #cheshi_GetCardDetailById_IsAvailableCard()
    #cheshi_GetCardDetailById_IsAvailableCard()
    cheshi_get_CardDetail_IsCanReplyCard()
    print "测试完成"

