
from twisted.application import service,internet
from twisted.application.service import Service
from twisted.internet.protocol import Protocol, ServerFactory
from twisted.python import log

__author__ = 'cqh'

class PoetryServerProtocol(Protocol):

    def connectionMade(self):
        poem=self.factory.service.poem
        log.msg('sending %d bytes of poetry to %s'%(len(poem),self.transport.getPeer()))
        self.transport.write(poem)
        self.transport.loseConnection()


class PoetryServerFactory(ServerFactory):
    protocol = PoetryServerProtocol

    def __init__(self,service):
        self.service=service


class PoetryServerService(Service):
    def __init__(self,poetry_file):
        self.poetry_file=poetry_file

    def startService(self):
        Service.startService(self)
        self.poem=open(self.poetry_file).read()
        log.msg('loaded a poem from :%s'%(self.poetry_file,))


port=10000
iface='localhost'
poetry_file='poetry/ec.txt'


top_service=service.MultiService()

poetry_service=PoetryServerService(poetry_file)
poetry_service.setServiceParent(top_service)

factory=PoetryServerFactory(poetry_service)
tcp_service=internet.TCPServer(port,factory,interface=iface)
tcp_service.setServiceParent(top_service)

application=service.Application('fastpoetry')

top_service.setServiceParent(application)
