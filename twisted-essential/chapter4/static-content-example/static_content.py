from twisted.internet import reactor
from twisted.web.server import Site
from twisted.web.static import File

__author__ = 'cqh'


resource=File('/var/www')
factory=Site(resource)
reactor.listenTCP(8080,factory)
reactor.run()