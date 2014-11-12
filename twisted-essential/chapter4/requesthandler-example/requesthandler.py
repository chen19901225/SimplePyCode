from twisted.internet import reactor
from twisted.web import http
from twisted.web.http import Request

__author__ = 'cqh'

class MyRequestHandler(Request):
    resources={
        '/':'<h1>Home</h1>Home page',
        '/about':'<h1>About</h1> All About me'
    }

    def process(self):
        self.setHeader('Content-Type','text/html')

        if self.resources.has_key(self.path):
            self.write(self.resources[self.path])
        else:
            self.setResponseCode(http.NOT_FOUND)
            self.write('<h1>Not Found</h1> Sorry,no such resource.')
        self.finish()
class MyHttp(http.HTTPChannel):
    requestFactory = MyRequestHandler

class MyHttpFactory(http.HTTPFactory):
    def buildProtocol(self, addr):
        return MyHttp()

reactor.listenTCP(8080,MyHttpFactory())
reactor.run()
