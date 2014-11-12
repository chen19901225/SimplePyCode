#coding:utf-8
import StringIO
import codecs
import os
import string
import tempfile

__author__ = 'Administrator'


print_indent=' '*4



comment_format="""print "="*15,__file__,"="*15
 import sys
 print "Line No",sys._getframe().f_lineno
 print "="*15,__file__,"="*15"""





possible_comment_line_maxcount=5;

comment_format_lines=comment_format.splitlines()


def get_line_with_indent(py_line):
    """

    py_line:文件行
    return: 一个元祖,(缩进，去掉缩进的代码行)
    """
    if not py_line:
        return None,None
    for index in range(len(py_line)):
        if py_line[index] in   string.whitespace:
            continue
        else:
            break
    if index==0:
        return '',py_line
    else:
        return py_line[:index-1],py_line[index:]






for index,comment_format_line in enumerate(comment_format_lines):
    _,comment_format_line=get_line_with_indent(comment_format_line)
    if not  comment_format_line.endswith(os.linesep):
        comment_format_line+='\n'
    comment_format_lines[index]=comment_format_line






def remove_one_file_comment(file_name,print_indent=print_indent):
    if not file_name.endswith('.py'):
        print print_indent+file_name+"不是Py文件"
        return
    tmp_py_file=tempfile.TemporaryFile('w+b')
    with tmp_py_file:
        posible_comment_line=StringIO.StringIO()
        def write_new_comment_line(param_line):
            posible_comment_line.write(param_line)

        def write_something_to_tmpfile(param_unicode):
            tmp_py_file.write(param_unicode.encode('utf-8'))

        def read_something_from_tmpfile(func_name='readline'):
            func=getattr(tmp_py_file,func_name)
            if not func:
                raise ValueError,tmp_py_file.name+"不含有方法"+func_name
            func_result=func()
            if func_result and isinstance(func_result,basestring):
                func_result=func_result.decode('utf-8')
            return func_result




        with codecs.open(file_name,'r',encoding='utf-8') as read_f:
            read_line=None
            read_index=0
            while 1:
                read_index+=1

                read_line=read_f.readline()
                if not read_line:
                    break
                line_ident,line_code=get_line_with_indent(read_line)
                if not line_code:
                    continue
                if line_code==comment_format_lines[0]:
                    write_new_comment_line(read_line)
                    #posible_comment_line.write(read_line)

                    while 1:
                        second_line=read_f.readline()
                        line_ident,line_code=get_line_with_indent(second_line)
                        if not line_code or line_code in string.whitespace:
                            continue
                        else:
                            break

                    posible_comment_line.write(os.linesep+second_line)
                    if line_code==comment_format_lines[1]:
                        try_find_comment_index=0
                        try_find_comment_status=False
                        while try_find_comment_index<possible_comment_line_maxcount and not try_find_comment_status:
                            try_new_line=read_f.readline()
                            try_line_ident,try_line_code=get_line_with_indent(try_new_line)
                            #posible_comment_line.write(os.linese+try_new_line)
                            write_new_comment_line(try_new_line)
                            if try_line_code==comment_format_lines[-1]:
                                try_find_comment_status=True
                            try_find_comment_index+=1

                        if not try_find_comment_status and  try_find_comment_index>=possible_comment_line_maxcount:
                            #tmp_py_file.write(posible_comment_line.getvalue())
                            write_something_to_tmpfile(posible_comment_line.getvalue())
                        else:
                            pass
                            #posible_comment_line.seek(0)
                            #for #comment_line #in #posible_comment_line:
                                #comment_line_ident,comment_line_code=get_line_with_indent(comment_line)
                                #write_something_to_tmpfile(comment_line_ident+'#'+comment_line_code)



                    else:
                        #tmp_py_file.write(posible_comment_line)
                        write_something_to_tmpfile(posible_comment_line.getvalue())

                else:
                    write_something_to_tmpfile(read_line)
                    #tmp_py_file.write(read_line)

        #####################################################################################
        tmp_py_file.seek(0)
        with codecs.open(file_name,'w',encoding='utf-8') as writef:
            for tmp_line in tmp_py_file:
                tmp_line=tmp_line.decode('utf-8')
                writef.write(tmp_line)





if __name__=="__main__":
    ceshi_file='C:\\Users\\Administrator\\Desktop\\admin.py'
    remove_one_file_comment(ceshi_file)
    print "Over"









