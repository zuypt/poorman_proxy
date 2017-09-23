import BaseHTTPServer
import SocketServer
import threading
import logging
import select
import socket
import string
import random
import time
import ssl
import sys
import os


SSLcontext = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
SSLcontext.load_cert_chain('server.crt', 'server.key')
SSLcontext.verify_mode = ssl.CERT_NONE
SSLcontext.check_hostname = False

s = socket.socket()
s.bind(('172.16.42.195', 443))
s.listen(5)

c = s.accept()[0]
c = SSLcontext.wrap_socket(c, server_side = True)
print c.recv(1024)
print c.recv(1024)
print c.recv(1024)
print c.recv(1024)