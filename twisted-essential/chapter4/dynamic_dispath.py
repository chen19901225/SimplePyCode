from twisted.internet import reactor
from twisted.web.resource import Resource, NoResource
from calendar import calendar
from twisted.web.server import Site
from twisted.web.util import redirectTo
import datetime

__author__ = 'cqh'
class YearPage(Resource):
    def __init__(self,year):
        Resource.__init__(self)
        self.year=year

    def render(self, request):
        return """<html>
        <body>
             <pre>
                %s
             </pre>
        </body>
        </html>"""%(calendar(self.year),)


class CalendarHome(Resource):
    def getChild(self,name,request):
        if name=='':
            return self
        if name.isdigit():
            return YearPage(int(name))
        else:
            return NoResource()

    def render(self, request):
        return redirectTo(datetime.datetime.now().year,request)

root=CalendarHome()
factory=Site(root)
reactor.listenTCP(8080,factory)
reactor.run()
