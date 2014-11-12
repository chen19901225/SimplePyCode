from twisted.internet import reactor
from twisted.internet.protocol import Protocol, ClientFactory

__author__ = 'cqh'

class EchoClientProtocol(Protocol):
    def connectionMade(self):
        self.transport.write("Hello,World")

    def dataReceived(self, data):
        print 'server_said',data
        self.transport.loseConnection()

class EchoClientFactory(ClientFactory):
    protocol = EchoClientProtocol

    def clientConnectionFailed(self, connector, reason):
        print "Connection failed"
        reactor.stop()

    def clientConnectionLost(self, connector, reason):
        print "Connection Lost"
        reactor.stop()

reactor.connectTCP("localhost",8080,EchoClientFactory())
reactor.run()
