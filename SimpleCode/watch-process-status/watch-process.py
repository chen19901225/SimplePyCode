#coding:utf-8
import os
import re
import string
import time
import setting
import sh


mem_name=setting.mem_name
status_name_list=setting.status_name_list

def serial_func(ele,*func_list):
    re_value=ele
    for tmp_func in func_list:
        if not re_value:
            break
        else:
            re_value=tmp_func(re_value)
    return re_value

def convertB_TO_G(param_value):
    """
    把byte转换为G
    :param param_value:
    :return:
    """
    return round(param_value/float(1024**2),2)

def get_processinfo_fromfile(in_file_name):
    """
    从status文件中获取进程状态
    :param in_file_name: 文件名 必须符合/proc/pid/status
    :return:一个包含进程状态的字典
    """
    process_info_dict=dict.fromkeys(status_name_list)
    process_info_dict[mem_name]=0
    with open(in_file_name) as f:
        for line in f:
            if line.startswith(status_name_list):
                key_value_pair=map(string.strip,line.split(':'))
                process_info_dict[key_value_pair[0]]=key_value_pair[1]

                if key_value_pair[0]==mem_name:
                    size_str=process_info_dict[key_value_pair[0]]
                    process_info_dict[key_value_pair[0]]=serial_func(size_str,lambda x:x.split()[0],float,convertB_TO_G)

    return process_info_dict

def read_process_info():
    """
    读取进程信息。
    读取进程所占有的内在，只要同名，则为一个进程
    :return:
    进程信息的字典
    """
    process_info_collection_dict=dict()
    dir_root='/proc'
    for process_dir in os.listdir(dir_root):
        if process_dir.isdigit():
            status_file_name=os.path.join(dir_root,process_dir,'status')
            this_process_status_dict=get_processinfo_fromfile(status_file_name)

            process_name=this_process_status_dict['Name']
            if process_name not in process_info_collection_dict:
                process_info_collection_dict[process_name]=this_process_status_dict

            else:
                contained_dict=process_info_collection_dict[process_name]

                contained_dict[mem_name]+=this_process_status_dict[mem_name]

                process_info_collection_dict[process_name]=contained_dict



    return process_info_collection_dict





def get_sys_meminfo():
    """
    获取系统的内存信息
    :return:
    """
    lineindex=0
    for line in sh.free(_iter=True):
        lineindex+=1
        if lineindex==1:
            mem_name_list=line.split()
        elif lineindex==2:
            mem_value_list=map(lambda x: serial_func(x,int,convertB_TO_G) ,line.split()[1:])
            return dict(zip(mem_name_list,mem_value_list))

def get_line(process_info_dict):
    status_value_list=map(lambda  x: process_info_dict[x],status_name_list)

    return ' '.join(status_value_list)




def get_process_meminfo(process_info_dict):
    meminfo_dict=get_sys_meminfo()


    process_mem_digit=process_info_dict[mem_name]
    process_mem_perccent=process_mem_digit/float(meminfo_dict['total'])*100

    return process_mem_perccent,process_mem_digit



def is_processinfo_warning(process_info_dict):
    process_percent_mem,process_mem_digit=get_process_meminfo(process_info_dict)
    if process_percent_mem>setting.max_mem_percent or  process_mem_digit>setting.max_mem_digit:
        return True
    else:
        return False









if __name__=="__main__":
    for_index=0
    while True:
        for_index+=1
        process_info_list_dict=read_process_info()
        for process_name,process_info_dict in process_info_list_dict.iteritems():
            if is_processinfo_warning(process_info_dict):
                tmp_process_mem_percent,tmp_process_mem_digit=get_process_meminfo(process_info_dict)
                print "NO:{p_no},Procss:{process_name},ID:{process_id},mem_percent:{mem_percent},mem_digit:{mem_digit}G".format(process_name=process_name,
                mem_percent=tmp_process_mem_percent,mem_digit=tmp_process_mem_digit,process_id=process_info_dict['Pid'],p_no=for_index)


        time.sleep(setting.sleep_time)








