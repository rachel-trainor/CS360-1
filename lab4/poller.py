import select
import socket
import sys
import time
import os
import errno

class Poller:
    """ Polling server """
    def __init__(self,port): #,debug):
        self.host = ""
        self.port = port
        self.clients = {}
        self.hosts = {}
        self.media = {}
        self.parameters = {}
        self.timeout = 1
        self.size = 10000
        self.debug = False
        self.configFile = 'web.conf'

        self.open_socket()
        self.readConf()

    def open_socket(self):
        """ Setup the socket for incoming clients """
        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)
            self.server.bind((self.host,self.port))
            self.server.listen(5)
        except socket.error, (value,message):
            if self.server:
                self.server.close()
            print "Could not open socket: " + message
            sys.exit(1)

    def readConf(self):
        print "configFile: ", self.configFile

        f = open(self.configFile, 'r')

        #print f.readlines()

        for line in f.readlines():
            if len(line) > 1:
                print "line before split: ", line

                line = line.split()

                print "my line after split: ", line
                print line[0]

                if line[0] == "host":
                    self.hosts[line[1]] = line[2]
                    print "found host"

                elif line[0] == "media":
                    self.media[line[1]] = line[2]
                    print "found media"

                elif line[0] == "parameter":
                    self.parameters[line[1]] = line[2]
                    if line[1] == "timeout":
                        self.timeout = line[2]
                    print "found parameter"

                else:
                    print "found something else"

        print "hosts: \n", self.hosts
        print "media: \n", self.media
        print "parameters: \n", self.parameters
        print "timeout: ", self.timeout


    def run(self):

        print "begin run()"

        """ Use poll() to handle each incoming client."""
        self.poller = select.epoll()
        self.pollmask = select.EPOLLIN | select.EPOLLHUP | select.EPOLLERR
        self.poller.register(self.server,self.pollmask)
        while True:
            # poll sockets
            try:
                fds = self.poller.poll(timeout=int(self.timeout))
            except:
                return
            for (fd,event) in fds:
                # handle errors
                if event & (select.POLLHUP | select.POLLERR):
                    self.handleError(fd)
                    continue
                # handle the server socket
                if fd == self.server.fileno():
                    self.handleServer()
                    continue
                # handle client socket
                result = self.handleClient(fd)

        print "end run()"

    def handleError(self,fd):
        self.poller.unregister(fd)
        if fd == self.server.fileno():
            # recreate server socket
            self.server.close()
            self.open_socket()
            self.poller.register(self.server,self.pollmask)
        else:
            # close the socket
            self.clients[fd].close()
            del self.clients[fd]

    def handleServer(self):
        (client,address) = self.server.accept()
        client.setblocking(0) #for non blocking i/o on a client socket
        self.clients[client.fileno()] = client
        self.poller.register(client.fileno(),self.pollmask)

    def handleClient(self,fd):
        while True:
            try:
                data = self.clients[fd].recv(self.size)
                if data:
                    #store part of message in cache??
                    response = self.parseRequest(data)
                    self.clients[fd].send(response)
                else:
                    self.poller.unregister(fd)
                    self.clients[fd].close()
                    del self.clients[fd]
            except socket.error, e:
                if e.args[0] == errno.EWOULDBLOCK or e.args[0] == errno.EAGAIN:
                    print "EWOULDBLOCK or EAGAIN"
                    break

        # data = self.clients[fd].recv(self.size)
        # if data:
        #     response = (data)
        #     #echo back what you received
        #     self.clients[fd].send(data)
        # else:
        #     self.poller.unregister(fd)
        #     self.clients[fd].close()
        #     del self.clients[fd]


    def parseRequest(self,data):
        print "start parseRequest()"
        print "data: ", data

        data = data.split()
        print data

        response = None

        if data[0] != 'GET':
            response = self.createError(501) #not implemented
        else:
            url = data[1]
            if url == '/':
                url = '/index.html'
            version = data[2]
            if version != 'HTTP/1.1':
                print "here 1"
                response = self.createError(400) #bad request
            else:
                host = data[4]
                if 'host' not in self.hosts:
                    if 'default' not in self.hosts:
                        print "here 2"
                        response = self.createError(400) #bad request
                    else:
                        #use default host
                        path = self.hosts['default']
                        print "path: ", path
                        path = path + url
                        print "path + url: ", path
                        response = self.createResponse(path)
                else:
                    #use host given
                    path = self.hosts[host]
                    print "path: ", path
                    path = path + url
                    print "path + url: ", path
                    response = self.createResponse(path)

        print "Response: ", response
        return response

    def createError(self, errNum):
        print "entered createError()", errNum


    def createResponse(self, path):
        print "entered createResponse()"

        t = time.time()
        currTime = self.get_time(t)
        filetype = path.split('.')[-1]
        print "filetype: ", filetype
        print "filetype[0]: ", filetype[0]
        print "filetype size: ", len(filetype)

        if filetype in self.media:
            filetype = self.media[filetype]
        else:
            filetype = 'text/plain'

        response = 'HTTP/1.1 200 OK \r\n'
        response += 'Date: ' + currTime + '\r\n'
        response += 'Server: Apache/2.2.22 (Ubuntu) \r\n'
        response += 'Content-Type: ' + filetype + '\r\n'
        response += 'Content-Length: ' + str(os.stat(path).st_size) + '\r\n'
        response += 'Last-Modified: ' + self.get_time(os.stat(path).st_mtime) + '\r\n'

        print "path.split", path.split('.')[-1]
        print "Response: ", response

        return response

    def get_time(self, t):
        gmt = time.gmtime(t)
        format = '%a, %d %b %Y %H :%M :%S GMT'
        time_string = time.strftime(format,gmt)
        return time_string


#  call open() to determine whether you can access the le
# 1 try:
# 2 open ( filename )
# 3 except IOError as ( errno , strerror ):
# 4 if errno == 13:
# 5 // 403 Forbidden
# 6 elif errno == 2:
# 7 // 404 Not Found
# 8 else:
# 9 // 500 Internal Server Error


# 1 import time
# 2 import os
# 3 filename = '/ etc / motd '
# 4
# 5 def get_time ( t ):
# 6 gmt = time . gmtime ( t )
# 7 format = '%a , % d % b % Y % H :% M :% S GMT '
# 8 time_string = time . strftime ( format , gmt )
# 9 return time_string
# 10
# 11 t = time . time ()
# 12 current_time = get_time ( t )
# 13 mt = os . stat ( filename ). st_mtime
# 14 mod_time = get_time ( mt )
# 15 print current_time
# 16 print mod_time



#  use non-blocking I/O
#  while loop
#      call recv()
#      if returns EAGAIN or EWOULDBLOCK, break from loop
#      append to cache for that socket
#      check for end of a message (\r\n\r\n)
#      process any HTTP messages present
#      leave any remainder in the cache
#      if messages processed, break from loop
#  handles pipelined requests properly
#  prevents a busy client from monopolizing the server