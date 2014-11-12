import datetime
import json

__author__ = 'Administrator'

class Food(object):
    def __init__(self,*args,**kwargs):
        self.id=0
        self.mid=0
        self.pname=""
        self.price=0.00
        self.pubtime=datetime.datetime.now()
        self.starttime=datetime.datetime.now()
        self.endtime=datetime.datetime.now()
        self.tags=""
        self.tagbs=""
        self.memo=""
        self.deleteflag=False
        self.pids=""

        self.__dict__.update(kwargs)

    def __eq__(self, other):
        for key,value in self.__dict__.iteritems():
            if key=="tagbs":
                continue
            if value !=other.__dict__.get(key,None):
                return False
        return True

    def __str__(self):
        return "%s-%s"%(self.pname,self.tags)

    def isAvailable(self):
        return self.deleteflag==False and self.endtime>datetime.datetime.now()








