from twisted.internet import reactor
from twisted.internet.protocol import ServerFactory

__author__ = 'cqh'

from twisted.protocols import basic
class HttpEchoProcotol(basic.LineReceiver):
    def __init__(self):
        self.lines=[]

    def lineReceived(self, line):
        self.lines.append(line)
        if not line:
            self.sendResponse()

    def sendResponse(self):
        self.sendLine("Http/1.1 200 OK")
        self.sendLine("")
        responseBody="You said:\r\n\r\n"+"\r\n".join(self.lines)
        self.transport.write(responseBody)
        self.transport.loseConnection()

class HttpEchoFactory(ServerFactory):
    def buildProtocol(self, addr):
        return HttpEchoProcotol()

reactor.listenTCP(8080,HttpEchoFactory())
reactor.run()
