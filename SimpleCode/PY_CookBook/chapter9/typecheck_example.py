import functools

class A(object):
    def decorator1(self,func):
        @functools.wraps(func)
        def wrapper(*args,**kwargs):
            print "Decorator 1"
            return func(*args,**kwargs)
        return wrapper

    @classmethod
    def decorator2(cls,func):
        @functools.wraps(func)
        def wrapper(*args,**kwargs):
            print "Decoraor 2"
            return func(*args,**kwargs)
        return wrapper


a=A()

@a.decorator1
def span():
    pass

@A.decorator2
def grok():
    pass

span()
grok()

