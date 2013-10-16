import sys
import argparse
import os
import requests
import threading
import time

'''Download one file using different numbers of threads'''
class DownloadAccelerator:
    def __init__(self):
        self.args = None
        self.threads = 1
        self.url = 'http://www.google.com'
        self.dir = None

        self.parse_arguments()

    def parse_arguments(self):
        parser = argparse.ArgumentParser(prog = 'DownloadAccelerator', 
            description = 'Download one file using different unumbers of threads',
             add_help=True)
        parser.add_argument('-n', '--threads', type=int, action='store', help='Specify the number of threads to create', default='1')
        parser.add_argument("URL", type=str, action='store', help='URL to download')

        args = parser.parse_args()
        self.threads = args.threads
        self.url = args.URL
        self.dir = "downloads"
        self.filename = self.dir + '/' + self.url.split('/')[-1].strip()

        if not os.path.exists(self.dir):
            os.makedirs(self.dir)

    def download(self):
        '''download the file using the specified number of threads'''

        r = requests.head(self.url)
        content_length = r.headers['content-length']
        num_bytes = int(content_length)/self.threads

        threads = []
        start = 0
        end = 0

        for i in range (0,self.threads):
            if(i == 0):
                start = i*num_bytes
            else:
                start = (i*num_bytes)+i
            if(i < self.threads-1):
                end = start + num_bytes
            else:
                end = int(content_length)

            d = DownThread(start, end, self.url)
            threads.append(d)

        firstTime = time.time()

        for t in threads:
            t.start()

        with open(self.filename, 'wb') as f:
            for t in threads:
                t.join()
                f.write(t.file_contents)
            f.close()
                
        elapsed = (time.time() - firstTime)
        #print elapsed

        sys.stdout.write(self.url + " ")
        sys.stdout.write("%d " % self.threads)
        sys.stdout.write(content_length + " ")
        sys.stdout.write("%s " % elapsed + "\n")

class DownThread(threading.Thread):
    def __init__(self, start, end, url):
        self.url = url
        self.num_bytes = end - start
        self.start_range = start
        self.end_range = end
        self.file_contents = None
        threading.Thread.__init__(self)
        self._content_consumed = False

        #print self.getName(), self.start_range, " ", self.end_range

    def run(self):
        #r = requests.get(self.url, headers={'Range': 'bytes=%d-%d' %(self.start_range, self.end_range)})
        r = requests.get(self.url, headers={'Accept-Encoding': '', 'Range': 'bytes=%d-%d' %(self.start_range, self.end_range)})
        #print r.headers['content-range']
        self.file_contents = r.content
        
if __name__ == '__main__':
    d = DownloadAccelerator()
    d.download()