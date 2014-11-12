
from zope.interface import implements
from twisted.python import log
from twisted.python import usage
from twisted.internet.protocol import Protocol, ServerFactory
from twisted.plugin import IPlugin

from twisted.application import service,internet




__author__ = 'cqh'

class PoetryServerProtocol(Protocol):

    def connectionMade(self):
        poem=self.factory.service.poem
        log.msg('sending %d bytes of poetry to %s'%(len(poem),self.factory.getPeer()))

        self.transport.write(poem)
        self.transport.loseConnection()


class PoetryServerFactory(ServerFactory):

    protocol = PoetryServerProtocol

    def __init__(self,service):
        self.service=service

class PoetryServerService(service.Service):

    def __init__(self,poetry_file):
        self.poetry_file=poetry_file

    def startService(self):
        service.Service.startService(self)
        self.poem=open(self.poetry_file).read()
        log.msg('loaded a poem from %s'%(self.poetry_file,))

class PoetryOptions(usage.Options):
    optParameters=[
        ['port','p',10000,'The port number to  listen on.'],
        ['poem',None,None,'the file containing the poem'],
        ['iface',None,'localhost','The interface to listen on.']
    ]

class PoetryServiceMaker(object):

    implements(service.IServiceMaker,IPlugin)

    tapname="fastpoetry"
    description="A fast poetry service"
    options=PoetryOptions

    def makeService(self,options):
        top_service=service.MultiService()

        poetry_service=PoetryServerService(options['poem'])
        poetry_service.setServiceParent(top_service)

        factory=PoetryServerFactory(poetry_service)
        tcp_service=internet.TCPServer(int(options['port']),factory,
                                       interface=options['iface'])

        tcp_service.setServiceParent(top_service)

        return top_service


service_maker=PoetryServiceMaker()


