from twisted.internet import reactor

__author__ = 'cqh'
class Countdown(object):
    counter=5
    def count(self):
        if self.counter==0:
            reactor.stop()
        else:
            print self.counter,'...'
            self.counter-=1
            reactor.callLater(1,self.count)


if __name__=="__main__":
    reactor.callWhenRunning(Countdown().count)
    print "start !"
    reactor.run()
    print "Stop!"