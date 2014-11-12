
from socket import socket,AF_INET,SOCK_STREAM

print "Go"
s=socket(AF_INET,SOCK_STREAM)
s.connect(('localhost',20000))
print s.send('Hellow world')

print s.recv(1024)