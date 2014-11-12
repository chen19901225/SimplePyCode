#coding:utf-8
import codecs
import os
import io
import pysvn


except_files_list=['config.ini.dev','station.py','outlet']

svn_client=None
def get_client():
    global  svn_client
    if not svn_client:
        svn_client=pysvn.Client()
    return svn_client




def read_file_subversion_state(file_name):
    """

    """
    #f=codecs.open(file_name)
    if is_file_uncommited(file_name):
        return os.path.splitext(file_name)
    return None



def is_file_uncommited(file_name):
    #f=codecs.open(file_name)
    client=get_client()
    except_name_list=(".idea",".svn",'cache','.gitignore')#去掉文件夹
    for except_name in except_name_list:
        if file_name.endswith(except_name):
            return False

        if  '\\'+except_name+'\\' in file_name:
            return False

    tmp_file_name=os.path.basename(file_name)

    if tmp_file_name in  except_files_list:
        return False
    commit_info=client.info(file_name)
    commit_status=client.status(file_name)

    if commit_status[-1].data['text_status']==pysvn.wc_status_kind.modified:
        return True
    return False

def find_uncommit_files_underDir(dir_name,file_list):
    for tmp_file in  file_list:
        if is_file_uncommited(os.path.join(dir_name,tmp_file)):
            yield (dir_name,tmp_file)


def walk_generator_list(*generator_list):
    for walk_generator in generator_list:
        for walk_item in walk_generator:
            yield walk_item



def find_uncommit_files(dir_name):

    for walk_root,walk_dir_list,walk_file_list in os.walk(dir_name):
        #yield (yield find_uncommit_files_underDir(walk_root,walk_dir_list))
        #yield (yield find_uncommit_files_underDir(walk_root,walk_file_list))
        for  matched_item in walk_generator_list(find_uncommit_files_underDir(walk_root,walk_file_list)):
            yield matched_item



def find_and_print_uncommited_files(dir_name):
    for ucommited_items in find_uncommit_files(dir_name):
        print ucommited_items[0],ucommited_items[1]



if __name__=="__main__":
    dir_name='F:\\svn_balin'
    #print is_file_uncommited(dir_name)
    find_and_print_uncommited_files(dir_name)

    #dir_name='F:\\svn_balin\\config.ini.prod'
    #print is_file_uncommited(dir_name)


