import defer
from twisted.internet import reactor

__author__ = 'cqh'

class HeadlineRetriever(object):
    def processHeadline(self,headline):
        if len(headline)>50:
            self.d.errback("The Headline '%s' is too long "%(headline,))
        else:
            self.d.callback(headline)

    def _toHtml(self,result):
        return "<h1>%s</h1>"%(result,)

    def getHeadline(self,input):
        self.d=defer.Deferred()
        reactor.callLater(1,self.processHeadline,input)
        self.d.add_callback(self._toHtml)
        return self.d

def printData(result):
    print result
    reactor.stop()

def printError(failure):
    print failure
    reactor.stop()

h=HeadlineRetriever()
d=h.getHeadline("1234343424"*10)
d.add_callbacks(printData,printError)

reactor.run()