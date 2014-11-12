#coding=utf-8


from ComHelper import PathHelper
from ComHelper.DataHelper import get_uid_by_session
from ComHelper.MerchantDataHelper import merchant_available_slice

__author__ = 'Administrator'

from ComHelper.dbHelper import  get_cursor, getsingle, get_conn
#from  ComHelper.otherCommon import   get_db_return_obj
from ComHelper.ConvertHelper import   get_db_return_obj, get_db_return_list
from CardService.Model.GetCardDetail  import CardDetail

def card_available_slice(param_table_name):
    table_name="TB_Card" if not param_table_name else param_table_name
    return  " {0}.deleteflag=0  and {0}.active=1 and {0}.disable=0".format(table_name)
CardDetail_Path="CardService.Model.GetCardDetail.CardDetail"
static_avaiable_card=None #有效名片
static_temp_card=None #临时名片
static_expiry_card=None #过期名片
static_get_hascollect_count_card=None #获取带有收藏数大于0的名片
static_merchant_deleted_card=None #获取名片，该名片的商户被标记删除

static_sql_base="""
 select
      b.cid as Id,
      b.cname as Name,
      b.mobile1 as Phone1,
      b.mobile2 as Phone2,
      b.tel as Telephone,
      case
      when c.level is null then b.fax
      when  c.deleteflag=1 then b.fax
      else c.fax
      end    as Fax,
     case
     when c.level is null then b.comname
      when b.deleteflag=1 then b.comname
      else c.mname
     end    as Company,
      c.address as Address,
      c.mainproduct as Scope,
      b.email as Email,
      b.post as Job,
      b.shareagain as Shareagain,
      b.mid as Mid,
      b.uid as Uid,
      b.ctype as Category,
      b.mobile3 as Phone3,
      b.active as Active,
      b.deleteflag as Deleteflag,
      case
      when IFNULL(c.level,0)=0  then  0
      when length(IFNULL(c.pwd,''))=0 then 1
      else 2
      end  as Mlevel,
      b.isdefault as Isdefault,
      b.disable as Disable,
      b.expirydate as Expirydate
      from TB_Card as b
      left outer join TB_Merchant as c on b.mid=c.id
"""

def get_has_collectCount_Card():
    global  static_get_hascollect_count_card
    if not static_get_hascollect_count_card:
        has_collectcount_card_sql="""
        select
      b.cid as Id,
      b.cname as Name,
      b.mobile1 as Phone1,
      b.mobile2 as Phone2,
      b.tel as Telephone,
      case
      when c.level is null then b.fax
      when  c.deleteflag=1 then b.fax
      else c.fax
      end    as Fax,
     case
     when c.level is null then b.comname
      when b.deleteflag=1 then b.comname
      else c.mname
     end    as Company,
      c.address as Address,
      c.mainproduct as Scope,
      b.email as Email,
      b.post as Job,
      b.shareagain as Shareagain,
      b.mid as Mid,
      b.uid as Uid,
      b.ctype as Category,
      b.mobile3 as Phone3,
      b.active as Active,
      b.deleteflag as Deleteflag,
      case
      when IFNULL(c.level,0)=0  then  0
      when length(IFNULL(c.pwd,''))=0 then 1
      else 2
      end  as Mlevel,
      b.isdefault as Isdefault,
      b.disable as Disable,
      b.expirydate as Expirydate
      from TB_Card as b
      left outer join TB_Merchant as c on b.mid=c.id
      where  (b.deleteflag=0  or (b.disable=1 and b.deleteflag=1)) and b.active=1 and b.expirydate<now()
      and exists( select 1 from TB_User c where c.uid=b.uid  and c.disable=0)
      and exists(select 1 from TB_Relation r1 where r.rid=b.cid and r.rtype=3)
      LIMIT 1
    """
        static_get_hascollect_count_card=get_db_return_obj(PathHelper.Get_CardDetail_Path(),has_collectcount_card_sql)
    return static_get_hascollect_count_card

def get_expiry_card():
    global  static_expiry_card
    if 0 :
        return static_expiry_card
    get_expiry_car_sql="""
    select
      b.cid as Id,
      b.cname as Name,
      b.mobile1 as Phone1,
      b.mobile2 as Phone2,
      b.tel as Telephone,
      case
      when c.level is null then b.fax
      when  c.deleteflag=1 then b.fax
      else c.fax
      end    as Fax,
     case
     when c.level is null then b.comname
      when b.deleteflag=1 then b.comname
      else c.mname
     end    as Company,
      c.address as Address,
      c.mainproduct as Scope,
      b.email as Email,
      b.post as Job,
      b.shareagain as Shareagain,
      b.mid as Mid,
      b.uid as Uid,
      b.ctype as Category,
      b.mobile3 as Phone3,
      b.active as Active,
      b.deleteflag as Deleteflag,
      case
      when IFNULL(c.level,0)=0  then  0
      when length(IFNULL(c.pwd,''))=0 then 1
      else 2
      end  as Mlevel,
      b.isdefault as Isdefault,
      b.disable as Disable,
      b.expirydate as Expirydate
      from TB_Card as b
      left outer join TB_Merchant as c on b.mid=c.id
      where  (b.deleteflag=0  or (b.disable=1 and b.deleteflag=1)) and b.active=1 and b.expirydate<now()
      and exists( select 1 from TB_User c where c.uid=b.uid  and c.disable=0)
      LIMIT 1
    """
    static_expiry_card=None
    static_expiry_card=get_card_obj(get_expiry_car_sql)
    if not static_expiry_card:#数据库里找不到过期名片
        create_expiry_card()
        static_expiry_card=get_card_obj(get_expiry_car_sql)
    return static_expiry_card

def create_expiry_card(id=0):
    "更改一张名片使之为过期名片"
    if not id:
        get_will_expiry_card_sql="""
    select cid from
    TB_Card c  where mid=0 and isdefault=0 and {card_available}
    LIMIT 1
    """.format(card_available=card_available_slice('c'))
        will_expiry_id=getsingle(get_will_expiry_card_sql)
        if not will_expiry_id:#如果不存在MID为0的名片，则取一张临时名片
            get_will_expiry_card_sql="""
            select cid
            from TB_Card c where expirydate<'2100-01-01' and isdefault=0 and {card_available}
            LIMIT 1
            """.format(card_available=card_available_slice('c'))
            will_expiry_id=getsingle(get_will_expiry_card_sql)
            assert will_expiry_id!=None and will_expiry_id!=0,"找不到一张可以用来过期的名片"
    else:
        will_expiry_id=id


    update_to_expiry_sql="""
    update TB_Card
    set disable=1 , expirydate=date_sub(now(),interval 1 second)
    where
    cid = {0}
    """.format(will_expiry_id)
    get_cursor().execute(update_to_expiry_sql)
    get_conn().commit()




def get_available_card():
    "获取有效名片"
    global  static_avaiable_card
    if static_avaiable_card:
        return static_avaiable_card
    get_available_card_sql="""
      select
      b.cid as Id,
      b.cname as Name,
      b.mobile1 as Phone1,
      b.mobile2 as Phone2,
      b.tel as Telephone,
      case
      when c.level is null then b.fax
      when  c.deleteflag=1 then b.fax
      else c.fax
      end    as Fax,
     case
     when c.level is null then b.comname
      when b.deleteflag=1 then b.comname
      else c.mname
     end    as Company,
      c.address as Address,
      c.mainproduct as Scope,
      b.email as Email,
      b.post as Job,
      b.shareagain as Shareagain,
      b.mid as Mid,
      b.uid as Uid,
      b.ctype as Category,
      b.mobile3 as Phone3,
      b.active as Active,
      b.deleteflag as Deleteflag,
      case
      when IFNULL(c.level,0)=0  then  0
      when length(IFNULL(c.pwd,''))=0 then 1
      else 2
      end  as Mlevel,
      b.isdefault as Isdefault,
      b.disable as Disable,
      b.expirydate as Expirydate
      from TB_Card as b
      left outer join TB_Merchant as c on b.mid=c.id
      where  (b.deleteflag=0  or (b.disable=1 and b.deleteflag=1)) and b.active=1
      and exists( select 1 from TB_User c where c.uid=b.uid  and c.disable=0)
      LIMIT 1
    """
    static_avaiable_card=get_db_return_obj(CardDetail_Path,get_available_card_sql)
    return static_avaiable_card


def get_temp_card():
    "获取临时名片"
    global  static_temp_card
    if static_temp_card:
        return static_temp_card
    get_temp_card_sql="""
      select
      b.cid as Id,
      b.cname as Name,
      b.mobile1 as Phone1,
      b.mobile2 as Phone2,
      b.tel as Telephone,
      case
      when c.level is null then b.fax
      when  c.deleteflag=1 then b.fax
      else c.fax
      end    as Fax,
     case
     when c.level is null then b.comname
      when b.deleteflag=1 then b.comname
      else c.mname
     end    as Company,
      c.address as Address,
      c.mainproduct as Scope,
      b.email as Email,
      b.post as Job,
      b.shareagain as Shareagain,
      b.mid as Mid,
      b.uid as Uid,
      b.ctype as Category,
      b.mobile3 as Phone3,
      b.active as Active,
      b.deleteflag as Deleteflag,
      case
      when IFNULL(c.level,0)=0  then  0
      when length(IFNULL(c.pwd,''))=0 then 1
      else 2
      end  as Mlevel,
      b.isdefault as Isdefault,
      b.disable as Disable,
      b.expirydate as Expirydate
      from TB_Card as b
      left outer join TB_Merchant as c on b.mid=c.id
      where  b.deleteflag=0   and b.active=1 and
      not exists(
      select 1 from TB_Merchant as m1 where m1.id=b.mid
      )
      and exists( select 1 from TB_User c where c.uid=b.uid  and c.disable=0)
      LIMIT 1
    """
    static_temp_card=get_db_return_obj(CardDetail_Path,get_temp_card_sql)
    return static_temp_card
def  get_card_by_mobile_with_condition(mobile,**kwargs):
    get_card_by_mobile_sql="""
      select
      b.cid as Id,
      b.cname as Name,
      b.mobile1 as Phone1,
      b.mobile2 as Phone2,
      b.tel as Telephone,
      case
      when c.level is null then b.fax
      when  c.deleteflag=1 then b.fax
      else c.fax
      end    as Fax,
     case
     when c.level is null then b.comname
      when b.deleteflag=1 then b.comname
      else c.mname
     end    as Company,
      c.address as Address,
      c.mainproduct as Scope,
      b.email as Email,
      b.post as Job,
      b.shareagain as Shareagain,
      b.mid as Mid,
      b.uid as Uid,
      b.ctype as Category,
      b.mobile3 as Phone3,
      b.active as Active,
      b.deleteflag as Deleteflag,
      case
      when IFNULL(c.level,0)=0  then  0
      when length(IFNULL(c.pwd,''))=0 then 1
      else 2
      end  as Mlevel,
      b.isdefault as Isdefault,
      b.disable as Disable,
      b.expirydate as Expirydate
      from TB_Card as b
      left outer join TB_Merchant as c on b.mid=c.id
      where  b.deleteflag=0   and b.active=1 and  b.mobile1='{0}'
    """.format(mobile)
    card_list=get_db_return_list(CardDetail_Path,get_card_by_mobile_sql)
    card_list=filter(lambda x:record_meet_dict(x,kwargs)==True,card_list)
    return card_list


def get_card_merchant_deleted():
    global  static_merchant_deleted_card
    if not static_merchant_deleted_card:
        sql_merchant_delted_card="""
        {sql_base}
       where  {card_available}
        and  not ( {merchant_available})
        """.format(sql_base=static_sql_base,
                   card_available=card_available_slice('b'),
                   merchant_available=merchant_available_slice('c'))
        static_merchant_deleted_card=get_card_obj(sql_merchant_delted_card)
    return static_merchant_deleted_card



def get_card_CanReply(parm_session_id=0):
    user_id=get_uid_by_session(parm_session_id)
    assert user_id is not None and user_id>0,"用户ID为空"
    sql_card_canReply="""
    {sql_base}
    left join TB_User u  on u.uid =b.uid
    and (
    exists (
    select 1 from TB_RelationInfo r1,TB_Card c1 where r1.rid=c1.cid and r1.rtype=3 and r1.uid=u.uid and c1.uid={user_id} and ({c1_available})
    and not exists (
    select 1 from TB_RelationInfo r2,TB_Card c2 where r2.rid=c2.cid and r2.rtype=3 and r2.uid={user_id} and c2.uid=u.uid and ({c2_available})
    )
    )
    or exists(
    select 1 from TB_Relation r3,TB_Card c3 where r3.rid=c3.cid and r3.rtype=3 and r3.uid={user_id} and c3.uid=u.uid and ({c3_available})
    and not exists(
    select 1 from TB_RelationInfo r4,TB_Card c4 where r4.rid=c4.cid and r4.rtype=3 and r4.uid=u.uid and c4.uid={user_id} and ({c4_available})
    )
    )
    )
    """.format(sql_base=static_sql_base,user_id=user_id
    ,c1_available=card_available_slice('c1'),
    c2_available=card_available_slice('c2'),
    c3_available=card_available_slice('c3'),
    c4_available=card_available_slice('c4'))
    return get_card_obj(sql_card_canReply)





def get_card_obj(param_get_sql_url):
    return get_db_return_obj(PathHelper.Get_CardDetail_Path(),param_get_sql_url)


def record_meet_dict(record,dict):
    local_is_meet=True
    for compare_key,compare_value in dict.iteritems():
        source_value=record.get(compare_key,None)
        if not  source_value or source_value!=compare_value:
            local_is_meet=False
            break
    return local_is_meet

    pass
if __name__=="__main__":
    #assert get_available_card().isavailable_return()==True
    assert get_temp_card().isavailable_return()==True,"临时名片有问题"
    assert get_expiry_card().isavailable_return()==False,"过期名片不报错"
    get_card_by_mobile_with_condition('13900139151')
    get_card_merchant_deleted()
    create_expiry_card()





