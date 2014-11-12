__author__ = 'Administrator'

class TB_MenuLabel(object):
    def __init__(self,*args,**kwargs):
        self.id=0
        self.mid=0
        self.lname=""
        self.__dict__.update(kwargs)

    def __str__(self):
        return "%s-%s"%(self.id,self.lname)

    def __eq__(self, other):
        return self.id==other.id  and self.lname==other.lname


