__author__ = 'Administrator'
class Login(object):
    def __init__(self,**kwargs):
        self.Key=""
        self.Status=0
        self.IsMerchant=0
        self.Typecode=0
        self.ImgIndex=0
        self.Name=""
        self.MerchantId=0
        self.MerchantLevel=0
        self.Uid=0
        self.__dict__.update(kwargs)
    def isavailable_return(self):
        success_return=True
        if self.Status!=0 or not self.Key or not  self.Uid or not  self.Name:
            success_return=False
        else:
            if self.IsMerchant==1 and self.MerchantId<=0:
                success_return=False
        return success_return


    def loginInfo_isequal (self,other,exceptKey=True):
        isequal=True
        if not  isinstance(other,Login):
            isequal=False
        else:
            for key,value in self.__dict__.iteritems():
                if key=="Key" and exceptKey==True:
                    continue
                if value!=other.__dict__[key]:
                    isequal=False
                    break
        return isequal








