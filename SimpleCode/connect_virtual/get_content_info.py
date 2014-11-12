#coding:utf-8
from collections import defaultdict
import datetime
import functools
import string
from pytz import timezone
import pytz
import xlwt


__author__ = 'Administrator'
import pymongo
import utils

out_ad_pay_type='cpc'
host='192.168.219.135'
port=27017
conn=None
default_db_name="advert_platform_zheshi"
app_status_dict=None
app_platform_dict=None
#must_include_advert_types=("full",)
name_key_pair_list=[(u"应用名称",'name'),
    (u"应用Key",'api_key'),
    (u"应用系统",'platform') ,
    (u'应用通过审核的时间','pass_date',lambda x:x.strftime('%Y-%m-%d') if x else "")]


time_SH=timezone("Asia/Shanghai")

open_print_control=True #是否允许Print输出
out_ad_pay_type=out_ad_pay_type.upper()#小写字母
type_name_value_pair=[(u"banner","banner"),(u"插屏",'popup'),(u"全屏",'full_screen'),(u'开屏','open_screen')]

propforType_nameValue_pair=[(u"日均点击量","number_click"),(u'级别',"code"),(u"对应价格","developer"),(u"浮动值",'variable',lambda x:x or 0)]

show_type_list=[pair[1] for pair in type_name_value_pair]

level_keys=('_id','show_type','code','developer','variable','date_creation','date_start')

level_detail_keys=level_keys+("number_click",)



needed_added_default_level_keys=[]

nonlocal=dict()



def try_print(param_content):
    print param_content

for type_name,type_value in type_name_value_pair:
    for prop_tuple in propforType_nameValue_pair:
        new_search_name=u"{type_name}{prop_name}".format(type_name=type_name,prop_name=prop_tuple[0])
        new_search_value='level_log[show_type="{type_value}"].{prop_value}'.format(prop_value=prop_tuple[1],type_value=type_value)
        if len(prop_tuple)==2:
            out_format=lambda x:x
        else:
            out_format=prop_tuple[2]
        name_key_pair_list.append((new_search_name,new_search_value,out_format))



name_key_pair_list.append((u"是否被删除","removed"))
name_key_pair_list.append((u"开始点击时间","start_click_time",lambda x :x.strftime("%Y-%m-%d") if x else ""))


def get_client():
    global  conn
    if conn:
        return conn
    conn=pymongo.MongoClient(host,port)
    assert conn is not None,"数据库连接失败"
    return conn

def get_Database(basename=default_db_name):
    _database=get_client()[basename]
    assert _database is not None,"数据库"+basename+"不存在"
    return _database


def get_collection_byname(collection_name):
    collection=get_Database()[collection_name]
    assert collection is not None,collection_name+"并不存在"
    return collection

def print_data(param_data):
    print param_data



def get_all_app_status():
    global  app_status_dict
    if app_status_dict:
        return app_status_dict
    collection_app_status=get_collection_byname(u'app_status')
    _query={u"removed":False}
    app_status_cursor=collection_app_status.find(_query)
    app_status_dict=dict()
    for app_status_item in app_status_cursor:
        app_status_dict[app_status_item[u'code']]=utils.try_get_childDict(app_status_item,u'name',u'_id',u'removed')

    return app_status_dict

def get_all_platform():
    global app_platform_dict
    if app_platform_dict:
        return app_platform_dict

    collection_platform=get_collection_byname(u'platform')
    _query={"removed":False}
    cursor_platform=collection_platform.find(_query)
    app_platform_dict=dict()
    for app_platform_item in cursor_platform:
        app_platform_dict[app_platform_item[u'code']]=utils.try_get_childDict(app_platform_item,u'code',u'_id',u'removed')
    return app_platform_dict


def get_platform_by_id(param_id):
    for platform_name,platform_item in get_all_platform().items():
        if platform_item['_id']==param_id:
            return platform_name
    raise ValueError,str(param_id)+"Not Exist!!"



def get_app_id_list(*platform_name_list):
    objid_list=[]
    for platform_name in platform_name_list:
        matched_dict=get_all_platform()[platform_name]
        if not matched_dict:
            raise platform_name+"Not Exist"
        objid_list.append(matched_dict.get('_id'))
    return objid_list


dict_advert_level=None

def all_advert_level():

    global  dict_advert_level
    if dict_advert_level:
        return dict_advert_level

    collection_default_levels=get_collection_byname('advert_level')

    cursor_default_levels=collection_default_levels.find()
    dict_advert_level=defaultdict(list)
    for row_level in cursor_default_levels:
        if not needed_added_default_level_keys:
            for key  in level_keys:
                if key not in row_level:
                    needed_added_default_level_keys.append(key)

        appended_dict=dict.fromkeys(needed_added_default_level_keys)
        row_level.update(appended_dict)
        payment_type_code=row_level['payment_type_code']
        dict_advert_level[payment_type_code].append(row_level)
    return dict_advert_level


def get_advert_level_by_name(payment_type_code):
    payment_type_code=string.lower(payment_type_code)
    matched_levels=all_advert_level().get(payment_type_code,None)
    assert matched_levels is not None,payment_type_code+u"的levels不存在"
    return matched_levels







def get_status_objid(*status_name_list):
    objid_list=[]
    for status_name in status_name_list:
             matched_dict=get_all_app_status()[status_name]
             if not matched_dict:
                 raise status_name+'Not Exist'
             objid_list.append( matched_dict.get('_id'))
    return objid_list



def get_advert_level(*level_id_list):
    collection_advert_level=get_collection_byname('advert_level_log')
    _query={"_id":{"$in":list(level_id_list)}}

    cursor_advert_level=collection_advert_level.find(_query)
    list_advert_level=[]
    #return cursor_advert_level.collection

    #cheshi_level_log=DocumentConvetor(documents={"items":list(cursor_advert_level)},level=3).to_dict()["items"]

    newest_date=None
    for item_advert_level in cursor_advert_level:
        new_dict=utils.try_get_childDict(item_advert_level,*level_keys)
        new_dict['number_click']=0
        new_dict_date=new_dict['date_creation'] or new_dict['date_start']
        if newest_date is None:
            newest_date=new_dict_date
        else:
            newest_date=max(newest_date,new_dict_date)
        if new_dict['code'] is not None:
            #new_dict['code']=new_dict['code'].split('-')[0]
            if not new_dict['code'].startswith(out_ad_pay_type):
                try_print(u' '*4+u"应用分级_id:"+str(new_dict['_id'])+u"被舍弃,因为 code: "+new_dict['code']+u"!=要输出的分级"+out_ad_pay_type)
                continue
        list_advert_level.append(new_dict)

    nonlocal['pass_date']=newest_date
    return list_advert_level











def get_report_app_log_detail(app_id,date_period):
    """
    求出_id为app_id的APP，在date_period这段时间内，的详细点击情况。
    app_id:APP表里的主键ID,
    date_period:{""}
    """
    collection_report_app_log_detail=get_collection_byname('report_app_log_detail')

    query_report_app_log_detail={"date_start":{"$gt":date_period["date_start"],"$lt":date_period["date_end"]}      }
    query_report_app_log_detail["app"]=app_id


    cursor_report_app_log_detail=collection_report_app_log_detail.find(query_report_app_log_detail)

    dict_report_app_log_detail=dict()
    new_start_click_time=None
    for item_report_app_log_detail in cursor_report_app_log_detail:

        now_show_type=item_report_app_log_detail['show_type']
        actual_show_type=now_show_type
        if not new_start_click_time:
            new_start_click_time=item_report_app_log_detail['date_creation']
        else:
            new_start_click_time=min(new_start_click_time,item_report_app_log_detail['date_creation'])
        if actual_show_type.startswith('banner'):
            actual_show_type='banner'
        if now_show_type in dict_report_app_log_detail:
            dict_report_app_log_detail[actual_show_type]['number_click']+=item_report_app_log_detail['number_click']
        else:
            dict_report_app_log_detail[actual_show_type]=utils.try_get_childDict(item_report_app_log_detail,'number_click','show_type','_id','app')

    nonlocal['start_click_time']=new_start_click_time
    return dict_report_app_log_detail










def get_detail_dict(app_item,date_period):
    number_click='number_click'

    copy_dict=app_item.copy()
    #platform_name=copy_dict.pop('platform')
    copy_dict['platform']=get_platform_by_id(copy_dict['platform'])#平台
    copy_dict['level_log']=get_advert_level(*copy_dict['level_log'])#应用等级

    #cheshi_level_log=DocumentConvetor(documents={"items":copy_dict['level_log']},level=3).to_dict()["items"]

    dict_level_log={level_log['show_type']:level_log for  level_log in copy_dict['level_log']}

    default_advert_level=get_advert_level_by_name(out_ad_pay_type)


    copy_dict['pass_date']=nonlocal['pass_date']
    if not copy_dict['pass_date'] or copy_dict['removed']==True:
        return dict(app_item=None,date_period=None)
    if copy_dict['pass_date']:
        #copy_dict['pass_date'].replace(tzinfo=pytz.UTC)
        copy_dict['pass_date']=pytz.UTC.localize(copy_dict['pass_date'])
        copy_dict['pass_date'].astimezone(time_SH)

    #if len(copy_dict["level_log"])==1 and  "" in dict_level_log:
    if not  copy_dict["level_log"]:
        for must_show_type in show_type_list:
            new_dict=dict.fromkeys(level_detail_keys)
            new_dict['number_click']=""
            new_dict['show_type']=must_show_type
            new_dict['code']=""
            new_dict['developer']=" "
            new_dict['variable']=" "

    if not  len(copy_dict["level_log"])==1 :#如果有不指一种show_type的广告分级被设置
        for must_show_type in show_type_list:
            if  must_show_type not in  dict_level_log:
                new_dict=dict.fromkeys(level_detail_keys)
                new_dict[number_click]=0
                new_dict['show_type']=must_show_type
                new_dict['code']=out_ad_pay_type.upper()+'-E'
                new_dict['developer']=utils.get_value_by_search_path(default_advert_level,'[code="%s"].developer'%new_dict['code'])
                new_dict['variable']=0
                copy_dict['level_log'].append(new_dict)
                dict_level_log[must_show_type]=new_dict
    else:
        show_type_nameCompare,show_type_levelDict=dict_level_log.items()[0]
        for must_show_type in  show_type_list:
                if must_show_type!=show_type_nameCompare:
                    new_dict=show_type_levelDict.copy()
                    new_dict.setdefault('variable',0)
                    new_dict['show_type']=must_show_type
                    copy_dict['level_log'].append(new_dict)
                    dict_level_log[must_show_type]=new_dict




    dict_report_app_log_detail=get_report_app_log_detail(copy_dict['_id'],date_period)


    copy_dict['start_click_time']=nonlocal['start_click_time'] or None
    if copy_dict['start_click_time']:
        copy_dict['start_click_time']=pytz.UTC.localize(copy_dict['start_click_time'])
        copy_dict['start_click_time'].astimezone(time_SH)





    for show_type,item_report_app_log_detail in dict_report_app_log_detail.items():
        matched_level_log=dict_level_log.get(show_type,None)
        #assert matched_level_log is not None,show_type+'的应用分级不存在'
        if not  matched_level_log and show_type.startswith('banner'):
            show_type=show_type.split('_',1)[0]
            matched_level_log=dict_level_log.get(show_type,None)
            if matched_level_log is  None:
               print str(copy_dict['_id'])+' Name:'+copy_dict['name']+",show_type:"+show_type+",not exist!"
               continue
            #continue


        matched_level_log[number_click]=matched_level_log.get(number_click,0)+item_report_app_log_detail[number_click]
    #copy_dict['level_log']=dict_level_log.values()
    return dict(app_item=copy_dict,date_period=date_period)







def create_store_handler(para_data,date_period):
   pass








def get_output_by_dateperiod(data_handler,store_handler,dataperiod=None):
    if not dataperiod:
        today=datetime.datetime.now()
        date_start="{year}-{month}-{day}".format(year=today.year,month=today.month,day="01")
        date_end=today.strftime("%Y-%m-%d")
        dataperiod={'date_start':date_start,"date_end":date_end}

    collection_app=get_collection_byname('app')
    app_cursor=None
    app_query={"removed":False,u"status":{u"$in":get_status_objid(u"running", u"paused", u"verified",u'not verified',u'verifying',u'rejected')},u"level_log":{"$ne":[]}}
    #app_query={"removed":False}

    app_cursor=collection_app.find(app_query)
    print "app Count:",app_cursor.count()

    for app_item in  app_cursor:
        utils.serial_func([data_handler,store_handler],app_item=app_item,date_period=date_period)
        #store_handler(data_handler(app_item,dataperiod))



















if __name__=="__main__":
    date_start=datetime.datetime(2014,10,01,tzinfo=time_SH)
    #date_start.replace(tzinfo=time_SH)
    date_end=datetime.datetime(2014,11,01,tzinfo=time_SH)-datetime.timedelta(seconds=1)
    #date_end.replace(tzinfo=time_SH)


    #date_start,date_end=[ time_SH.localize(item) for item in (date_start,date_end)]
    date_start,date_end=[item.astimezone(pytz.UTC) for item in  (date_start,date_end)]

    date_period=utils.try_get_childDict(locals(),'date_start','date_end')

    row_number=0
    wb=xlwt.Workbook()
    wb.encode='gbk'
    file_name=date_period['date_start'].strftime("%Y-%m-%d")+'_'+date_period['date_end'].strftime("%Y-%m-%d")
    ws=wb.add_sheet(file_name)


    nolocal=dict()
    nolocal['row_num']=0
    for pair_index,pair_tuple in enumerate(name_key_pair_list):
        ws.write(nolocal['row_num'],pair_index,pair_tuple[0])
        get_orgin_func=functools.partial(utils.get_value_by_search_path,search_path=pair_tuple[1])
        if len(pair_tuple)==2:
            name_key_pair_list[pair_index]=(pair_tuple[0],get_orgin_func,lambda x:x)
        else:
            name_key_pair_list[pair_index]=(pair_tuple[0],get_orgin_func,pair_tuple[2] )


    pair_index=0

    def store_handler(app_item,date_period):
        if not app_item or not date_period:
            return
        nolocal['row_num']+=1
        row_num=nolocal['row_num']
        for pair_index,pair_tuple in enumerate(name_key_pair_list):
            orgin_data=pair_tuple[1](app_item)
            ws.write(row_num,pair_index,pair_tuple[2](orgin_data))


    get_output_by_dateperiod(get_detail_dict,store_handler,dataperiod=date_period)










    wb.save(file_name+'.xls')


    #get_connection()
    #get_output_by_dateperiod(print_data)
    print 'OK!'



















