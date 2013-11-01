import select
import socket
import sys
import time
import os
import errno
import re
import stat

class Poller:
    """ Polling server """
    def __init__(self,port): #,debug):
        self.host = ""
        self.port = port
        self.clients = {}
        self.hosts = {}
        self.media = {}
        self.parameters = {}
        self.cache = {}
        self.validRequests = ["GET", "POST", "DELETE", "HEAD", "PUT"]

        print self.validRequests

        self.timeout = 1
        self.size = 10000
        self.debug = False
        self.configFile = 'web-server-testing-master/tests/web.conf'
        #self.configFile = 'web.conf'

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
        print "\nconfigFile: ", self.configFile

        f = open(self.configFile, 'r')

        #print f.readlines()

        for line in f.readlines():
            if len(line) > 1:
                print "line before split: ", line

                line = line.split()

                print "my line after split: ", line
                print line[0]

                if line[0] == "host":
                    path = line[2]
                    if path[0] != '/': #check if reletive or absolute path
                        path = os.getcwd() + '/' + path
                    self.hosts[line[1]] = path
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

        print "\nbegin run()"

        """ Use poll() to handle each incoming client."""
        self.poller = select.epoll()
        self.pollmask = select.EPOLLIN | select.EPOLLHUP | select.EPOLLERR
        self.poller.register(self.server,self.pollmask)
        while True:
            # poll sockets
            try:
                print "going to sleep"
                fds = self.poller.poll(timeout=int(self.timeout))
                print "waking up"
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
        print "\nIn handleError()"

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
            del self.cache[fd]

    def handleServer(self):
        print "\nIn handleServer()"

        (client,address) = self.server.accept()
        client.setblocking(0) #for non blocking i/o on a client socket
        self.clients[client.fileno()] = client
        self.poller.register(client.fileno(),self.pollmask)

    def handleClient(self,fd):
        print "\nIn handleClient()"

        while True:
            try:
                data = self.clients[fd].recv(self.size)

                #print "data from recv: \n", data, "\n"

                if fd in self.cache:
                    self.cache[fd] += data
                else:
                    self.cache[fd] = data

                if data: #(check if data is complete rather than just any data)
                    dataSplit = data.split('\r\n')
                    print "\ndataSplit: ", dataSplit
                    print "\ndataSplit[-1]", dataSplit[-1], "length: ", len(dataSplit[-1])
                    print "\ndataSplit[-2]", dataSplit[-2], "length: ", len(dataSplit[-2])
                    (response, path) = self.parseRequest(data)
                    #check if path is not none
                    #self.clients[fd].send(response)
                    self.sendResponse(fd, response, path)
                    break
                else:
                    print "\nremoving file descriptor: ", self.clients[fd]
                    self.poller.unregister(fd)
                    self.clients[fd].close()
                    del self.clients[fd]
                    del self.cache[fd]
                    break
            except socket.error, e:
                if e.args[0] == errno.EWOULDBLOCK or e.args[0] == errno.EAGAIN:
                    print "\nEWOULDBLOCK or EAGAIN in handleClient()"
                    break
                    #continue

        # data = self.clients[fd].recv(self.size)
        # if data:
        #     response = (data)
        #     #echo back what you received
        #     self.clients[fd].send(data)
        # else:
        #     self.poller.unregister(fd)
        #     self.clients[fd].close()
        #     del self.clients[fd]


    def sendResponse(self, fd, response, path):
        print "\nIn sendResponse()"
        #print response

        #if exists
        #if permission

        while True:
            try:
                self.clients[fd].send(response) # change to send the whole thing
                break
            except socket.error, e:
                if e.args[0] == errno.EWOULDBLOCK or e.args[0] == errno.EAGAIN:
                    print "EWOULDBLOCK or EAGAIN in sendFile() 1"
                    #break
                    continue

        split = response.split()
        print "split = ", split
        print "split[1] = ", split[1]

        if path and split[1] == "200":
            f = open(path, 'rb')

            while True:
                stuffRead = f.read(self.size)
                if not stuffRead:
                    break

                #print "\nstuff read: ", "\n", stuffRead, "\n"

                totalsent = 0

                while totalsent < len(stuffRead):
                    try:
                        s = self.clients[fd].send(stuffRead[totalsent:]) #change to send the whole thing
                        print "s: \n", s
                    except socket.error, e:
                        if e.args[0] == errno.EWOULDBLOCK or e.args[0] == errno.EAGAIN:
                            print "EWOULDBLOCK or EAGAIN in sendFile() 2"
                            #break
                            continue
                    totalsent += s
                    print "totalsent: \n", totalsent


        print "Exit sendResponse()"

    def parseRequest(self,data):
        print "\nstart parseRequest()"
        print "data: ", data

        #data = data.split()
        request = data.split()
        print "\nrequest: ", request
        headers = dict(re.findall(r"(?P<name>.*?): (?P<value>.*?)\r\n", data))
        print "\nheaders: ", headers

        response = None
        path = None
        host = None

        if request[0] not in self.validRequests:#put delete post head
            print request[0], "is NOT a valid request"
            response = self.createError("400", "Bad Request") #not implemented
        else:
            if request[0] != 'GET':
                response = self.createError("501", "Not Implemented")
            else:
                url = request[1]
                if url == '/':
                    url = '/index.html'
                version = request[2]

                #host = data[4]
                if 'Host' in headers:
                    host = headers['Host'].split(':')[0]
                    print "\nhost: ", host, "\n"

                if host not in self.hosts:
                    if 'default' not in self.hosts:
                        print "\nhere 2"
                        response = self.createError("400", "Bad Request") #bad request
                    else:
                        #use default host
                        print "using default host"
                        path = self.hosts['default']
                        print "\npath: ", path
                        path = path + url
                        print "path + url: ", path
                        response = self.createResponse(path)
                else:
                    #use host given
                    path = self.hosts[host]
                    print "\npath: ", path
                    path = path + url
                    print "path + url: ", path
                    response = self.createResponse(path)

        #print "Response: ", response
        print "end response"
        return response, path  #make sure path is ok

    def createError(self, errNum, errMsg):
        print "\nentered createError()", errNum, errMsg
        t = time.time()
        currTime = self.get_time(t)

        htmlErr = '<html> <body> <h1>' + errNum + ' ' + errMsg + '</h1> </body> </html>'
        print "htmlErr: ", htmlErr

        error = 'HTTP/1.1' + ' ' + errNum + ' ' + errMsg + '\r\n'
        error += 'Date: ' + currTime + '\r\n'
        error += 'Server: Apache/2.2.22 (Ubuntu) \r\n'
        error += 'Content-Type: text/html \r\n'
        error += 'Content-Length: ' + str(len(htmlErr)) + '\r\n'
        error += '\r\n'
        error += htmlErr
        error += '\r\n'
        error += '\r\n'
        return error

    def createResponse(self, path):
        print "\nentered createResponse()"

        possibleError = self.verifyPath(path)

        if possibleError == None:
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
            response += '\r\n'

            print "path.split", path.split('.')[-1]
            #print "Response: ", response

            return response
        else:
            return possibleError

    def get_time(self, t):
        gmt = time.gmtime(t)
        format = '%a, %d %b %Y %H :%M :%S GMT'
        time_string = time.strftime(format,gmt)
        return time_string

    def verifyPath(self, path):
        if os.path.isfile(path):
            print "path is a file"
            st = os.stat(path)
            if st.st_mode & stat.S_IRGRP:
                print "path is group readable"
                return None
            else:
                #don't have read permission
                return self.createError("403", "Forbidden")
        else:
            #file doesn't exist
            return self.createError("404", "Not Found")



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