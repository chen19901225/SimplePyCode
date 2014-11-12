import abc

class IStream(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def read(self,maxbytes=-1):
        pass
    @abc.abstractmethod
    def write(self,data):
        pass

class SocketStream(IStream):
    def read(self,maxbytes=-1):
        print 'Read'

    def write(self,data):
        print 'write data :{}'.format(data)

if __name__=="__main__":

