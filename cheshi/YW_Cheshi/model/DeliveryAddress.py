__author__ = 'Administrator'

class DeliveryAddress(object):
    def __init__(self,*args,**kwargs):
        self.id=0
        self.uid=0
        self.address=''
        self.contacttel=''
        self.contactman=''
        self.__dict__.update(kwargs)

    def __str__(self):
        return "%s-%s"%(self.address,self.contacttel)

    def __eq__(self, other):
        if not isinstance(other,DeliveryAddress):
            return False
        if any  (self.__getattribute__(propname)!=other.__getattribute__(propname) for propname in self.__dict__.iterkeys()):
            return False
        return True



