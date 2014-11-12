from twisted.application import service,internet
from twisted.application.service import Application
from twisted.internet.protocol import Protocol, ServerFactory
from twisted.plugin import IPlugin
from twisted.python import log,usage
from zope.interface import implements
import sys
import collections
from utils import update_option, getList, getIndexItem_Or_LastItem, get_childOrderDict

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

# listen_options=[
#     dict(port=8080,interface='localhost',poetry_file='poetry/ec.txt'),
#     dict(port=8000,interface='localhost',poetry_file='poetry/science.txt')
# ]
#
# top_service=service.MultiService()
#
# for tmp_option in listen_options:
#     poetry_service=PoetryService(tmp_option['poetry_file'])
#     poetry_service.setServiceParent(top_service)
#
#     factory=PoetryServerFactory(poetry_service)
#     tcp_service=internet.TCPServer(tmp_option['port'],factory,
#                                    interface=tmp_option['interface'])
#     tcp_service.setServiceParent(top_service)
#
# application=Application('fasterpoetry')
# top_service.setServiceParent(application)


class ExOptions(usage.Options):
    optParameters=[
        ['port','p',[8080],'port list to listen on '],
        ['poem',None,[],'poem file list'],
        ['iface',None,['localhost'],'The interface to listen on ']
    ]

def printDetail(in_options):
    for key,value in  in_options.iteritems():
        print >>sys.stdout,"key:%s,value:%s"%(key,value)




class PoetryServerMaker(object):
    implements(service.IServiceMaker,IPlugin)

    tapname='expoetry'
    description='excise poetry example'
    options=ExOptions

    def makeService(self,options):
        print options
        update_option(options,['port','iface','poem'],getList)
        #printDetail(options)
        local_options=get_childOrderDict(options,['port','iface','poem'])
        port_list,poem_file_list,iface_list=local_options.values()
        top_service=service.MultiService()
        service_num=max(map(len,local_options.values()))
        for start_no in xrange(service_num):
            #print start_no
            port,iface,poem_file=map(lambda x,y=start_no:getIndexItem_Or_LastItem(x,start_no),local_options.values())
            #port=int(port)
            #port,poem_file,iface=8080,'poetry/ec.txt','localhost'
            #print port,poem_file,iface
            poetry_service=PoetryService(poem_file)
            poetry_service.setServiceParent(top_service)

            factory=PoetryServerFactory(poetry_service)
            tcp_service=internet.TCPServer(port,factory,interface=iface)
            tcp_service.setServiceParent(top_service)

        return top_service




service_maker=PoetryServerMaker()




