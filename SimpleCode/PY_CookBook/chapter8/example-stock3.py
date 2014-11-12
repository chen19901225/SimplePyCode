
def init__fromlocals(self):
    import sys
    for k,v in locals():
        if k !='self':
            setattr(self,k,v)
class Stock(object):
    def __init__(self,name,shares,price):
        init__fromlocals(self)
if __name__=="__main__":
    s=Stock(1,2,3)
