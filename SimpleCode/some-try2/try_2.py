__author__ = 'Administrator'
#coding:utf-8
import datetime
import functools
import xlwt

__author__ = 'Administrator'
import pymongo
import utils
host='192.168.219.135'
port=27017
conn=None
default_db_name="advert_platform_zheshi"
app_status_dict=None
app_platform_dict=None
#must_include_advert_types=("full",)
name_key_pair_list=[(u"应用名称",'name'),
    (u"应用Key",'api_key'),
    (u"应用系统",'platform')   ]

type_name_value_pair=[(u"banner","banner"),(u"插屏",'popup'),(u"全屏",'full_screen'),(u'开屏','open_screen')]

propforType_nameValue_pair=[(u"日均点击量","number_click"),(u'级别',"code"),(u"对应价格","developer")]

type_value_list=[pair[1] for pair in type_name_value_pair]

level_keys=('_id','show_type','code','developer')
level_detail_keys=level_keys+("number_click",)


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


    for item_advert_level in cursor_advert_level:
        new_dict=utils.try_get_childDict(item_advert_level,*level_keys)
        new_dict['number_click']=0
        list_advert_level.append(new_dict)
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


    cursor_report_app_log_detail=collection_report_app_log_detail.find(**query_report_app_log_detail)

    dict_report_app_log_detail=dict()
    for item_report_app_log_detail in cursor_report_app_log_detail:
        dict_report_app_log_detail[item_report_app_log_detail['show_type']]=utils.try_get_childDict(item_report_app_log_detail,'number_click','show_type','_id','app')

    return dict_report_app_log_detail










def get_detail_dict(app_item,date_period):
    number_click='number_click'

    copy_dict=app_item.copy()
    #platform_name=copy_dict.pop('platform')
    copy_dict['platform']=get_platform_by_id(copy_dict['platform'])#平台
    copy_dict['level_log']=get_advert_level(*copy_dict['level_log'])#应用等级

    dict_level_log={level_log['show_type']:level_log for  level_log in copy_dict['level_log']}


    for must_type in type_value_list:
        if  must_type not in  dict_level_log:
            new_dict=dict.fromkeys(level_detail_keys)
            new_dict[number_click]=0
            new_dict['show_type']=must_type
            copy_dict['level_log'].append(new_dict)
            dict_level_log[must_type]=new_dict

    dict_report_app_log_detail=get_report_app_log_detail(copy_dict['_id'],date_period)



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
    app_query={"removed":False,'status':get_status_objid(u"running", u"paused", u"verified",u'not verified',u'verifying',u'rejected')}
    app_cursor=collection_app.find(**app_query)
    print "app Count:",app_cursor.count()

    for app_item in  app_cursor:
        utils.serial_func([data_handler,store_handler],app_item=app_item,date_period=date_period)
        #store_handler(data_handler(app_item,dataperiod))













for type_name,type_value in type_name_value_pair:
    for prop_name,prop_value in propforType_nameValue_pair:
        new_search_name=u"{type_name}{prop_name}".format(**locals())
        new_search_value='level_log[show_type="{type_value}"].{prop_value}'.format(**locals())
        name_key_pair_list.append((new_search_name,new_search_value))





if __name__=="__main__":
    date_start="2014-10-01"
    date_end="2014-11-01"
    date_period=utils.try_get_childDict(locals(),'date_start','date_end')


    row_number=0
    wb=xlwt.Workbook()
    wb.encode='gbk'
    file_name=date_period['date_start']+'_'+date_period['date_end']
    ws=wb.add_sheet(file_name)


    nolocal=dict()
    nolocal['row_num']=0
    for pair_index,pair_tuple in enumerate(name_key_pair_list):
        ws.write(nolocal['row_num'],pair_index,pair_tuple[0])

        name_key_pair_list[pair_index]=(pair_tuple[0],functools.partial(utils.get_value_by_search_path,search_path=pair_tuple[1]))

    pair_index=0

    def store_handler(app_item,date_period):
        nolocal['row_num']+=1
        row_num=nolocal['row_num']
        for pair_index,pair_tuple in enumerate(name_key_pair_list):
            ws.write(row_num,pair_index,pair_tuple[1](app_item))


    get_output_by_dateperiod(get_detail_dict,store_handler,dataperiod=date_period)










    wb.save(file_name+'.xls')


    #get_connection()
    #get_output_by_dateperiod(print_data)
    print 'OK!'









