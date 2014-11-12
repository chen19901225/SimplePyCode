import defer
import optparse
import random
from twisted.internet import reactor
from twisted.internet.protocol import Protocol, connectionDone, ClientFactory
import sys


def parse_args():
    usage = """usage: %prog [options] [hostname]:port ...

This is the Get Poetry Now! client, Twisted version 5.0
Run it like this:

  python get-poetry.py port1 port2 port3 ...

If you are in the base directory of the twisted-intro package,
you could run it like this:

  python twisted-client-5/get-poetry.py 10001 10002 10003

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
        self.factory.poem_finished(poem)

class PoetryClientFactory(ClientFactory):
    protocol = PoetryProtocol
    def __init__(self,deferred):
        self.deferred=deferred

    def clientConnectionLost(self, connector, reason):
        if self.deferred is not None:
            d,self.deferred=self.deferred,None
            d.errback(reason)

    def poem_finished(self,poem):
        if self.deferred is not None:
            d,self.deferred=self.deferred,None
            d.callback(poem)

class GibberishError(Exception):pass

class CannotCummingsify(Exception):pass

def cumminsify(poem):
    def success():
        return poem.lower()

    def gibberish():
        raise GibberishError()
    def bug():
        raise CannotCummingsify(poem)

    return random.choice([success,gibberish,bug])()


def get_poetry(host,port):
    d=defer.Deferred()
    factory=PoetryClientFactory(d)
    reactor.connectTCP(host,port,factory)
    return d


def poetry_main():
    addresses=parse_args()

    poems,errors=[],[]

    def cummingsify_failed(err):
        if err.check(CannotCummingsify):
            print 'Cummingsify failed!'
            return err.value.args[0]
        return err
    def poem_got(poem):
        print 'poem',poem
        poems.append(poem)

    def poem_failed(err):

        print >>sys.stderr,'Poem Failed',err
        errors.append(err)
    def poem_done(_):
        if len(errors)+len(poems)==len(addresses):
            reactor.stop()
    for address in addresses:
        host,port=address
        d=get_poetry(host,port)
        d.add_callback(cumminsify)
        d.add_errback(cummingsify_failed)
        d.add_callbacks(poem_got,poem_failed)
        d.add_callbacks(poem_done,poem_done)
    reactor.run()
    print "Over"

if __name__=="__main__":
    poetry_main()
