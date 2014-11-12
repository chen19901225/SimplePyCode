#coding=utf-8
import string
from ComHelper.MerchantDataHelper import get_merchant_byId
from ComHelper.otherCommon import convert_datetime, get_child_dict, getbitvalue, is_keys_equal
import time,urllib,json,datetime
from   ComHelper import dbHelper
from setreader import  get_static_setting_reader
from ComHelper.DataHelper import   get_active_session_list


class  CardDetail(object):
    def __init__(self,**kwargs):
        self.Id=0
        self.Name=""
        self.Phone1,self.Phone2,self.Phone3="","",""
        self.Telephone=""
        self.Fax=""
        self.Company=""
        self.Address=""
        self.Scope=""
        self.Email=""
        self.Job=""
        self.Shareagain=0
        self.Mid=0
        self.Uid=0
        self.Active=0
        self.Deleteflag=0
        self.Mlevel=0
        self.Isdefault=0
        self.Disable=0
        self.CollectCount=0
        self.Expirydate=datetime.datetime.now()
        self.Canreply=0
        self.__dict__.update(kwargs)
        if isinstance(self.Expirydate,unicode):
            self.Expirydate=self.Expirydate.strip()
            self.Expirydate=convert_datetime(self.Expirydate)

        for name in ["Shareagain","Disable","Isdefault","Active","Deleteflag"]:
            self.__setattr__(name,getbitvalue(self.__getattribute__(name)))
    def get_update_dict(self):
        key_tuple=["Id","Name","Phone1","Phone2","Phone3","Telephone","Fax","Company","Address","Scope","Email","Job","UId","Shareagain","Mid"]
        update_dict=get_child_dict(self.__dict__,key_tuple)
        return update_dict


    def isavailable_return(self):
        sucess_return=True
        sucess_return=sucess_return and  self.record_success()
        return sucess_return

    def record_success(self):
        if self.Id==0:
           return  False
        if self.Uid==0:
            return False
        if self.Deleteflag==1:
            return False
        if self.Isdefault==1:
            if self.Active==0 or self.Disable==1  or self.Deleteflag==1:
                return False
        if not self.Phone1 and self.Phone2 and self.Phone3:
            return False
        if self.Mid!=0:
            merchant_info_tuple=("Scope","Address")
            connect_merchant=get_merchant_byId(self.Mid)
            if not connect_merchant or  connect_merchant.IsInavailableMerchant():#商户不存在或者商户失效
                success= self.is_merchant_about_info_clear()
                if not success:
                    return success
                success=card_matched_merchant(self,connect_merchant)
                return success

            else:#商户有效
                success= not self.is_merchant_about_info_clear()
                if not success:
                    return success
                return card_matched_merchant(self,connect_merchant)
        else:
            return self.IsMerchantInfo_Clear()
        return True


    def is_expired(self):
        return self.Expirydate<datetime.datetime.now() or  self.Disable==1

    def is_merchant_about_info_clear(self):
        return  not self.Scope and not self.Address
    def IsAvailableCard(self):#是有效名片
        return self.record_success()  and not self.is_expired()
    def IsCanReplyCard(self,has_base_validate=False):
        success=True
        if not  has_base_validate:
            success=self.IsAvailableCard()
        if not success:
            return success
        return self.Canreply==1






    def IsMerchantInfo_Clear(self):
        if self.Mlevel!=0:
            return False
        if self.Scope:
            return False
        if self.Address:
            return False
        return True

    def IsMerchantDeletedAndAvailable(self,base_validate=False): #名片关联的商户已经被删除
        validate_success=True
        if not base_validate:
            validate_success=self.IsAvailableCard()
        if not validate_success:
            return validate_success
        if self.Mid==0:
            return False
        return self.IsMerchantInfo_Clear()

    def IsExpiryCard(self):
        return self.record_success() and self.is_expired()







def GetCardDetailById_ByDb(carddetail_id):
    local_db_instance=dbHelper.get_dbhelper()
    getcard_detail_sql_str="""

    """
def card_matched_merchant(card,merchant):
    success=True
    string_empty= '' or None
    if card.Mid not in (merchant.Id , 0):
        return False
    if card.Mlevel not in (merchant.Level , 0):
        return False
    if card.Scope not in (merchant.MainProduct , '' , None):
        return False
    if card.Address not in (merchant.Address , '' , None):
        return False
    return success
if __name__=="__main__":
   pass



