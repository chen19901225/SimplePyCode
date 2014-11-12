__author__ = 'Administrator'
#ecoding=utf-8

def execute_insert_dict(cur,insert_dict):
    """
    cur :游标
    insert_dict：要插入的字典
    """
    values=[]
    for key,(value,remark)  in insert_dict.iteritems():
        values.append((key,value,remark))
    single_insert_format="insert into TB_SysConfig(TB_SysConfig.key,TB_SysConfig.values,TB_SysConfig.remark,TB_SysConfig.type,TB_SysConfig.sort) values ('%s','%s','%s','1',0)"
    for key,value,remark in values:
        #print key,value,remark
        single_insert_sql=single_insert_format%(key,value,remark)
        print single_insert_sql+";"
        #action(single_insert_sql)
def execute_update_dict(parm_cur,parm_update_dict):
    """
    parm_cur:游标
    parm_update_dict:执行更新操作的字典
    """
    single_update_format=u"update TB_SysConfig set TB_SysConfig.values='{1}' where TB_SysConfig.key='{0}' "
    for for_key,for_values in parm_update_dict.iteritems():
        single_update_sql_str=single_update_format.format(for_key,for_values)
        print single_update_sql_str+";"
        #action(single_update_sql_str)

import io
file_path=r'C:\Users\Administrator\Desktop\errorid.txt'
code_des_dict=dict()
with io.open(file_path,'r',-1,'gbk') as f:
    while True:
        line_summary=f.readline()
        if not line_summary:
            break #第一行不是标注,则继续往下读
        line_summary=line_summary.strip()
        if not line_summary:
            continue
        if line_summary.endswith('summary>'):#如果第一行是标注
            code_description=f.readline().strip().strip('/').strip()#获取状态码的描述信息
            f.readline()
            code_line=f.readline().strip()
            if 'const' in code_line:#表示是存储错误码的东西而不是public class
                err_code=code_line.split('=')[1][:-1].strip()
                err_code=int(err_code)
                err_str=code_line.split('=')[0].split()[-1].strip()
                code_des_dict[err_code]=(code_description,err_str)
key_value_items=code_des_dict.items()
key_value_items.sort(key= lambda x:x[0])
"""
for key,value in key_value_items:
    print key,value[0],value[1]
"""
#把配置更新到数据库
import MySQLdb
import re
try:
    conn=MySQLdb.connect(host='192.168.1.183',user='jhtest',passwd='jhtest',db='DBICYPM',port=3306,charset='utf8')
    config_get_url='select TB_SysConfig.key,TB_SysConfig.values,TB_SysConfig.remark,TB_SysConfig.type from TB_SysConfig'
    cur=conn.cursor()
    cur.execute(config_get_url)
    config_err=dict()#数据库里已经存在的配置
    for row in cur:
        object_key=row[0]
        if re.match('^-?\d+$',object_key):
            config_err[int(object_key)]=row
    #print config_err
    #对不存在的错误码进入插入
    insert_dict={ str(key):value for key,value in  key_value_items if key not in config_err} #插入的数据字典

    execute_insert_dict(cur=cur, insert_dict=insert_dict)
    #执行更新
    update_dict={ str(err_int):up_des for err_int, (up_des,up_code) in code_des_dict.iteritems() if err_int in config_err and up_des!=config_err[err_int][1]  }

    execute_update_dict(cur,update_dict)


    #对已经存在的错误码进行更新
    #cur.executemany('insert into TB_SysConfig(TB_SysConfig.key,TB_SysConfig.values,TB_SysConfig.remark,TB_SysConfig.type) values (%s,%s,%s,"1") ',values)

    conn.commit()
    cur.close()
    conn.close()
except Exception as e:
    print e





