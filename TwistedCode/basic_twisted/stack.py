import traceback
from twisted.internet import reactor

__author__ = 'cqh'


def stack():
    print "The python stack:"
    traceback.print_stack()

if __name__=="__main__":
    reactor.callWhenRunning(stack)
    reactor.run()