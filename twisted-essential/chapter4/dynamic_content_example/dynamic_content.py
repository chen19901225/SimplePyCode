from twisted.internet import reactor
from twisted.web.resource import Resource
import time
from twisted.web.server import Site

__author__ = 'cqh'

class ClockPage(Resource):
    isLeaf=True

    def render(self, request):
        return "The local time is %s"%(time.ctime(),)

resource=ClockPage()
factory=Site(resource)
reactor.listenTCP(8080,factory)
reactor.run()