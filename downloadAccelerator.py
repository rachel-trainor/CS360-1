import sys
import argparse
import os
import requests
import threading

'''Download one file using different numbers of threads'''
class DownloadAccelerator:
    def __init__(self):
        self.args = None
        self.in_file = 'urls.txt'
        self.dir = 'downloads'

        self.threads = 1
        self.url = 'http://www.google.com'

        self.parse_arguments()

        sys.stdout.write("Threads: %s" % self.threads)
        sys.stdout.write('\n')
        sys.stdout.write("URL: %s" % self.url)
        sys.stdout.write('\n')
        sys.stdout.write(self.url)
        sys.stdout.write('\n')
        sys.stdout.write(self.url.split('/')[-1].strip())
        sys.stdout.write('\n')

    def parse_arguments(self):
        parser = argparse.ArgumentParser(prog = 'DownloadAccelerator', 
            description = 'Download one file using different unumbers of threads',
             add_help=True)
        parser.add_argument('-n', '--threads', type=int, action='store', help='Specify the number of threads to create', default='1')
        parser.add_argument("URL", type=str, action='store', help='URL to download')

        args = parser.parse_args()
        self.threads = args.threads
        self.url = args.URL

    def download(self):
        '''download the file using the specified number of threads'''
        # self.url = self.url.split('/')[-1].strip()
        # sys.stdout.write('\n')
        # sys.stdout.write(self.url)
        # sys.stdout.write('\n')

        #r = requests.get('http://www.stackoverflow.com')
        r = requests.get('http://www.stackoverflow.com', headers={'Range': 'bytes=0-1000'})
        print r
        print r.headers
        #r = requests.get('https://cs360.byu.edu')
        #self.url)#, headers={'Range': 'bytes=0-1000'})
        content_length = r.headers['content-length']
        sys.stdout.write('\n')
        sys.stdout.write("content length: %s \n" %content_length)
        sys.stdout.write('\n')

        num_bytes = int(content_length)/self.threads
        sys.stdout.write("num_bytes: %s \n" %num_bytes)
        sys.stdout.write('\n')

        threads = []

        for i in range (0,self.threads):
            d = DownThread()
            threads.append(d)

        for t in threads:
            t.start()

        for t in threads:
            t.join()

class DownThread(threading.Thread):
    def __init__(self):
        #self.url = url
        #self.num_bytes = bytes
        self.byte_range = None
        self.file_contents = None
        threading.Thread.__init__(self)
        self._content_consumed = False

    def run(self):
        print self.getName(), "reporting for duty"



if __name__ == '__main__':
    d = DownloadAccelerator()
    d.download()





# ''' Downloader for a set of files '''
# class Downloader:
#     def __init__(self):
#         ''' initialize the file where the list of URLs is listed, and the
# directory where the downloads will be stored'''
#         self.args = None
#         self.in_file = 'urls.txt'
#         self.dir = 'downloads'
#         self.parse_arguments()

#     def parse_arguments(self):
#         ''' parse arguments, which include '-i' for input file and
# '-d' for download directory'''
#         parser = argparse.ArgumentParser(prog='Mass downloader', description='A simple script that downloads multiple files from a list of URLs specified in a file', add_help=True)
#         parser.add_argument('-i', '--input', type=str, action='store', help='Specify the input file containing a list of URLs, default is urls.txt',default='urls.txt')
#         parser.add_argument('-d', '--dir', type=str, action='store', help='Specify the directory where downloads are stored, default is downloads',default='downloads')
#         args = parser.parse_args()
#         self.in_file = args.input
#         self.dir = args.dir
#         if not os.path.exists(self.dir):
#             os.makedirs(self.dir)

#     def download(self):
#         ''' download the files listed in the input file '''
#         # setup URLs
#         urls = []
#         f = open(self.in_file,'r')
#         for line in f.readlines():
#             urls.append(line.strip())
#         f.close()
#         # setup download locations
#         files = [url.split('/')[-1].strip() for url in urls]
#         # create a thread for each url
#         threads = []
#         for f,url in zip(files,urls):
#             filename = self.dir + '/' + f
#             d = DownThread(url,filename)
#             threads.append(d)
#         for t in threads:
#             t.start()
#         for t in threads:
#             t.join()

# ''' Use a thread to download one file given by url and stored in filename'''
# class DownThread(threading.Thread):
#     def __init__(self,url,filename):
#         self.url = url
#         self.filename = filename
#         threading.Thread.__init__(self)
#         self._content_consumed = False

#     def run(self):
#         print 'Downloading %s' % self.url
#         r = requests.get(self.url, stream=True)
#         with open(self.filename, 'wb') as f:
#             f.write(r.content)
 
# if __name__ == '__main__':
#     d = Downloader()
#     d.download()