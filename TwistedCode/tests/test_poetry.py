from twisted.internet import reactor
from twisted.internet.defer import Deferred
from twisted.internet.protocol import Protocol, ServerFactory, connectionDone, ClientFactory
from twisted.trial._asynctest import TestCase
from twisted.internet.error import   ConnectError
__author__ = 'cqh'


class PoetryServerProtocol(Protocol):
    def  connectionMade(self):
        self.transport.write(self.factory.poem)
        self.transport.loseConnection()

class PoetryServerFactory(ServerFactory):
    protocol = PoetryServerProtocol

    def __init__(self,poem):
        self.poem=poem

class PoetryClientProtocol(Protocol):
    poem=''

    def dataReceived(self, data):
        self.poem+=data

    def connectionLost(self, reason=connectionDone):
        self.poemReceived(self.poem)

    def poemReceived(self,poem):
        self.factory.poem_finished(poem)
class PoetryClientFactory(ClientFactory):
    protocol = PoetryClientProtocol

    def __init__(self):
        self.deferred=Deferred()

    def poem_finished(self,poem):
        if self.deferred is not None:
            d,self.deferred=self.deferred,None
            d.callback(poem)

    def clientConnectionFailed(self, connector, reason):
        if not self.deferred:
            pass
        else:
            d,self.deferred=self.deferred,None
            d.errback(reason)

def get_poetry(host,port):
    factory=PoetryClientFactory()
    reactor.connectTCP(host,port,factory)
    return factory.deferred

test_poem="""\
This is a test.
This is only a test."""

class PoetryTestCase(TestCase):
    def setUp(self):
        factory=PoetryServerFactory(test_poem)
        self.port=reactor.listenTCP(0,factory,interface="127.0.0.1")
        self.portnum=self.port.getHost().port

    def tearDown(self):
        port,self.port=self.port,None
        return port.stopListening()

    def test_client(self):
        d=get_poetry('127.0.0.1',self.portnum)

        def got_poem(poem):
            self.assertEquals(poem,test_poem)

        d.addCallback(got_poem)
        return d

    def test_failure(self,):
        d=get_poetry('127.0.0.1',0)
        return self.assertFailure(d,ConnectError)

