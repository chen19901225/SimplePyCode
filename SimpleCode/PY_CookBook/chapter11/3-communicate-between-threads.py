from Queue import Queue
from threading import Thread

def producer(out_q):
    n=0
    while True:
        n+=1
        print "Produce some data"
        out_q.put('The data %s .'%n)

def consumer(in_q):
    while True:
        data=in_q.get()
        print "We received data: ",data

q=Queue()
consumer_thread=Thread(target=consumer,args=(q,))
producer_thread=Thread(target=producer,args=(q,))
consumer_thread.start()
producer_thread.start()
