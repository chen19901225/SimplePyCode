#coding:utf-8
import codecs
import os
import utils

__author__ = 'Administrator'


indent_levl=' '*4


def is_file_contain_word(file_name,search_word):
    file_path,file_extension=os.path.splitext(file_name)
    if not file_extension.endswith('.py'):
        #print indent_levl+file_name +" Not end with .py"
        return (False,None,None)
    file_extension=file_extension[1:]
    line_index=0
    with codecs.open(file_name) as f:
        for line in f:
            line_index+=1
            if search_word in line:
                return (True,file_extension,line_index)

        return (False,None,None)




def filter_with(search_word):
    def filter_file_list(file_root,file_list):
        for  walk_file in file_list:
            abs_file=os.path.join(file_root,walk_file)
            matched_item=is_file_contain_word(abs_file,search_word)

            if matched_item[0]:
                 yield  (file_root,walk_file)+matched_item[1:]
    return filter_file_list




if __name__=="__main__":

    dir_name='F:\\svn_balin'
    utils.find_meeted_files(dir_name,filter_with('admin_get_ad_option'))
    print "OK"







