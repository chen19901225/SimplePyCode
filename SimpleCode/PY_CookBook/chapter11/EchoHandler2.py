from SocketServer import StreamRequestHandler, TCPServer


import socket

class EchoHandler(StreamRequestHandler):
    timeout=5
    rbufsize = -1
    wbufsize = 0
    disable_nagle_algorithm = False
    def handle(self):
        print "Got connectionfrom",self.connection
        try:
            for line in self.rfile:
                self.wfile.write(line)
        except socket.timeout:
            print "Time out!"

if __name__=="__main__":
    server=TCPServer(('',20000),EchoHandler)
    server.serve_forever()