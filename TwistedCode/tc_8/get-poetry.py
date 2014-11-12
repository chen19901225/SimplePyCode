
import optparse
from twisted.internet import defer
from twisted.internet import reactor
from twisted.internet.defer import DeferredList
from twisted.internet.protocol import Protocol, connectionDone, ClientFactory
from twisted.protocols.basic import NetstringReceiver
import sys

__author__ = 'cqh'

def parse_args():
    usage = """usage: %prog [options] [hostname]:port ...

This is the Get Poetry Now! client, Twisted version 8.0
Run it like this:

  python get-poetry.py xform-port port1 port2 ...

If you are in the base directory of the twisted-intro package,
you could run it like this:

  python twisted-client-6/get-poetry.py 10001 10002 10003

to grab poetry from servers on ports 10002, and 10003 and transform
it using the server on port 10001.

Of course, there need to be appropriate servers listening on those
ports for that to work.
"""

    parser = optparse.OptionParser(usage)

    _, addresses = parser.parse_args()

    if len(addresses) < 2:
        print parser.format_help()
        parser.exit()

    def parse_address(addr):
        if ':' not in addr:
            host = '127.0.0.1'
            port = addr
        else:
            host, port = addr.split(':', 1)

        if not port.isdigit():
            parser.error('Ports must be integers.')

        return host, int(port)

    return map(parse_address, addresses)

class PoetryClientProtocol(Protocol):
    poem=''

    def dataReceived(self, data):
        self.poem+=data

    def connectionLost(self, reason=connectionDone):
        self.poemReceived(self.poem)

    def poemReceived(self,poem):
        self.factory.poem_finished(poem)

class PoetryClientFactory(ClientFactory):

    protocol= PoetryClientProtocol

    def __init__(self,deferred):
        self.deferred=deferred

    def poem_finished(self,poem):
        if self.deferred  is not None:
            d,self.deferred=self.deferred,None
            d.callback(poem)

    def clientConnectionFailed(self, connector, reason):
        if self.deferred is not None:
            d,self.deferred=self.deferred,None
            d.errback(reason)


class TransformClientProtocol(NetstringReceiver):

    def connectionMade(self):
        self.sendRequest(self.factory.xform_name,self.factory.poem)

    def sendRequest(self,xform_name,poem):
        self.sendString(xform_name+'.'+poem)

    def stringReceived(self, recv_str):
        self.transport.loseConnection()
        self.poemReceived(recv_str)

    def poemReceived(self,poem):
        self.factory.handlePoem(poem)

class TransformClientFactory(ClientFactory):

    protocol =  TransformClientProtocol
    def __init__(self,xform_name,poem):
        self.xform_name=xform_name
        self.poem=poem
        self.deferred=defer.Deferred()

    def handlePoem(self,poem):
        d,self.deferred=self.deferred,None
        d.callback(poem)

    def clientConnectionLost(self, _, reason):
        if self.deferred is not None:
            d,self.deferred=self.deferred,None
            d.errback(reason)
    clientConnectionFailed=clientConnectionLost


class TransformProxy(object):
    def __init__(self,host,port):
        self.host=host
        self.port=port

    def xform(self,xform_name,poem):
        factory=TransformClientFactory(xform_name,poem)
        reactor.connectTCP(self.host,self.port,factory)
        return factory.deferred

def get_poetry(host,port):
    d=defer.Deferred()
    factory=PoetryClientFactory(d)
    reactor.connectTCP(host,port,factory)
    return d

def poetry_main():
    addresses=parse_args()

    xform_addr=addresses.pop(0)

    proxy=TransformProxy(*xform_addr)

    ds=[]
    poem_list=[]

    @defer.inlineCallbacks
    def get_transformed_poem(host,port):
        try:
            poem=yield get_poetry(host,port)

        except Exception,e:
            print >>sys.stderr,'the poem downalod failed :',e
            raise

        try:
            #print proxy.host,proxy.port
            #print poem
            poem=yield proxy.xform('cummingsify',poem)
            #print poem
        except Exception:
            print >>sys.stderr,'Cummingsify failed'

        defer.returnValue(poem)

    def got_poem(poem):

        poem_list.append(poem)
        if len(poem_list)==len(addresses):
            for tmp_poem in poem_list:
                print tmp_poem
        #print poem



    for (host,port) in addresses:
        d=get_transformed_poem(host,port)
        d.addCallback(got_poem)
        ds.append(d)
    dlist=defer.DeferredList(ds,consumeErrors=True)
    dlist.addCallback(lambda res:reactor.stop())

    reactor.run()

if __name__=="__main__":
    poetry_main()
