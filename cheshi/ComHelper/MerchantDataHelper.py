#coding=utf-8
from ComHelper import otherCommon
import ComHelper
from ComHelper.ConvertHelper import get_db_return_obj, executeNoQuery_sql
from ComHelper.PathHelper import Get_Merchant_Path
from ComHelper.dbHelper import getsingle
from ComHelper.otherCommon import wraper_cheshi_get

__author__ = 'Administrator'
import datetime
class TB_Merchant(object):
    def __init__(self,**kwargs):
        Id=0
        Uid=0
        Typecode=0
        Mname=""
        Mobile=""
        Address=""
        MainProduct=""
        Contacttel=""
        Tag=""
        Url=""
        Publisher=0
        Pubtime=datetime.datetime.now()
        Distid=0
        Lng=0.0
        Lat=0.0
        Geohash=""
        Status=0
        Createtime=datetime.datetime.now()
        Gclng=0.0
        Gclat=0.0
        X=0.0
        Y=0.0
        Geohashxy=""
        Endtime=datetime.datetime.now()
        Pwd=""
        Deleteflag=0
        Level=0
        Fax=""
        Logopicid=0
        Logopath=""
        self.__dict__.update(kwargs)
        if isinstance(self.Pubtime,basestring):
            self.Pubtime=otherCommon.convert_datetime(self.Pubtime)
        if isinstance(self.Createtime,basestring):
            self.Createtime=otherCommon.convert_datetime(self.Createtime)
        if isinstance(self.Endtime,basestring):
            self.Endtime=otherCommon.convert_datetime(self.Endtime)
    def isavailable_return(self):
        success_db_return=True
        if  self.Level==0 or self.Endtime<datetime.datetime.now() or self.Deleteflag==1:
            success_db_return=False
        return success_db_return
    def IsAvailableMerchant(self):
        return self.isavailable_return()
    def IsInavailableMerchant(self):
        return not self.IsAvailableMerchant()



sql_merchant_base="""
select  id as Id,
      uid as Uid,
      typecode as Typecode,
      mname as Mname,
      mobile as Mobile,
      address as Address,
      mainproduct as MainProduct,
      contacttel as Contacttel,
      tag as Tag,
      url as Url,
      publisher as Publisher,
      pubtime as Pubtime,
      distid as Distid,
      lng as Lng,
      lat as Lat,
      geohash as Geohash,
      status as Status,
      createtime as Createtime,
      gclng as Gclng,
      gclat as Gclat,
      x as X,
      y as Y,
      geohashxy as Geohashxy,
      endtime as Endtime,
      pwd as Pwd,
      deleteflag as Deleteflag,
      level as Level,
      fax as Fax,
      logopicid as Logopicid,
      logopath as Logopath
      from TB_Merchant  m
"""
static_merchant_available=None
static_merchant_inavailable=None

def  merchant_available_slice(para_table_name=None):
    loc_table_name= 'TB_Merchant' if not  para_table_name else para_table_name
    return "{0}.deleteflag=0 and {0}.level!=0 and {0}.endtime>now() ".format(loc_table_name)

def get_merchant_bySql(param_sql):
    return get_db_return_obj(Get_Merchant_Path(),param_sql)


@wraper_cheshi_get
def get_merchant_IsAvailableMerchant(start_mid=0):
    global  static_merchant_available
    if not 0:
        sql_get_merchant_available="""
        {sql_base}
        where {merchant_available}
        and id>{start_mid}
        LIMIT 1
        """.format(sql_base=sql_merchant_base,
                   merchant_available=merchant_available_slice('m'),
                   start_mid=start_mid)
        static_merchant_available=get_merchant_bySql(sql_get_merchant_available)
        #assert static_merchant_available.isavailable_return()==True,"有效商户的结果不有效"
    return static_merchant_available


@wraper_cheshi_get
def get_merchant_IsInavailableMerchant(start_mid):
    global  static_merchant_inavailable
    if not 0:
        sql_get_merchant_inavailable="""
        {sql_base}
        where not({merchant_available})
        and id>{start_mid}
        LIMIT 1
        """.format(sql_base=sql_merchant_base,
                   merchant_available=merchant_available_slice('m')
        ,start_mid=start_mid)

        static_merchant_inavailable=get_merchant_bySql(sql_get_merchant_inavailable)
        #assert static_merchant_inavailable.isavailable_return()==False,"失效商户 的结果测试结果为有效"
    return static_merchant_inavailable



def get_merchant_byId(merchant_id):
    get_merchant_by_id_sql="""
    {sql_base}
    where id={merchant_id}
    """.format(sql_base=sql_merchant_base,
               merchant_id=merchant_id)
    match_id_merchant=get_merchant_bySql(get_merchant_by_id_sql)
    return match_id_merchant

def get_merchant_by_userid_withoutCheck(uid):
    get_merchant_by_userid_sql="""
    {sql_base}
    where uid={uid}
    """.format(sql_base=sql_merchant_base,uid=uid)

    match_id_merchant=get_merchant_bySql(get_merchant_by_userid_sql)


def get_userid_by_merchant_id(merchantid,ischeck):
    get_userid_sql="""
    select uid
    from TB_Merchant
    where id={merchantid}
    """.format(merchantid=merchantid)

    matched_userid=getsingle(get_userid_sql)

    return matched_userid


def get_merchant_by_userid(uid,ischeck):
    get_merchant_by_userid_sql="""
    {sql_base}
    where uid={uid}
    """.format(sql_base=sql_merchant_base,uid=uid)

    match_id_merchant=get_merchant_bySql(get_merchant_by_userid_sql)

    if ischeck:
        match_id_merchant=get_merchant_after_check(match_id_merchant)


def get_merchant_after_check(parm_merchant):
    "获取合法的商户"
    local_merchant=parm_merchant
    if not local_merchant:
        return local_merchant
    if local_merchant.Deleteflag==1:
        return None
    if local_merchant.Endtime<datetime.datetime.now():
        return None
    return local_merchant


def update_merchant(merchant,**kwargs):
    assert len(kwargs)==1,"暂时只允许更新商户的一个字段"

    assert merchant is not None,"更新的商户不能为空"

    update_merchant_slice_sql=" {table_alias}.{name}={value} ".format(table_alias='TB_Merchant',name=kwargs.keys()[0],value=kwargs.values()[0])

    update_merchant_sql="""
    update TB_Merchant
    set {update_slice}
    where id={merchantid}
    """.format(merchantid=merchant.Id,update_slice=update_merchant_slice_sql)

    executeNoQuery_sql(update_merchant_sql)


def update_merchant_toYWMerchant(merchant):
    update_merchant_toYWMerchant(merchant,typecode=10101)







if __name__=="__main__":
    get_merchant_IsAvailableMerchant()
    get_merchant_IsInavailableMerchant()


