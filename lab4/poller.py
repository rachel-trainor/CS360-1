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
            self.server.setblocking(0)
        except socket.error, (value,message):
            if self.server:
                self.server.close()
            print "Could not open socket: " + message
            sys.exit(1)

    def readConf(self):
        if self.debug:
            print "\nconfigFile: ", self.configFile

        f = open(self.configFile, 'r')

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
                    if self.debug:
                        print "found something strange in configFile"

        f.close()

        if self.debug:
            print "\nhosts: \n", self.hosts
            print "\nmedia: \n", self.media
            print "\nparameters: \n", self.parameters
            print "\ntimeout: ", self.timeout


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
                fds = self.poller.poll(timeout=1)#int(self.timeout))
            except:
                return

            currentTime = time.time()
            #print "\ncurrentTime = ", currentTime
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
                result = self.handleClient(fd)

            now = time.time()
            #print "\nnow = ", now, "\nlastChecked = ", lastChecked, "\ndiff: ", now-lastChecked
            if now-lastChecked > self.threshold:
                toDelete = []
                for c in self.lastUsed:
                    if float(now - self.lastUsed[c]) > float(self.timeout):
                        #close the socket
                        if self.debug:
                            print "mark and sweep, closing ", c
                        toDelete.append(c)
                for c in toDelete:
                    self.closeSocket(c)
                toDelete = []
                lastChecked = time.time()

        if self.debug:
            print "end run()"

    def closeSocket(self, fd):
        if fd in self.clients:
            self.clients[fd].close()
            del self.clients[fd]
        if fd in self.lastUsed:
            del self.lastUsed[fd]
        if fd in self.cache:
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

    def handleServer(self):
        if self.debug:
            print "\nIn handleServer()"
        (client,address) = self.server.accept()
        client.setblocking(0) #for non blocking i/o on socket
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

                if data:
                    if '\r\n\r\n' in data:  #check if request is complete rather than just any data
                        dataSplit = data.split('\r\n')
                        (response, path, rangeRequest) = self.parseRequest(self.cache[fd])
                        self.sendResponse(fd, response, path, rangeRequest)
                        del self.cache[fd] # = ''
                        break
                    else:
                        continue
                else:
                    if self.debug:
                        print "\nremoving file descriptor: ", self.clients[fd]
                    self.poller.unregister(fd)
                    self.closeSocket(fd)
                    break
            except socket.error, e:
                if e.args[0] == errno.EWOULDBLOCK or e.args[0] == errno.EAGAIN:
                    if self.debug:
                        print "\nEWOULDBLOCK or EAGAIN in handleClient()"
                    break

    def sendResponse(self, fd, response, path, rangeRequest):
        if self.debug:
            print "\nIn sendResponse()"
            print "\nSending Response: ", response

        while True:
            try:
                self.clients[fd].send(response)
                break
            except socket.error, e:
                if e.args[0] == errno.EWOULDBLOCK or e.args[0] == errno.EAGAIN:
                    if self.debug:
                        print "EWOULDBLOCK or EAGAIN in sendFile() 1"
                    continue

        split = response.split()
        if path and split[1] == "200":
            f = open(path, 'rb')

            while True:
                stuffRead = f.read(self.size)
                if not stuffRead:
                    break

                totalsent = 0
                while totalsent < len(stuffRead):
                    try:
                        s = self.clients[fd].send(stuffRead[totalsent:])
                    except socket.error, e:
                        if e.args[0] == errno.EWOULDBLOCK or e.args[0] == errno.EAGAIN:
                            if self.debug:
                                print "EWOULDBLOCK or EAGAIN in sendFile() 2"
                            continue
                    totalsent += s
            f.close()

        if path and split[1] == "206":
            self.sendRangeResponse(fd, response, path, rangeRequest)

        if self.debug:
            print "Exit sendResponse()"

    def splitRangeRequest(self, rangeRequest):
        rangeRequest = rangeRequest.split('=')
        rangeRequest = rangeRequest[1].split('-')
        start = int(rangeRequest[0])
        end = int(rangeRequest[1])
        diff = (end - start) + 1

        return start, end, diff

    def sendRangeResponse(self, fd, response, path, rangeRequest):
        if self.debug:
            print "begin sendRangeResponse()"

        (start, end, diff) = self.splitRangeRequest(rangeRequest)

        if self.debug:
            print "start: ", start
            print "end: ", end
            print "diff: ", diff

        f = open(path, 'rb')
        stuffRead = ''
        totalToRead = diff
        totalRead = 0

        while totalRead < totalToRead:
            if self.debug:
                print "\ntotalRead < totalToRead ", totalRead, " < ", totalToRead
            #start reading from the specified start index
            f.seek(start + totalRead, 0)
            if self.debug:
                print "start + totalRead: ", start + totalRead
                print "diff: ", diff

            if diff < self.size:
                stuffRead = f.read(diff)
                totalRead += len(stuffRead)
                diff = diff - diff
                if self.debug:
                    print "stuffRead: ", stuffRead
                    print "length of stuffRead: ", len(stuffRead)
                    print "totalRead: ", totalRead
            else:
                stuffRead = f.read(self.size)
                totalRead += len(stuffRead)
                diff = diff - self.size
                if self.debug:
                    print "stuffRead: ", stuffRead
                    print "length of stuffRead: ", len(stuffRead)
                    print "totalRead: ", totalRead

            if not stuffRead:
                break

            totalsent = 0

            while totalsent < len(stuffRead):
                try:
                    s = self.clients[fd].send(stuffRead[totalsent:]) #change to send the whole thing
                    #print "s: \n", s
                except socket.error, e:
                    if e.args[0] == errno.EWOULDBLOCK or e.args[0] == errno.EAGAIN:
                        if self.debug:
                            print "EWOULDBLOCK or EAGAIN in sendFile() 2"
                        continue
                totalsent += s
        f.close()

        if self.debug:
            print "Exit sendRangeResponse()"

    def parseRequest(self,data):
        if self.debug:
            print "\nstart parseRequest()"

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
                            response = self.createResponse(path, rangeRequest)
                    else:
                        #use host given
                        path = self.hosts[host]
                        if self.debug:
                            print "\npath: ", path
                        path = path + url
                        if self.debug:
                            print "path + url: ", path
                        response = self.createResponse(path, rangeRequest)
        if returnHeadRequest:
            path = None

        if self.debug:
            print "end response"

        return response, path, rangeRequest

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

    def createResponse(self, path, rangeRequest):
        if self.debug:
            print "\nentered createResponse()"

        possibleError = self.verifyPath(path)

        if possibleError == None:
            start = None
            end = None
            diff = None

            t = time.time()
            currTime = self.get_time(t)
            filetype = path.split('.')[-1]

            if filetype in self.media:
                filetype = self.media[filetype]
            else:
                filetype = 'text/plain'

            if rangeRequest == None:
                response = 'HTTP/1.1 200 OK \r\n'
            else:
                response = 'HTTP/1.1 206 Partial Message \r\n'
                (start, end, diff) = self.splitRangeRequest(rangeRequest)

            response += 'Date: ' + currTime + '\r\n'
            response += 'Server: Apache/2.2.22 (Ubuntu) \r\n'
            response += 'Content-Type: ' + filetype + '\r\n'

            if rangeRequest == None:
                response += 'Content-Length: ' + str(os.stat(path).st_size) + '\r\n'
            else:
                response += 'Content-Length: ' + str(diff) + '\r\n'

            response += 'Last-Modified: ' + self.get_time(os.stat(path).st_mtime) + '\r\n'
            response += '\r\n'

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