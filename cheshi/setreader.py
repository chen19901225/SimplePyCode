__author__ = 'Administrator'
#coding=utf-8
import io
import os,re
class Setting_Reader(object):
    def __init__(self,filename='sett.txt'):
        _localDir=os.path.dirname(__file__)
        _curpath=os.path.normpath(os.path.join(_localDir,filename))

        with io.open(_curpath,'r',-1,'utf-8') as file_reader:
            for line_content in file_reader:
                line_content=line_content.strip()
                line_content=line_content.replace(' ','')
                if not line_content:
                    continue
                line_pair=line_content.split('=')
                if re.match('^-?\d+$',line_pair[1]):#自动转化为整数
                    line_pair[1]=int(line_pair[1])
                self.__dict__[line_pair[0]]=line_pair[1]
            if self.domain_url.endswith('\\'):
                self.domain_url=self.domain_url[:-1]
    def __unicode__(self):
        return self.__dict__.iteritems()
    def print_self(self):
        for key,value in self.__dict__.iteritems():
            print key,value
static_setting_reader=None
def get_static_setting_reader():
    global  static_setting_reader
    if not static_setting_reader:
        static_setting_reader=Setting_Reader()
    return static_setting_reader
if __name__=="__main__":
    setting_reader=Setting_Reader()
    setting_reader.print_self()





