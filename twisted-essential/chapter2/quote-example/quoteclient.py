from twisted.internet import reactor
from twisted.internet.protocol import Protocol, ClientFactory

__author__ = 'cqh'

class QuoteClientProtocol(Protocol):

    def connectionMade(self):
        self.sendQuote()

    def sendQuote(self):
        self.transport.write(self.factory.quote)

    def dataReceived(self, data):
        print "Recived quote:",data
        self.transport.loseConnection()

class QuoteClientFactory(ClientFactory):
    protocol = QuoteClientProtocol
    def __init__(self,quote):
        self.quote=quote

    def clientConnectionFailed(self, connector, reason):
        print 'connection failed:',reason.getErrorMessage()
        maybeStopReactor()

    def clientConnectionLost(self, connector, reason):
        print 'connection lost:',reason.getErrorMessage()
        maybeStopReactor()

def maybeStopReactor():
    global quote_counter
    quote_counter-=1
    if not quote_counter:
        reactor.stop()

quotes=["You snooze you lose",
        "The early bird get the worm",
        "Carpe diem"]
quote_counter=len(quotes)
for quote in quotes:
    reactor.connectTCP('localhost',8080,QuoteClientFactory(quote))
reactor.run()

