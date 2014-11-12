import defer
import optparse
from twisted.internet import reactor
from twisted.internet.protocol import Protocol, connectionDone, ClientFactory
from twisted.protocols.basic import NetstringReceiver
import sys

__author__ = 'cqh'

def parse_args():
    usage = """usage: %prog [options] [hostname]:port ...

This is the Get Poetry Now! client, Twisted version 7.0
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
        self.factory.poem_finished(self.poem)

class PoetryClientFactory(ClientFactory):
    protocol = PoetryClientProtocol

    def __init__(self,deferred):
        self.deferred=deferred

    def poem_finished(self,poem):
        if self.deferred is not None:
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

    def stringReceived(self, recv_s):
        self.transport.loseConnection()
        self.poemReceived(recv_s)

    def poemReceived(self,poem):
        self.factory.handPoem(poem)

class TransformClientFactory(ClientFactory):

    protocol=TransformClientProtocol

    def __init__(self,xform_name,poem):
        self.xform_name=xform_name
        self.poem=poem
        self.deferred=defer.Deferred()

    def handPoem(self,poem):
        d,self.deferred=self.deferred,None
        d.callback(poem)

    def clientConnectionLost(self, _, reason):
        if self.deferred is not None:
            d,self.deferred=self.deferred,None
            d.errback(reason)

class TransformProxy(object):
    def __init__(self,host,port):
        self.host,self.port=host,port

    def xform(self,xform_name,poem):
        factory=TransformClientFactory(xform_name,poem)
        reactor.connectTCP(self.host,self.port,factory)
        return factory.deferred


def get_poetry(host,port):
    d=defer.Deferred()
    factory=PoetryClientFactory(d)
    reactor.connectTCP(host,port,factory)
    return d

def poem_main():
    addresses=parse_args()

    xform_addr=addresses.pop(0)
    proxy=TransformProxy(*xform_addr)

    results=[]
    @defer.inline_callbacks
    def get_transformed_poem(host,port):
        try:
            poem=yield get_poetry(host,port)
        except Exception,e:
            print >>sys.stderr,'The poem download failed',e
            raise

        try:
            poem=yield proxy.xform('cummingsify',poem)
        except Exception:
            print >>sys.stderr,'Cummingsify failed'
            raise

        defer.return_value(poem)

    def got_poem(poem):
        print poem

    def poem_done(_):
        results.append(_)
        if len(results)==len(addresses):
            reactor.stop()

    for address in addresses:
        host,port=address
        d=get_transformed_poem(host,port)
        d.add_callback(got_poem)
        d.add_callbacks(poem_done,poem_done)

    reactor.run()

if __name__=="__main__":
    poem_main()

