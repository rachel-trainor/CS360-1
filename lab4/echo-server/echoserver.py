"""
A TCP echo server that handles one client at a time.  Typing Control-C
will quit the server.
"""

import argparse

from server import Server

class Main:
    """ Parse command line options and perform the download. """
    def __init__(self):
        self.parse_arguments()

    def parse_arguments(self):
        ''' parse arguments, which include '-p' for port '''
        parser = argparse.ArgumentParser(prog='Echo Server', description='A simple echo server that handles one client at a time', add_help=True)
        parser.add_argument('-p', '--port', type=int, action='store', help='port the server will bind to',default=3000)
        self.args = parser.parse_args()

    def run(self):
        s = Server(self.args.port)
        s.run()

if __name__ == "__main__":
    m = Main()
    m.parse_arguments()
    try:
        m.run()
    except KeyboardInterrupt:
        pass
