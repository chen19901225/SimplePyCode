import codecs
import io
import os
import tempfile




def clear_onefile(file_name):
    if not  file_name.endswith('.py'):
        return
    with tempfile.TemporaryFile(u'w+b') as f:
        #f=io.TextIOWrapper(f,encoding='utf-8')
        with codecs.open(file_name,'r',encoding=u'utf-8') as read_f:
            for line in read_f:
                if  line and  not line.startswith(u'__author__'):
                    f.write(line.encode('utf-8'))

        with codecs.open(file_name,'w',encoding=u'utf-8') as write_f:
            f.seek(0)
            for line in f:
                write_f.write(line)

def clear_dir(dir_name):
    for walk_root,walk_dir_list,walk_file_list in os.walk(dir_name):
        for walk_file in  walk_file_list:
            clear_onefile(os.path.join(walk_root,walk_file))


if __name__=="__main__":
    file_path='C:\\Users\\chenqinghe\\Desktop\\one.py'
    clear_onefile(file_path)
    dir_name='E:\\pycode\\SimpleCode'
    clear_dir(dir_name)
    print 'Clear OK'


