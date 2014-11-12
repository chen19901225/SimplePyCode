
class Structure(object):
    _fields=[]

    def __init__(self,*args,**kwargs):
        if len(args)>len(self._fields):
            raise TypeError('Expected {} arguments'.format(len(self._fields)))

        for name,value in zip(self._fields,args):
            setattr(self,name,value)

        for name in  self._fields[len(args):]:
            setattr(self,name,kwargs.pop(name))

        if kwargs:
            raise  TypeError('Invalid arguments:{}'.format(','.join(kwargs)))

if __name__=="__main__":
    class Stock(Structure):
        _fields = ['name','shares','price']

    s1=Stock('Acme',50,91.1)
    s2=Stock('Acme',50,price=91.1)
    s3=Stock('acme',shares=50,price=91.1)

