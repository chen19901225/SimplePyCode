import math


def lazyproperty(func):
    name='_lazy_'+func.__name__
    @property
    def lazy(self):
        if hasattr(self,name):
            return getattr(self,name)
        else:
            value=func(self)
            setattr(self,name,value)
            return value
    return lazy

class Circle(object):
    def __init__(self,radius):
        self.radius=radius

    @lazyproperty
    def area(self):
        print 'Computing area'
        return math.pi*self.radius**2

    @lazyproperty
    def perimeter(self):
        print 'Computing perimeter'

        return 2*math.pi*self.radius

if __name__=="__main__":
    c=Circle(4.0)
    print vars(c)
    print c.radius

    print c.area
    c.area=50
    print c.area
    print c.perimeter
    print c.perimeter

