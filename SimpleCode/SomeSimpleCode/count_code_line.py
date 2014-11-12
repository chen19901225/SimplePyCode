import codecs
import os


count_dir=r'D:\bailin\svn_adnetwork\apps'


def get_lineno_of_file(file_name,extension='.py'):
    file_lineno=0
    if file_name.endswith(extension):
        with codecs.open(file_name,'r','utf-8') as f:
            for line in f:
                if not line:
                    continue
                line=line.strip()
                if not line:
                    continue
                if line.startswith(('import','from','#','"')):
                    continue
                file_lineno+=1

        return file_lineno
    else:
        return 0
def get_dir_lineno(dir_name,extention='.py'):
    dir_lineno=0
    for dir_path,tmp_dir_name_list,tmp_file_name_list in os.walk(dir_name):
        for tmp_file_name in tmp_file_name_list:
            abs_file_name=os.path.join(dir_path,tmp_file_name)
            dir_lineno+=get_lineno_of_file(abs_file_name)
    return dir_lineno

print get_dir_lineno(count_dir)






