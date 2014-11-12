
class MyClass(object):
    def __new__(cls):
        print '__new__ called'
        return  object.__new__(cls)

    def __init__(self):
        print '__init__ called'
        self.a=1

class MyOtherClassWithoutAConstructor(MyClass):
    pass

class MyOtherClass(MyClass):
    def __init__(self):
        print 'MyOther class __init__ called'
        super(MyOtherClass,self).__init__()
        self.b=2


if __name__=="__main__":
    instance=MyClass()
    instance=MyOtherClass()
