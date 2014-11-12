#coding:utf-8
from twisted.internet import reactor
from twisted.internet.protocol import Protocol, connectionDone, Factory, ServerFactory

__author__ = 'cqh'

class QuoteProtocol(Protocol):


    def connectionMade(self):
        self.factory.numConnection+=1

    def dataReceived(self, data):
        print "Number of active connections:%d"%(self.factory.numConnection,)
        print ">Received:'%s'\n>Sending:'%s'"%(data,self.getQuote())
        self.transport.write(self.getQuote())
        self.updateQuote(data)
        self.transport.loseConnection()

    def connectionLost(self, reason=connectionDone):
        self.factory.numConnection-=1
        print "After Lost:connectionCount",self.factory.numConnection

    def getQuote(self):
        return self.factory.quote

    def updateQuote(self,data):
        self.factory.quote=data

class QuoteFactory(ServerFactory):

    protocol = QuoteProtocol
    def __init__(self):
        self.numConnection=0
        self.quote= "An apple a kay keeps the doctor away"

reactor.listenTCP(8080,QuoteFactory())
reactor.run()

"""
运行有问题：
Number of active connections:3
>Received:'The early bird get the worm'
>Sending:'An apple a kay keeps the doctor away'
Number of active connections:3
>Received:'You snooze you lose'
>Sending:'The early bird get the worm'
Number of active connections:3
>Received:'Carpe diem'
>Sending:'You snooze you lose'
可以看到，连接数始终为3,而且客户端接收到的数据也有问题：
Recived quote: An apple a kay keeps the doctor away
connection lost: Connection was closed cleanly.
Recived quote: The early bird get the worm
Recived quote: You snooze you lose
connection lost: Connection was closed cleanly.
connection lost: Connection was closed cleanly.
可以看到只有一个客户端可以正常发送接收。
这就是说并发的时候有问题的。数据访问不是锁定的。

"""
