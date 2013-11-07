import sys
import os
import requests
import time
import matplotlib
matplotlib.use('Agg')
from pylab import *

class ResponseTime:
    def __init__(self):
        self.myServer = 'http://localhost:8010/file000.txt'
        self.lighttpd = 'http://localhost:8001/file000.txt'
        self.num = 100
        self.myServerTimes = []
        self.lighttpdTimes = []
        self.filename = 'times.txt'

        self.myServerAvg = None
        self.myServerMu = None
        self.myServerX = []
        self.myServerY = []

        self.lighttpdAvg = None
        self.lighttpdMu = None
        self.lighttpdX = []
        self.lighttpdY = []

        self.lightLoadFiles = ["web-lighttpd-1.txt", "web-lighttpd-65.txt",
        "web-lighttpd-130.txt","web-lighttpd-195.txt","web-lighttpd-260.txt",
        "web-lighttpd-325.txt","web-lighttpd-390.txt","web-lighttpd-455.txt",
        "web-lighttpd-520.txt","web-lighttpd-585.txt"]
        self.myServerLoadFiles = ["web-myServer-1.txt","web-myServer-61.txt",
        "web-myServer-122.txt","web-myServer-183.txt","web-myServer-244.txt",
        "web-myServer-305.txt","web-myServer-366.txt","web-myServer-427.txt",
        "web-myServer-488.txt","web-myServer-549.txt"]

    def run(self):
    	for i in range(0, self.num):

    		firstTime = time.time()
    		r = requests.get(self.myServer)
    		print i, " ", r
    		secondTime = time.time()

    		r2 = requests.get(self.lighttpd)
    		print "\n", i, " ", r
    		thirdTime = time.time()

    		myServerElapsed = (secondTime - firstTime)
    		lighttpdElapsed = (thirdTime - secondTime)
    		self.myServerTimes.append(myServerElapsed)
    		self.lighttpdTimes.append(lighttpdElapsed)

    def writeTimes(self):
    	f = open(self.filename, 'wb')
    	f.write("myServer: \n")

    	self.myServerAvg = 0
    	for t in self.myServerTimes:
    		f.write(str(t) + ", ")
    		self.myServerAvg += t

    	self.myServerAvg = self.myServerAvg/100
    	f.write("\nmyServerAvg: " + str(self.myServerAvg))

    	f.write("\nlighttpd: \n")
    	self.lighttpdAvg = 0

    	for t in self.lighttpdTimes:
    		f.write(str(t) + ", ")
    		self.lighttpdAvg += t

    	self.lighttpdAvg = self.lighttpdAvg/100
    	f.write("\nlighttpdAvg: " + str(self.lighttpdAvg))

    def createPoints(self):
    	self.myServerMu = 1/self.myServerAvg
    	muDiff = self.myServerMu/50

    	for i in range(0, 50):
			myLambda = i*muDiff
			xVal = myLambda/self.myServerMu
			yVal = 1/(self.myServerMu-myLambda)
			self.myServerX.append(xVal)
			self.myServerY.append(yVal)

        self.lighttpdMu = 1/self.lighttpdAvg
        muDiff = self.lighttpdMu/50

        for i in range(0,50):
			myLambda = i*muDiff
			xVal = myLambda/self.lighttpdMu
			yVal = 1/(self.lighttpdMu-myLambda)
			self.lighttpdX.append(xVal)
			self.lighttpdY.append(yVal)

    def linePlot(self):
        """ Create a line graph. """
        self.createPoints()

        clf()
        plot(self.myServerX, self.myServerY)
        xlabel('lambda / mu')
        ylabel('1 / (mu - lambda)')
        savefig('myServer.png')

        clf()
        plot(self.lighttpdX, self.lighttpdY)
        xlabel('lambda / mu')
        ylabel('1 / (mu - lambda)')
        savefig('lighttpd.png')

    def generateLoadTest(self):
        interval = self.myServerMu / 10
        port = 8010
        duration = 30
        #output = "myServer-%s.txt" % (name)

        print "mu = ", self.myServerMu
        print "interval = ", interval

        for i in range (0, 10):
            load = (i*interval) + 1
            output = "web-myServer-%s.txt" % int(load)
            os.system("python generator.py --port %s -l %s -d %s >> %s" % (port, int(load), duration, output))
            #os.system("python downloadAccelerator.py -n %s %s >> %s" % (thread,url,output))

        interval = self.lighttpdMu/10
        port = 8001
        duration = 30

        for i in range (0, 10):
            load = (i*interval) + 1
            output = "web-lighttpd-%s.txt" % int(load)
            os.system("python generator.py --port %s -l %s -d %s >> %s" % (port, int(load), duration, output))


    def boxplot(self, xvalues, yvalues):
        print "\nin boxplot()"
        #parseFiles("myServer")
        #parseFiles("light")
        """ Create a graph that includes a line plot and a boxplot. """
        clf()
        # plot the line
        #plot(self.x,self.averages)
        # plot the boxplot
        boxplot(yvalues,positions=xvalues,widths=0.5)
        xlabel('X Label (units)')
        ylabel('Y Label (units)')
        savefig('combined.png')

        print "\nexit boxplot()"

    def parseFiles(self, whichfiles):
        xvalues = []
        yvalues = []

        if whichfiles == "myServer":
            for currFile in self.myServerLoadFiles:
                print "currFile = ", currFile
                try:
                    f = open(currFile, 'r')
                    splitName = currFile.split('-')
                    getLoad = splitName[2]
                    getLoad = getLoad.split('.')
                    myLambda = float(getLoad[0])
                    print "\nmyLambda = ", myLambda

                    for line in f.readlines():
                        split = line.split()
                        print split
                        if split[2] == '200':
                            mu = float(split[5])
                            xval = myLambda/mu
                            print "lambda/mu = ", xval
                            xvalues.append(xval)
                            yval = 1/(mu - myLambda)
                            print "yval = ", yval
                            yvalues.append(yval)

                    self.boxplot(xvalues, yvalues)
                except IOError as e:
                    print "Error Opening File"
                    print "i/O error({0}): {1}".format(e.errno, e.strerror)


if __name__ == '__main__':
    r = ResponseTime()
    #r.run()
    #r.writeTimes()
    #r.linePlot()
    #r.generateLoadTest()
    r.parseFiles("myServer")