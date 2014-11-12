import math


class Structure(object):
    _fields=[]
    def __init__(self,*args):
        if len(args)!=len(self._fields):
            raise TypeError('Excpected {} arguments'.format(len(self._fields)))

        for name,value in zip(self._fields,args):
            setattr(self,name,value)
class Stock(Structure):
    _fields = ['name','shares','price']

class Point(Structure):
    _fields = ['x','y']

class Circle(Structure):
    _fields = ['radius']
    def area(self):
        return math.pi*self.radius**2




if __name__=="__main__":
    # tuple_1=(1,2,3)
    # tuple_2=('a','b','c')
    # for name,value in zip(tuple_1,tuple_2):
    #     print name,value
    pass
    s=Stock('ACME',50,91.1)
    p=Point(2,3)
    c=Circle(4.6)

