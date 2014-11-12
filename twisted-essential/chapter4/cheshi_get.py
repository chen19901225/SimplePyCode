from multiprocessing.pool import Pool
from twisted.internet import reactor
from twisted.internet.protocol import Protocol, ClientFactory, connectionDone
import urllib


__author__ = 'cqh'

def print_url_content(param_url):
    print  urllib.urlopen(param_url).read()




url_list=["http://localhost:8080"]*4
pool=Pool(4)
pool.map(print_url_content,url_list)
pool.close()
pool.join()
print "Over"

