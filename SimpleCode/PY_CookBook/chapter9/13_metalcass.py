
class NoInstances(type):
    def __call__(self,*args,**kwargs):
        raise TypeError("Cant's instantiate directly")


class Spam(type):

    __metaclass__==NoInstances

    @staticmethod
    def grok(x):
        print "Spam.grok"


if __name__=="__main__":
    print Spam.grok(42)
    s=Spam()