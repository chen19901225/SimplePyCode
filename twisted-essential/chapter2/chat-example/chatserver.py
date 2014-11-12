from twisted.internet import reactor
from twisted.internet.protocol import ServerFactory
from twisted.protocols.basic import LineReceiver

__author__ = 'cqh'

class ChatServerProtocol(LineReceiver):
    def __init__(self,factory):
        self.factory=factory
        self.name=None
        self.state="register"

    def connectionMade(self):
        self.sendLine("What's your name?")

    def connectionLost(self,reason):
        if self.name in self.factory.users:
            del self.factory.users[self.name]
            self.broadcastMessage("%s has left the chatroom"%self.name)

    def lineReceived(self, line):
        handle_name="handle_%s"%self.state
        if hasattr(self,handle_name):
            handle_func=getattr(self,handle_name)
        handle_func(line)
        # if self.state=='register':
        #     self.handle_register(line)
        # else:
        #     self.handle_chat(line)

    def handle_register(self,name):
        if name in self.factory.users:
            self.sendLine("Name taken,please choose  another")
            return
        self.sendLine("Welcome,%s"%(name,))
        self.broadcastMessage("%s has joined the channel."%(name,))
        self.name=name
        self.factory.users[name]=self
        self.state="chat"

    def handle_chat(self,message):
        message="<%s> %s"%(self.name,message)
        self.broadcastMessage(message)

    def broadcastMessage(self,line):
        for name , protocol in self.factory.users.iteritems():
            if protocol!=self:
                protocol.sendLine(line)


class ChatServerFactory(ServerFactory):
    def __init__(self):
        self.users={}

    def buildProtocol(self, addr):
        return ChatServerProtocol(self)


reactor.listenTCP(8080,ChatServerFactory())
reactor.run()

