#coding:utf-8
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks, Deferred

__author__ = 'cqh'

@inlineCallbacks
def my_callbacks():
    """
    有些疑问:
    第一。我好像没有看到my_callbacks被调用过啊。。在调试过程中。
    :return:
    """

    print 'first callback'
    result=yield 1

    print 'second callback got',result

    d=Deferred()
    reactor.callLater(5,d.callback,2)
    result=yield d

    print 'third callback got',result

    d=Deferred()
    reactor.callLater(5,d.errback,Exception(3))
    try:
        yield d
    except Exception,e:
        result=e

    print 'fourth callback got',repr(result)
    reactor.stop()

reactor.callWhenRunning(my_callbacks)
reactor.run()

