from twisted.internet import reactor
from twisted.web.resource import Resource
import time
from twisted.web.server import Site

__author__ = 'cqh'

class BusyPage(Resource):
    isLeaf = True

    def render_GET(self, request):
        time.sleep(5)
        return "Finally done at %s"%(time.asctime(),)

factory=Site(BusyPage())
reactor.listenTCP(8080,factory)
reactor.run()
