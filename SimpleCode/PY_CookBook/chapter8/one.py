
class Integer(object):
    def __init__(self,name):
        self.name=name
    def __get__(self,instance,cls):
        if instance is None:
            return self
        else:
            return instance.__dict__[self.name]

    def __set__(self,instance,value):
        if not isinstance(value,int):
            raise TypeError('Expected an int')
        instance.__dict__[self.name]=value

    def __delete__(self,instance):
        del instance.__dict__[self.name]


class Point(object):
    x=Integer('x')
    y=Integer('y')
    def __init__(self,x,y):
        self.x=x
        self.y=y

if __name__=="__main__":
    p=Point(2,3)
    print p.x
    p.y=2.3
    print p.y