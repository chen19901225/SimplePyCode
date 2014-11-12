import optparse
import os
from twisted.internet import reactor
from twisted.internet.protocol import ServerFactory
from twisted.protocols.basic import NetstringReceiver


def parse_args():
    usage = """usage: %prog [options]

This is the Poetry Transform Server.
Run it like this:

  python transformedpoetry.py

If you are in the base directory of the twisted-intro package,
you could run it like this:

  python twisted-server-1/transformedpoetry.py --port 11000

to provide poetry transformation on port 11000.
"""

    parser = optparse.OptionParser(usage)

    help = "The port to listen on. Default to a random available port."
    parser.add_option('--port', type='int', help=help)

    help = "The interface to listen on. Default is localhost."
    parser.add_option('--iface', help=help, default='localhost')

    options, args = parser.parse_args()

    if len(args) != 0:
        parser.error('Bad arguments.')

    return options

class TransformService(object):
    def cummingsify(self,poem):
        return poem.lower()

class TranformProtocol(NetstringReceiver):
    def is_badRequest(self,request):
        return '.' not in request
    def handler_goodRequest(self,request):
        xform_name,poem=request.split('.',1)
        self.xformRequestReceived(xform_name,poem)
    def stringReceived(self, request):
        if self.is_badRequest(request):
            self.transport.loseConnection()
            return
        else:
            self.handler_goodRequest(request)

    def xformRequestReceived(self,xform_name,poem):
        new_poem=self.factory.transform(xform_name,poem)
        if new_poem is not None:
            self.sendString(new_poem)
        self.transport.loseConnection()

class TransformServerFactory(ServerFactory):
    protocol = TranformProtocol
    def __init__(self,service):
        self.service=service

    def transform(self,xform_name,poem):
        thunk=getattr(self,'xform_%s'%(xform_name,),None)
        if not  thunk:
            return None
        try:
            return thunk(poem)
        except:
            return None
    def xform_cummingsify(self,poem):
        return self.service.cummingsify(poem)

def main():
    options=parse_args()

    service=TransformService()
    factory=TransformServerFactory(service)
    port=reactor.listenTCP(options.port or 0,factory,
                           interface=options.iface)
    print 'Serving transforms on %s'%(port.getHost(),)
    reactor.run()

if __name__=="__main__":
    main()
