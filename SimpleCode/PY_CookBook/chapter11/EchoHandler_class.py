from SocketServer import BaseRequestHandler,TCPServer

class EchoHandler(BaseRequestHandler):


    def handle(self):
        print "Got connection from",self.client_address

        while True:
            msg=self.request.recv(1024)
            print "recv:",msg
            if not msg:
                break
            self.request.send(msg)

if __name__=="__main__":
    print "Hello main"
    server=TCPServer(('',20000),EchoHandler)
    server.serve_forever()

