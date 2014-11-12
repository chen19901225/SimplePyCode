import defer
import optparse
from twisted.internet import reactor
from twisted.internet.protocol import Protocol, connectionDone, ClientFactory
import sys

__author__ = 'cqh'

def parse_args():
    usage = """usage: %prog [options] [hostname]:port ...

This is the Get Poetry Now! client, Twisted version 3.0
Run it like this:

  python get-poetry-1.py port1 port2 port3 ...

If you are in the base directory of the twisted-intro package,
you could run it like this:

  python twisted-client-3/get-poetry-1.py 10001 10002 10003

to grab poetry from servers on ports 10001, 10002, and 10003.

Of course, there need to be servers listening on those ports
for that to work.
"""

    parser = optparse.OptionParser(usage)

    _, addresses = parser.parse_args()

    if not addresses:
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

class PoetryProtocol(Protocol):
    poem=''

    def dataReceived(self, data):
        self.poem+=data

    def connectionLost(self, reason=connectionDone):
        self.poemReceived(self.poem)

    def poemReceived(self,poem):
        self.factory.finish_poem(poem)


class PoetryClientFactory(ClientFactory):

    protocol = PoetryProtocol
    def __init__(self,deferred):
        self.deferred=deferred

    def clientConnectionFailed(self, connector, reason):
        if self.deferred is not None:
            d,self.deferred=self.deferred,None
            d.errback(reason)
        #self.errback(reason)

    def finish_poem(self,poem):
        if self.deferred is not None:
            d,self.deferred=self.deferred,None
            d.callback(poem)
        #self.callback(poem)


def get_poetry(host,port):
    d=defer.Deferred()
    factory=PoetryClientFactory(d)
    reactor.connectTCP(host,port,factory)
    return d


def poetry_main():
    addresses=parse_args()
    poems=[]
    errors=[]
    def get_done(_):
        if len(poems)+len(errors)==len(addresses):
            reactor.stop()
    def got_poetry(poem):
        poems.append(poem)
        #get_done()
    def got_poetry_err(err):
        print >>sys.stderr,'Poetry Failed',err
        errors.append(err)
        #get_done()

    for address in addresses:
        host,port=address
        d=get_poetry(host,port)
        d.add_callbacks(got_poetry,got_poetry_err)
        #d.addBoth(get_done)
        d.add_callbacks(get_done,get_done)
    reactor.run()

    for poem in poems:
        print poem
    print "Over"

if __name__=="__main__":
    poetry_main()


