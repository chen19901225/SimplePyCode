from collections import Iterable

from Queue import Queue
from threading import Thread,Event

class ActorExit(Exception):
    pass

class Actor(object):
    def __init__(self):
        self._mailbox=Queue()


    def send(self,msg):
        self._mailbox.put(msg)


    def recv(self):
        msg=self._mailbox.get()
        if msg is ActorExit:
            raise ActorExit()
        return msg

    def close(self):
        self.send(ActorExit)


    def start(self):
        self._terminated=Event()
        t=Thread(target=self._bootstrap)
        t.daemon=True
        t.start()

    def _bootstrap(self):
        try:
            self.run()
        except ActorExit:
            pass
        finally:
            self._terminated.set()

    def join(self):
        self._terminated.set()

    def run(self):
        while True:
            msg=self.recv()



class PrintActor(Actor):
    def run(self):
        while 1:
            msg=self.recv()
            print "Got:",msg

class TaggedActor(Actor):
    def run(self):
        while 1:
            tag, payload=self.recv()
            if not isinstance(payload,Iterable):
                payload=(payload,)
            getattr(self,'do_'+tag)(*payload)

    def do_A(self,x):
        print 'Running A',x

    def do_B(self,x,y):
        print 'Running B',x,y


#p=PrintActor()
#p.start()
#p.send('Hello')
#p.send('world')
#p.close()
#p.join()

a=TaggedActor()
a.start()
a.send(('A',1))
a.send(('B',2,3))
a.join()
a.close()
