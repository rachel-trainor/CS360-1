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
    def __init__(self,port, debug):
        self.host = ""
        self.port = port
        self.clients = {}
        self.lastUsed = {} #time for each socket, last time a request was made
        self.hosts = {}
        self.media = {}
        self.parameters = {}
        self.cache = {} #cache for each socket
        self.validRequests = ["GET", "POST", "DELETE", "HEAD", "PUT"] #method requests allowed in http request
        self.threshold = 5 #mark and sweep every 5 seconds

        print self.validRequests

        self.timeout = 1 #if socket has been idle this long, it will be closed
        self.size = 10000
        self.debug = debug
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
        print "in readConf, self.debug = ", self.debug
        if self.debug:
            print "\nconfigFile: ", self.configFile

        f = open(self.configFile, 'r')

        #print f.readlines()

        for line in f.readlines():
            if len(line) > 1:

                line = line.split()

                if line[0] == "host":
                    path = line[2]
                    if path[0] != '/': #check if reletive or absolute path
                        path = os.getcwd() + '/' + path
                    self.hosts[line[1]] = path

                elif line[0] == "media": 
                    self.media[line[1]] = line[2]

                elif line[0] == "parameter":
                    self.parameters[line[1]] = line[2]
                    if line[1] == "timeout":
                        self.timeout = line[2]
                else:
                    print "found something else"

        f.close()

        if self.debug:
            print "hosts: \n", self.hosts
            print "media: \n", self.media
            print "parameters: \n", self.parameters
            print "timeout: ", self.timeout


    def run(self):
        if self.debug:
            print "\nbegin run()"

        """ Use poll() to handle each incoming client."""
        self.poller = select.epoll()
        self.pollmask = select.EPOLLIN | select.EPOLLHUP | select.EPOLLERR
        self.poller.register(self.server,self.pollmask)

        lastChecked = time.time()

        while True:
            # poll sockets
            try:
                #print "going to sleep"
                fds = self.poller.poll(timeout=1)#int(self.timeout))
                #print "waking up"
            except:
                return

            currentTime = time.time()
            if self.debug:
                print "\ncurrentTime = ", currentTime
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
                self.lastUsed[fd] = currentTime
                if self.debug:
                    print "\nself.lastUsed[fd] = ", self.lastUsed[fd]
                result = self.handleClient(fd)

                now = time.time()
                if self.debug:
                    print "\nnow = ", now
                if now-lastChecked > self.threshold: #in for loop or outside?
                    if self.debug:
                        print "\nnow-lastChecked is greater than threshold ", now-lastChecked
                    for c in self.lastUsed:
                        if now - self.lastUsed[c] > self.timeout: # if now - lastUsed[c] > idleTime:
                            #close the socket
                            print "mark and sweep, closing ", fd
                            self.closeSocket(fd)
                    lastChecked = time.time()

        if self.debug:
            print "end run()"

    def closeSocket(self, fd):
        self.clients[fd].close()
        del self.clients[fd]
        del self.lastUsed[fd]
        del self.cache[fd]

    def handleError(self,fd):
        if self.debug:
            print "\nIn handleError()"

        self.poller.unregister(fd)
        if fd == self.server.fileno():
            # recreate server socket
            self.server.close()
            self.open_socket()
            self.poller.register(self.server,self.pollmask)
        else:
            # close the socket
            self.closeSocket(fd)
            # self.clients[fd].close()
            # del self.clients[fd]
            # del self.lastUsed[fd]
            # del self.cache[fd]

    def handleServer(self):
        if self.debug:
            print "\nIn handleServer()"

        (client,address) = self.server.accept()
        client.setblocking(0) #for non blocking i/o on a client socket
        self.clients[client.fileno()] = client
        self.lastUsed[client.fileno()] = -1
        self.poller.register(client.fileno(),self.pollmask)

    def handleClient(self,fd):
        if self.debug:
            print "\nIn handleClient()"

        while True:
            try:
                data = self.clients[fd].recv(self.size)

                if self.debug:
                    print "data from recv: \n", data, "\n"

                if fd in self.cache:
                    self.cache[fd] += data
                else:
                    self.cache[fd] = data

                if data: #data[-1] == '\r\n' and data[-2] == '\r\n': #(check if data is complete rather than just any data)
                    dataSplit = data.split('\r\n')
                    if self.debug:
                        print "\ndataSplit: ", dataSplit
                        print "\ndataSplit[-1]", dataSplit[-1], "length: ", len(dataSplit[-1])
                        print "\ndataSplit[-2]", dataSplit[-2], "length: ", len(dataSplit[-2])
                    (response, path, rangeRequest) = self.parseRequest(data)
                    #check if path is not none
                    #self.clients[fd].send(response)
                    self.sendResponse(fd, response, path, rangeRequest)
                    break
                else:
                    if self.debug:
                        print "\nremoving file descriptor: ", self.clients[fd]
                    self.poller.unregister(fd)
                    self.closeSocket(fd)
                    # self.clients[fd].close()
                    # del self.clients[fd]
                    # del self.lastUsed[fd]
                    # del self.cache[fd]
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


    def sendResponse(self, fd, response, path, rangeRequest):
        if self.debug:
            print "\nIn sendResponse()"
        #print response

        while True:
            try:
                self.clients[fd].send(response)
                break
            except socket.error, e:
                if e.args[0] == errno.EWOULDBLOCK or e.args[0] == errno.EAGAIN:
                    print "EWOULDBLOCK or EAGAIN in sendFile() 1"
                    #break
                    continue

        split = response.split()
        if self.debug:
            print "split = ", split
            print "split[1] = ", split[1]

        if path and split[1] == "200":

            if rangeRequest != None:
                self.sendRangeResponse(fd, response, path, rangeRequest)

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
                        #print "s: \n", s
                    except socket.error, e:
                        if e.args[0] == errno.EWOULDBLOCK or e.args[0] == errno.EAGAIN:
                            print "EWOULDBLOCK or EAGAIN in sendFile() 2"
                            #break
                            continue
                    totalsent += s
                    #print "totalsent: \n", totalsent
            f.close()

        if self.debug:
            print "Exit sendResponse()"

    def sendRangeResponse(self, fd, response, path, rangeRequest):
        if self.debug:
            print "begin sendRangeResponse()"
            print "\nresponse", response

        response = self.editResponse(response)

        rangeRequest = rangeRequest.split('=')
        rangeRequest = rangeRequest[1].split('-')
        start = int(rangeRequest[0])
        end = int(rangeRequest[1])
        diff = end - start

        f = open(path, 'rb')
        stuffRead = 0

        while stuffRead < diff:
            #start reading from the specified start index
            f.seek(start + stuffRead, 0)
            diff = diff - stuffRead
            if diff < self.size:
                stuffRead = f.read(diff)
            else:
                stuffRead = f.read(self.size)

            if not stuffRead:
                break

            #print "\nstuff read: ", "\n", stuffRead, "\n"

            totalsent = 0

            while totalsent < len(stuffRead):
                try:
                    s = self.clients[fd].send(stuffRead[totalsent:]) #change to send the whole thing
                    #print "s: \n", s
                except socket.error, e:
                    if e.args[0] == errno.EWOULDBLOCK or e.args[0] == errno.EAGAIN:
                        print "EWOULDBLOCK or EAGAIN in sendFile() 2"
                        #break
                        continue
                totalsent += s
                #print "totalsent: \n", totalsent
        f.close()

        if self.debug:
            print "Exit sendRangeResponse()"

    def editResponse(self, response):
        #change the response to reflect a Partial Message
        if self.debug:
            print "in editResponse()"

        response = response.split()
        print "\nresponse split: ", response
        response[1] = '206'
        response[2] = 'Partial Message'
        response = ' '.join(response)
        print "\njoined response", response

        return response

    def parseRequest(self,data):
        if self.debug:
            print "\nstart parseRequest()"
            print "data: ", data

        #data = data.split()
        request = data.split()
        headers = dict(re.findall(r"(?P<name>.*?): (?P<value>.*?)\r\n", data))

        if self.debug:
            print "\nrequest: ", request
            print "\nheaders: ", headers

        rangeRequest = None
        response = None
        path = None
        host = None
        returnHeadRequest = False

        if 'Range' in headers:
            rangeRequest = headers['Range']
            if self.debug:
                print 'rangeRequest = ', rangeRequest

        if request[0] not in self.validRequests:#put delete post head get
            if self.debug:
                print request[0], "is NOT a valid request"
            response = self.createError("400", "Bad Request")
        else:

            if request[0] != 'GET' and request[0] != 'HEAD':
                response = self.createError("501", "Not Implemented")
            else:
                if request[0] == 'HEAD':
                    returnHeadRequest = True
                url = request[1]
                if url == 'HTTP/1.1':
                    if self.debug:
                        print "no url"
                    response = self.createError("400", "Bad Request")
                else:
                    if url == '/':
                        url = '/index.html'
                    version = request[2]

                    #host = data[4]
                    if 'Host' in headers:
                        host = headers['Host'].split(':')[0]
                        if self.debug:
                            print "\nhost: ", host, "\n"

                    if host not in self.hosts:
                        if 'default' not in self.hosts:
                            if self.debug:
                                print "\nhere 2"
                            response = self.createError("400", "Bad Request") #bad request
                        else:
                            #use default host
                            if self.debug:
                                print "using default host"
                            path = self.hosts['default']
                            if self.debug:
                                print "\npath: ", path
                            path = path + url
                            if self.debug:
                                print "path + url: ", path
                            response = self.createResponse(path)
                    else:
                        #use host given
                        path = self.hosts[host]
                        if self.debug:
                            print "\npath: ", path
                        path = path + url
                        if self.debug:
                            print "path + url: ", path
                        response = self.createResponse(path)
        if returnHeadRequest:
            path = None
        #print "Response: ", response
        if self.debug:
            print "end response"

        return response, path, rangeRequest  #make sure path is ok

    def createError(self, errNum, errMsg):
        if self.debug:
            print "\nentered createError()", errNum, errMsg
        t = time.time()
        currTime = self.get_time(t)

        htmlErr = '<html> <body> <h1>' + errNum + ' ' + errMsg + '</h1> </body> </html>'

        if self.debug:
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
        if self.debug:
            print "\nentered createResponse()"

        possibleError = self.verifyPath(path)

        if possibleError == None:
            t = time.time()
            currTime = self.get_time(t)
            filetype = path.split('.')[-1]

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

            if self.debug:
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
            if self.debug:
                print "path is a file"
            st = os.stat(path)
            if st.st_mode & stat.S_IRGRP:
                if self.debug:
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