from twisted.application import service,internet
from twisted.application.service import Application
from twisted.internet.protocol import Protocol, ServerFactory
from twisted.python import log

__author__ = 'cqh'

class PoetryServerProtocol(Protocol):

    def connectionMade(self):
        poem=self.factory.service.poem
        log.msg("send %d bytes to %s"%(len(poem),self.transport.getPeer()))
        self.transport.write(poem)
        self.transport.loseConnection()

class PoetryServerFactory(ServerFactory):
    protocol = PoetryServerProtocol
    def __init__(self,service):
        self.service=service

class PoetryService(service.Service):

    def __init__(self,poetry_file):
        self.poetry_file=poetry_file

    def startService(self):
        service.Service.startService(self)
        self.poem=open(self.poetry_file).read()
        log.msg("load poetry from %s"%(self.poetry_file,))


# port=8080
# interface='localhost'
# poetry_file='poetry/ec.txt'
#
# port2=8000
# poetry_file2='poetry/science.txt'

listen_options=[
    dict(port=8080,interface='localhost',poetry_file='poetry/ec.txt'),
    dict(port=8000,interface='localhost',poetry_file='poetry/science.txt')
]

top_service=service.MultiService()

for tmp_option in listen_options:
    poetry_service=PoetryService(tmp_option['poetry_file'])
    poetry_service.setServiceParent(top_service)

    factory=PoetryServerFactory(poetry_service)
    tcp_service=internet.TCPServer(tmp_option['port'],factory,
                                   interface=tmp_option['interface'])
    tcp_service.setServiceParent(top_service)

application=Application('fasterpoetry')
top_service.setServiceParent(application)




