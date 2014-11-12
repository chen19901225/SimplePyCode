#coding:utf-8
import json
import datetime
from CardService.Model.GetCardDetail import CardDetail
from CardService.UrlHelper.CardDetailHelper import *
from ComHelper.CardDataHelper import get_expiry_card
from ComHelper.ConvertHelper import get_url_return_dict
from ComHelper.DataHelper import get_sessionid_by_cardid
from ComHelper.MerchantDataHelper import get_merchant_IsAvailableMerchant, get_merchant_IsInavailableMerchant
from ComHelper.otherCommon import is_keys_equal, product_random_str

__author__ = 'Administrator'
def card_update(clone_card,parm_key=None):
    print clone_card.__dict__
    key=parm_key
    if not parm_key:
        key=get_sessionid_by_cardid(clone_card.Id)

    update_card_url="""
    YellowPageMap/Cardmanage.ashx?a=update&data={{"key":"{Key}","cardInfo":{Cardinfo} }}
    """.format(Key=key,Cardinfo=json.dumps(clone_card.get_update_dict()))
    url_dict=get_url_return_dict(update_card_url)
    return url_dict["Status"]
def Is_Update_HasCommit(local_card,url_return_card):
    for key,value in  local_card.__dict__.iteritems():
        if key in ("Disable","Expirydate"):
            continue
        if value !=url_return_card.__dict__[key]:
            print key +"Not matched"
            return False
    return True
def produce_update(clone_card):

    for key in ("Email","Job","Phone1","Phone2"):
        setattr(clone_card,key,product_random_str(getattr(clone_card,key,None)))





def cheshi_CardUpdate_expiry_to_noexpiry_byComname():
    "把过期名片更新为非过期名片(通过商户名称)"
    temp_card=get_expiry_card()
    clone_card=cheshi_get_CardDetail_ById_IsExpiryCard(temp_card.Id)
    #clone_card=CardDetail(**temp_card.__dict__)


    produce_update(clone_card)
    clone_card.Company=datetime.datetime.now().strftime('%m-%d %H:%M')+'chen'
    update_re=card_update(clone_card,get_sessionid_by_cardid(temp_card))

    assert update_re==0,"名片更新不成功"

    #测试更新后的名片，是否为非过期的
    url_ret_obj=cheshi_GetCardDetailById_IsAvailableCard(clone_card.Id)
    assert Is_Update_HasCommit(clone_card,url_ret_obj)==True,"名片更新不成功"

def cheshi_CardUpdate_expiry_noexpiry_byInavailableMid():
    #使过期名片变成非过期名片，通过更新到非有效商户
    merchant_id=0
    temp_card=get_expiry_card()
    cheshi_get_CardDetail_ById_IsExpiryCard(temp_card.Id)

    clone_card=CardDetail(**temp_card.__dict__)
    while True:
        merchant=get_merchant_IsInavailableMerchant(merchant_id)
        merchant_id=merchant.Id
        clone_card.Mid=merchant_id
        update_result=card_update(clone_card)
        if update_result!=0:
            print update_result
        else:
            break

    url_get_card=cheshi_GetCardDetailById_IsAvailableCard(clone_card)
    #assert is_keys_equal(("Scope","Address"),url_get_card,merchant)==True,"更新不起作用"
    #assert url_get_card.Company==merchant.Mname

def cheshi_CardUpdate_expiry_noexpiry_byAvailableMid():
    merchant_id=0
    temp_card=get_expiry_card()
    cheshi_get_CardDetail_ById_IsExpiryCard(temp_card)

    clone_card=CardDetail(**temp_card.__dict__)
    while True:
        merchant=get_merchant_IsInavailableMerchant(merchant_id)
        merchant_id=merchant.Id
        clone_card.Mid=merchant_id
        update_result=card_update(clone_card)
        if update_result!=0:
            print update_result
        else:
            break

    url_get_card=cheshi_GetCardDetailById_IsAvailableCard(clone_card)
    assert is_keys_equal(("Scope","Address"),url_get_card,merchant)==True,"更新不起作用"
    assert url_get_card.Company==merchant.Mname

def cheshi_CardUpdate_UpdateNoneTempInfo():
    available_card=get_available_card()
    cheshi_GetCardDetailById_IsAvailableCard(available_card.Id)

    clone_card=CardDetail(**available_card.__dict__)
    produce_update(clone_card)









if __name__=="__main__":
    cheshi_CardUpdate_expiry_to_noexpiry_byComname()
    cheshi_CardUpdate_expiry_noexpiry_byInavailableMid()
    cheshi_CardUpdate_expiry_noexpiry_byAvailableMid()
    cheshi_CardUpdate_UpdateNoneTempInfo()
    print "OK"




