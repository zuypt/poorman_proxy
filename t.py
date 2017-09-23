class HTTPRequestHandler(SocketServer.BaseRequestHandler):
    '''read initial header from client'''
    def read_header(self):
        t = ''
        while not t.endswith('\r\n'*2):
            try:
                t += self.request.recv(1024)
            except Exception as e:
                print e
                return None
        self.__raw_header = t
        return t

    def parse_header(self):
        self.__parse_success = 0
        if self.__raw_header.startswith('GET'):
            #HTTP
            self.__isSSL = 0
        elif self.__raw_header.startswith('CONNECT'):
            #HTTPS
            self.__isSSL = 1
        else:
            return -1

        t = self.__raw_header.split('\r\n')
        '''parse URI'''
        if self.__isSSL:
            pass
        else:
            #let's not care about other HTTP version for now
            self.__URI = t[1].replace('GET', '').replace('HTTP/1.1', '').strip()
        '''create header dictionary'''
        self.__header = {}
        '''skip the first line'''
        for line in t[1:]:
            if line != '':
                t2 = line.split(':')
                if len(t2) < 2:
                    return -1
                self.__header[ t2[0].strip() ] = ':'.join(t2[1:]).strip()

        if not 'Host' in self.__header:
            return -1
        '''I simplify thing to much, but it should work first'''
        if ':' in self.__header['Host']:
                    
        self.__parse_success = 1
        return self.__header
        
    def setup(self):
        self.read_header()
        self.parse_header()
    
    def handle(self):
        if not self.__parse_success:
            return -1
        print self.__header['Host']
      
        
    def finish(self):
        pass
