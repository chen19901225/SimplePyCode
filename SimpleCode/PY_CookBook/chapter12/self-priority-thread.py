import heapq
import threading

class PriorityQueue(object):
    def __init__(self):
        self._queue=[]
        self._count=0
        self._cv=threading.Condition()

    def put(self,item,priority=1):
        with self._cv:
            heapq.heappush(self._queue,(-priority,self._count,item))
            self._count+=1
            self._cv.notify()

    def get(self):
        with self._cv:
            while len(self._queue)==0:
                self._cv.wait()
            return heapq.heappop(self._queue)[-1]


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

q=PriorityQueue()
consumer_thread= threading.Thread(target=consumer,args=(q,))
producer_thread= threading.Thread(target=producer,args=(q,))
consumer_thread.start()
producer_thread.start()