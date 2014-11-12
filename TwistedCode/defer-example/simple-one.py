import os
from twisted.internet.defer import Deferred

__author__ = 'cqh'

def got_poem(res):
    print 'Your poem is served'
    print res

def  poem_failed(err):
    print 'No poetry for you'

d=Deferred()
d.addCallbacks(got_poem,poem_failed)
d.callback('This poem is short')

print 'Finished'