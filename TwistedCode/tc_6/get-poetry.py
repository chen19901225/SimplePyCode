#coding:utf-8
import defer
import optparse
from twisted.internet import reactor
from twisted.internet.protocol import Protocol, connectionDone, ClientFactory
from twisted.protocols.basic import NetstringReceiver
import sys

__author__ = 'cqh'
def parse_args():
    usage = """usage: %prog [options] [hostname]:port ...

This is the Get Poetry Now! client, Twisted version 5.0
Run it like this:

  python get-poetry.py port1 port2 port3 ...

If you are in the base directory of the twisted-intro package,
you could run it like this:

  python twisted-client-5/get-poetry.py 10001 10002 10003

to grab poetry from servers on ports 10001, 10002, and 10003.

Of course, there need to be servers listening on those ports
for that to work.
"""
    parser=optparse.OptionParser()
    _,addresses=parser.parse_args()
    if not addresses:
        print parser.format_help()
        parser.exit()
    def parse_address(address):
        if ':' not in address:
            host,port='127.0.0.1',address
        else:
            host,port=address.split(':',1)
        assert port.isdigit()==True,"port必须为整形"
        return host,int(port)
    return map(parse_address,addresses)

class PoetryProtocol(Protocol):
    poem=''
    def dataReceived(self, data):
        self.poem+=data

    def connectionLost(self, reason=connectionDone):
        self.poemReceived(self.poem)
    def poemReceived(self,poem):
        self.factory.poem_finished(poem)

class PoetryClientFactory(ClientFactory):
    protocol = PoetryProtocol
    def __init__(self,deferred):
        self.deferred=deferred

    def poem_finished(self,poem):
        if self.deferred is not None:
            d,self.deferred=self.deferred,None
            d.callback(poem)

    def clientConnectionFailed(self, connector, reason):
        if self.deferred is not None:
            d,self.deferred=self.deferred,None
            d.errback(reason)




class TransformClientProtocol(NetstringReceiver):

    def connectionMade(self):
        self.sendRequest(self.factory.xform_name,self.factory.poem)

    def sendRequest(self,xform_name,poem):
        self.sendString(xform_name+'.'+poem)


    def stringReceived(self, s):
        self.transport.loseConnection()
        self.poemReceived(s)

    def poemReceived(self,poem):
        self.factory.handlePoem(poem)

class TransformClientFactory(ClientFactory):
    protocol = TransformClientProtocol
    def __init__(self,xform_name,poem):
        self.xform_name=xform_name
        self.poem=poem
        self.deferred=defer.Deferred()

    def handlePoem(self,poem):
        d,self.deferred=self.deferred,None
        d.callback(poem)

    def  clientConnectionLost(self, _, reason):
        if self.deferred is not None:
            d,self.deferred=self.deferred,None
            #print reason
            d.errback(reason)

    clientConnectionFailed=clientConnectionLost

class TransformProxy(object):
    def __init__(self,host,port):
        self.host,self.port=host,port

    def xform(self,xform_name,poem):
        factory=TransformClientFactory(xform_name,poem)
        reactor.connectTCP(self.host,self.port,factory)
        return factory.deferred

def get_poetry(host,port):
    #print host,port
    d=defer.Deferred()
    factory=PoetryClientFactory(d)
    reactor.connectTCP(host,port,factory)
    return d

def poetry_main():
    addresses=parse_args()
    xform_addr=addresses.pop(0)

    proxy=TransformProxy(*xform_addr)
    poems,errors=[],[]

    def try_to_cummingsify(poem):
        local_d=proxy.xform('cummingsify',poem)
        def fail(err):
            print >>sys.stderr,'Cummingsify failed',err
            return poem
        local_d.add_errback(fail)
        return local_d
        return local_d.add_errback(fail)
    def got_poem(poem):
        print poem
        poems.append(poem)
    def poem_failed(err):
        print >>sys.stderr,'The poem download failed',err
        errors.append(err)

    def poem_done(_):
        if len(poems)+len(errors)==len(addresses):
            reactor.stop()

    for address in addresses:
        host,port =address
        d=get_poetry(host,port)
        d.add_callback(try_to_cummingsify)//为什么这个要放在第一位？为什么我觉得不应该放在第一位。
        d.add_callbacks(got_poem,poem_failed)
        d.add_callbacks(poem_done,poem_done)

    reactor.run()

if __name__=="__main__":
    poetry_main()



    


