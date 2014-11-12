from twisted.internet import defer

__author__ = 'cqh'


def got_results(res):
    print 'We got',res

print 'Empty List.'

d=defer.DeferredList([])
print 'Adding Callback.'
d.addCallback(got_results)