__author__ = 'Administrator'

class Person(object):
    def __init__(self,*args,**kwargs):
        self.id=0
        self.Name=''
        self.__dict__.update(**kwargs)

    def __str__(self):
        return "%s-%s"%(self.id,self.Name)


if __name__=="__main__":
    p1=Person(id=1,Name="chen")
    p2=Person(id=2,Name="chen")
    p3=Person(id=1,Name="XXX")
    p_list=[p1,p2,p3]

    p_matched_list=(temp for temp in p_list if temp.id==1)

    print iter(p_matched_list).next()

