from twisted.internet import reactor
from twisted.internet.protocol import Protocol, ServerFactory

__author__ = 'cqh'

class EchoServerProtocol(Protocol):
    def dataReceived(self, data):
        print "Server_receive:",data
        self.transport.write(data)

class EchoServerFactory(ServerFactory):
    protocol = EchoServerProtocol

reactor.listenTCP(8080,EchoServerFactory())
reactor.run()
