Adam Christiansen
CS 360 Lab 4 Web Server

To run the server:
	python web.py -p 8000 (or any other port)

To run the tests:
	cd web-server-testing-master
	cd tests
	then run the desired test

	stress test:
	python stress-test.py localhost:8000/static/files/largefile.txt -t 100 -d 10
	
	protocol test: (I did do the extra credit)

	***You need to change the permissions on 
	***web-server-testing-master/web/static/files/test.txt
	***so that it generates a 403 Forbidden response since I cannot tar a
	***restricted file
	***use chmod ugo-rwx test.txt

	python protocol.py -s localhost -p 8000 -e

Describe how you handle non-blocking I/O, timeouts and caching
	I handle non-blocking I/O by creating non-blocking sockets. (web.py 
	Lines 39,161) Then, when sending or receiving, I check for errors 
	EWOULDBLOCK and EAGAIN and if they are found I try to send again 
	or move on and receive from another socket.(web.py Lines 198, 213, 232, 306)

	I handle timeouts using a mark-and-sweep algorithm which checks each socket
	and compares the last time it was active with a timeout and closes the socket
	if it has been inactive too long. (web.py run() Line 83, 124)

	I handle caching by creating a map that maps the socket to the request it has
	received so far. If the request is complete, I parse the request and send a
	response. If the request is incomplete, I call receive again and concatenate
	onto the previous part of the request. (web.py handleClient() Lines 166, 178,
	187)









