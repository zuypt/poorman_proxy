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

logging.getLogger().setLevel(logging.DEBUG)
sleep_interval = 0.3
READ_SIZE = 10240

'''This class stand betwwen client_socket and real_server_socket passing data to\from them'''
'''This class dertermine wether to intercept the data or just pass it to remote server'''
class FORWARDER():
    def __init__(self, client_socket, real_server_socket, request_filter_func = None, response_filter_func = None):
        if isinstance(client_socket, socket.socket) and isinstance(real_server_socket, socket.socket):
            self.__isSSL = False
        elif isinstance(client_socket, ssl.SSLSocket) and isinstance(real_server_socket, ssl.SSLSocket):
            self.__isSSL = True
        else:
            logging.critical("Mismatch protocol between client and REAL_SERVER => shit happened => how the fuck do I get here ?")
            return None
        
        self.__client_socket = client_socket
        self.__real_server_socket = real_server_socket
        self.__request_filter_func = request_filter_func
        self.__response_filter_func = response_filter_func
        
    def forward_forever(self):
        self.loop()
        
    def loop(self):
        socket_list = [self.__client_socket, self.__real_server_socket]
        request_data = ''
        response_data = ''

        '''do all the hard work here'''
        '''select doesn't work with SSL socket fuck !!!'''
        while True:
            readable, writeable, exceptions = select.select(socket_list, socket_list, [])
            '''These call should not block'''
            for s in readable:
                if (s == self.__client_socket):
                    try:
                        request_data += s.recv(READ_SIZE)
                    except:
                        logging.info('Connection closed on client side')
                        return 0
                elif (s == self.__real_server_socket):
                    try:
                        response_data += s.recv(READ_SIZE)
                    except:
                        logging.info('Connection closed on server side')
                        return 0
            for s in writeable:
                '''If these send cause error, it will be detected at the start of the loop'''
                if (s == self.__client_socket and response_data != ''):
                    if not self.__request_filter_func or self.__request_filter_func(request_data) == True:
                        #intercept response
                        response_data = modifier(response_data)
                    try:
                        s.send(response_data)
                    except:
                        logging.info('Connection closed on client side')
                        return 0
                    response_data = ''
                elif (s == self.__real_server_socket and request_data != ''):
                    if not self.__request_filter_func or self.__request_filter_func(request_data) == True:
                        #intercept request before sending to client
                        request_data = modifier(request_data)    
                    try:
                        s.send(request_data)
                    except:
                        logging.info('Connection closed on server side')
                        return 0
                    request_data = ''
            time.sleep(sleep_interval)
            
class NonHTTPRequestHandler(SocketServer.BaseRequestHandler):
    def setup(self):
        #isSSL is global variable
        if isSSL:
            #create secure socket connection with client
            #do handshake with client
            try:
            	self.request = SSLcontext.wrap_socket(self.request, server_side = True)
            except Exception as e:
            	logging.critical('Error doing handshake with client')
            	logging.critical(e)
            	return -1
            
    def handle(self):
        logging.info('Handling new connection')
        #connect to REAL_SERVER
        self.__real_server_socket = socket.socket()
        try:
            self.__real_server_socket.connect( (REAL_SERVER, PORT) )
        except:
            logging.critical('Error connecting to REAL_SERVER')
            return -1
        #create secure socket connection with REAL_SERVER
        #do handshake with REAL_SERVER
        if isSSL:
            self.__real_server_socket = SSLcontext.wrap_socket(self.__real_server_socket)
        forwarder = FORWARDER(self.request, self.__real_server_socket)
        forwarder.forward_forever()
        
    def finish(self):
        self.__real_server_socket.close()
        logging.info('Finished')

class HTTPRequestHandler():
    pass

#Samelessly taken from http://kmkeen.com/socketserver/2009-02-07-07-52-15.html
class SimpleNonHTTPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    # Ctrl-C will cleanly kill all spawned threads
    daemon_threads = True
    # much faster rebinding
    allow_reuse_address = True

    def __init__(self, server_address, RequestHandlerClass):
        SocketServer.TCPServer.__init__(self, server_address, RequestHandlerClass)

# class SimpleHTTPServer(SocketServer.ThreadingMixIn, BaseHTTPServer.HTTPServer):
#     # Ctrl-C will cleanly kill all spawned threads
#     daemon_threads = True
#     # much faster rebinding
#     allow_reuse_address = True

#     def __init__(self, server_address, RequestHandlerClass):
#         BaseHTTPServer.HTTPServer.__init__(self, server_address, RequestHandlerClass)

#this function allow user to modify request/response data
#this function is really fucked up
#this function will be replaced
def modifier(data):
    L.acquire()
    logging.info('Modifying data\n' + data)
    TMPFILE = ''.join(random.choice(string.ascii_uppercase + string.digits + string.lowercase) for _ in range(8))
    with open(TMPFILE, 'wb') as f:
        f.write(repr(data))
    f.close()
    os.system('notepad %s\n' % TMPFILE)
    with open(TMPFILE, 'rb') as f:
        r = eval(' %s ' % f.read() )
    f.close()
    logging.info('Modified data\n' + r)
    os.unlink(TMPFILE)
    L.release()
    return r

def run(server_class, handler_class, server_address):
    server = server_class(server_address, handler_class)
    server.serve_forever()
          
if __name__ == '__main__':
    IF = sys.argv[1] #interface
    PORT = int( sys.argv[2] )
    REAL_SERVER = sys.argv[3] #the real host to connect to
    isSSL = int( sys.argv[4] )

    #lock
    L = threading.Lock()
    
    #create SSLcontext and load certificate
    SSLcontext = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
    SSLcontext.load_cert_chain('server.crt', 'server.key')
    SSLcontext.verify_mode = ssl.CERT_NONE
    SSLcontext.check_hostname = False

    #server_class = SimpleHTTPServer
    server_class = SimpleNonHTTPServer
    handler_class = NonHTTPRequestHandler
    #handler_class = HTTPRequestHandler
    run(server_class, handler_class, (IF, PORT))
    #server = SimpleNonHTTPServer((IF, PORT), NonHTTPRequestHandler)
