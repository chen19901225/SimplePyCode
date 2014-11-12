#coding:utf-8
import codecs
import string
import tempfile
import sys
import io
import utils


import os





def format_AbsolutePathFile(file_name):
    current_word=u''
    prev_byte=''
    line_content=u''
    indent_level=0
    read_word_list=[]
    quote_tuple=(u'"','"','\'',u'\'')
    reg_tuple=(u'/','/')
    line_writeline=u''
    #global  current_word,prev_byte,line_content,indent_level,read_word_list,quote_tuple,line_writein


    temp_file=tempfile.TemporaryFile('w+t')


    with codecs.open(file_name,'r',encoding='utf-8') as sourceFile:
        def complete_read_currentWord():
            #global  current_word
            nonlocal current_word
            if not current_word:
                return
            read_word_list.append(current_word)
            current_word=u''

        line_writein=u''
        def write_formatLine(des_fileDescrption):
            nonlocal  line_writein
            if  not line_writein:
                line_writein=indent_level*4*u' '
            line_writein+=''.join(read_word_list)+os.linesep
            del read_word_list[:]
            des_fileDescrption.write(line_writein)
            line_writein=u''

        while 1:
            read_byte=sourceFile.read(1)
            if read_byte in (None,u'',''):
                break

            if read_byte in (string.ascii_letters+string.digits+'$'):

                #字符是字母或者数字
                if len(read_word_list)>0 and  read_word_list[0]  in ('}',';'):
                    write_formatLine(temp_file)
                current_word+=read_byte

            elif any(read_byte  in item for item in ( string.punctuation,string.whitespace)):
                #当前字符不是 字母以及数字
                if read_byte=='_':
                    current_word+=read_byte
                    continue
                if current_word.startswith(quote_tuple):
                    #当前单词是一个字符串
                    current_word+=read_byte
                    if read_byte not in quote_tuple:
                        pass
                    else:
                        if read_byte ==current_word[0]:
                            complete_read_currentWord()
                    continue

                if read_byte in quote_tuple:
                    complete_read_currentWord()
                    current_word+=read_byte
                    continue

                is_contain,contained_key=utils.try_get_containedElement(current_word,reg_tuple)
                if not is_contain:
                    pass
                else:
                    if read_byte==contained_key:
                        current_word+=read_byte
                        complete_read_currentWord()
                    else:
                        current_word+=read_byte
                    continue

                if read_byte in reg_tuple:
                    complete_read_currentWord()
                    current_word+=read_byte
                    continue

                complete_read_currentWord()

                if read_byte in string.punctuation:
                    read_word_list.append(read_byte)
                    #line_writein=indent_level*4*u' '



                    if read_byte in ';' :
                        if len(read_word_list)>0 and read_word_list[0]!='for':
                            write_formatLine(temp_file)


                    elif  read_byte in ('{',):
                        write_formatLine(temp_file)
                        indent_level+=1

                    elif read_byte in '}':
                        read_word_list,the_last_ele=read_word_list[:-1],read_word_list[-1]
                        if len(read_word_list)>0 and read_word_list[-1] not in ('{','}')  and ':' not in read_word_list:
                            read_word_list.append(';')
                        write_formatLine(temp_file)

                        indent_level-=1
                        read_word_list.append(the_last_ele)



                elif read_byte in string.whitespace:
                    read_word_list.append(read_byte)










        #temp_file.write(sourceFile.read().encode('utf-8'))

    temp_file.seek(0)
    read_content= temp_file.read()
    with codecs.open('format_js.js','w',encoding='utf-8') as result_fileDe:
        result_fileDe.write(read_content)

    print(read_content)




def format_FileWithDir(arg,dirname,filenames):
    for short_filename in filenames:
        absolute_file_name=os.path.join(dirname,short_filename)
        format_AbsolutePathFile(absolute_file_name)


def format_fileOrDir_WithAbsolutePath(in_name):
    if os.path.isfile(in_name):
        format_AbsolutePathFile(in_name)
    else:
        os.path.walk(in_name,format_FileWithDir,())


def format_fileOrDir(in_name):
    absolute_path=in_name
    if not os.path.isabs(absolute_path):
        current_dir=os.path.dirname(os.path.abspath(__file__))
        absolute_path=os.path.join(current_dir,absolute_path)

    format_fileOrDir_WithAbsolutePath(absolute_path)

if __name__=="__main__":
    format_fileOrDir('cheshi.js')







