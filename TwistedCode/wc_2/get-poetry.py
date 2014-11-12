import optparse
from twisted.internet import reactor
from twisted.internet.protocol import Protocol, connectionDone, ClientFactory
import datetime

__author__ = 'cqh'
def parse_args():
    usage="""usage: %prog [options] [hostname]:port ...

This is the Get Poetry Now! client, Twisted version 1.0.
Run it like this:

  python get-poetry.py port1 port2 port3 ...

If you are in the base directory of the twisted-intro package,
you could run it like this:

  python twisted-client-1/get-poetry.py 10001 10002 10003

to grab poetry from servers on ports 10001, 10002, and 10003.

Of course, there need to be servers listening on those ports
for that to work."""
    paser=optparse.OptionParser()
    _,addresses=paser.parse_args()
    if not addresses:
        print paser.format_help()
    def parse_address(addr):
        if ':' not in addr:
            host,port='127.0.0.1',addr
        else:
            host,port=addr.split(':',1)

        if not port.isdigit():
            paser.error('port must be integers.')

        return host,int(port)
    return map(parse_address,addresses)


class PoetryProtocol(Protocol):
    poem=''
    task_num=0

    def dataReceived(self, data):
        self.poem+=data
        msg='Task %d:got %d bytes of poetry from %s'
        print msg%(self.task_num,len(data),self.transport.getPeer())

    def connectionLost(self, reason=connectionDone):
        self.poemReceived(self.poem)
    def poemReceived(self,poem):
        self.factory.poem_finished(self.task_num,poem)

class PoetryClientFactory(ClientFactory):
    task_num=1
    protocol = PoetryProtocol

    def __init__(self,poetry_count):
        self.poetry_count=poetry_count
        self.poems={}

    def buildProtocol(self, addr):
        proto=ClientFactory.buildProtocol(self,addr)
        proto.task_num=self.task_num
        self.task_num+=1
        return proto


    def poem_finished(self,task_num=None,poem=None):
        if task_num is not None:
            self.poems[task_num]=poem

        self.poetry_count-=1

        if self.poetry_count==0:
            self.report()
            reactor.stop()

    def report(self):
        for i in self.poems:
            print 'Task %d:%d bytes of poetry'%(i,len(self.poems[i]))

    def clientConnectionFailed(self, connector, reason):
        print 'Failed to connect to ',connector.getDestination()
        self.poem_finished()


def poetry_main():
    addresses=parse_args()

    start=datetime.datetime.now()

    factory=PoetryClientFactory(len(addresses))
    for address in addresses:
        host,port=address
        reactor.connectTCP(host,port,factory)

    reactor.run()

    elapsed=datetime.datetime.now()-start
    print 'Got %d poems in %s'%(len(addresses),elapsed)

if __name__=="__main__":
    poetry_main()
