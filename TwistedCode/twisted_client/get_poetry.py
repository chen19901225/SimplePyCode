import optparse
import socket
from twisted.internet import reactor,main
import datetime
import errno
__author__ = 'cqh'

def parse_args():
    usage="""usage: %prog [options] [hostname]:port ...

This is the Get Poetry Now! client, Twisted version 1.0.
Run it like this:

  python get-poetry.py port1 port2 port3 ...

If you are in the base directory of the twisted-intro package,
you could run it like this:

  python twisted-client-1/get-poetry.py 10001 10002 10003

to grab poetry from servers on ports 10001, 10002, and 10003.

Of course, there need to be servers listening on those ports
for that to work."""
    paser=optparse.OptionParser()
    _,addresses=paser.parse_args()
    if not addresses:
        print paser.format_help()
    def parse_address(addr):
        if ':' not in addr:
            host,port='127.0.0.1',addr
        else:
            host,port=addr.split(':',1)

        if not port.isdigit():
            paser.error('port must be integers.')

        return host,int(port)
    return map(parse_address,addresses)

class PoetrySocket(object):
    poem=''
    def __init__(self,task_num,address):
        self.task_num=task_num
        self.address=address
        self.sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.sock.connect(self.address)
        self.sock.setblocking(0)

        reactor.addReader(self)

    def fileno(self):
        try:
            return self.sock.fileno()
        except socket.errno:
            return -1

    def connectionLost(self,reason):
        self.sock.close()

        reactor.removeReader(self)

        for reader in reactor.getReaders():
            if isinstance(reader,PoetrySocket):
                return
        reactor.stop()
    def doRead(self):
        bytes=''
        while True:
            try:
                bytes_read=self.sock.recv(1024)
                if not bytes_read:
                    break
                else:
                    bytes+=bytes_read
            except socket.error,e:
                if e.args[0]== errno.EWOULDBLOCK:
                    break
                return main.CONNECTION_LOST
        if not bytes:
            print 'Task %d finished'%self.task_num
            return main.CONNECTION_DONE
        else:
            msg='Task %d:got %d bytes of poetry from %s'
            print msg%(self.task_num,len(bytes),self.format_addr())

        self.poem+=bytes

    def logPrefix(self):
        return 'poetry'

    def format_addr(self):
        host,port=self.address

        return '%s:%s'%(host or '127.0.0.1',port)

def poetry_main():
    addresses=parse_args()

    start=datetime.datetime.now()
    sockets=[PoetrySocket(i+1,addr) for i,addr in enumerate(addresses)]

    reactor.run()

    elapsed=datetime.datetime.now()-start
    for i,sock in enumerate(sockets):
        print 'Task %d:%d bytes of poetry'%(i+1,len(sock.poem))

    print 'Got %d poems in %s'%(len(addresses),elapsed)

if __name__=="__main__":
    poetry_main()


