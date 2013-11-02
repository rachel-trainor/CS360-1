#web.py
"""
A TCP echo server that handles multiple clients with polling.  Typing
Control-C will quit the server.
"""

import argparse

from poller import Poller

class Main:
    """ Parse command line options and perform the download. """
    def __init__(self):
        self.parse_arguments()

    def parse_arguments(self):
        ''' parse arguments, which include '-p' for port '''
        parser = argparse.ArgumentParser(prog='Web Server', description='CS 360 Lab 4', add_help=True)
        parser.add_argument('-p', '--port', type=int, action='store', help='port the server will bind to',default=8080)
        parser.add_argument('-d', '--debug', action='store_true', help='if specified, will print debug info')        
        self.args = parser.parse_args()
        if self.args.debug:
            print "debug is on"
        else:
            print "debug is off"

    def run(self):
        p = Poller(self.args.port, self.args.debug)
        #p = Poller(self.args.port, self.args.debug)
        p.run()

if __name__ == "__main__":
    m = Main()
    m.parse_arguments()
    try:
        m.run()
        print "program done"
    except KeyboardInterrupt:
        pass