#coding:utf-8
#from bottle import ConfigDict

class SelfConfigDict(dict):

    def __init__(self,*args,**kwargs):
        self._meta={}
        self._onchange=lambda  key,value:None
        if args or kwargs:
            self.update(*args,**kwargs)


    def update(self,*args,**kwargs):
        if args:
            try_prefix=args[0]
            assert isinstance(try_prefix,basestring),"Key必须为字符串 "
            prefix=try_prefix.strip('.')+'.'
            args=args[1:]
        for key,value in dict(*args,**kwargs):
            self[prefix+key]=value

    def __setitem__(self, key, value):
        assert isinstance(key,basestring),"Key必须为字符串"
        value=self._meta.get(key,{}).get('filter',lambda  x:x)(value)
        if key in self and self[key] is value :
            return
        self._onchange(key,value)
        dict.__setitem__(self,key,value)

    def meta_set(self,key,in_filter_name,in_filter_func):
        assert  isinstance(in_filter_name,basestring),in_filter_name+"必须为字符串"
        self._meta.get(key,{}).setdefault(in_filter_name,in_filter_func)


