from defer import Deferred

__author__ = 'cqh'

def myCallback(result):
    print result

def myErrback(err):
    print err
d=Deferred()
d.add_callback(myCallback)
#d.add_errback(myErrback)
d.callback("Trigger callback.")