#include "Server.h"

Server::Server(int port, bool debug) {
	// setup variables
	port_ = port;
	this->debug = debug;
	buffer = Buffer();
	sem_init(&serverLock, 0, 1);

// create and run the server
	create();
	makeThreads(NUMTHREADS);
	serve();
}

Server::~Server() {
}

void Server::create() {
	struct sockaddr_in server_addr;

	// setup socket address structure
	memset(&server_addr, 0, sizeof(server_addr));
	server_addr.sin_family = AF_INET;
	server_addr.sin_port = htons(port_);
	server_addr.sin_addr.s_addr = INADDR_ANY;

	// create socket
	server_ = socket(PF_INET, SOCK_STREAM, 0);
	if (!server_) {
		perror("socket");
		exit(-1);
	}

	// set socket to immediately reuse port when the application closes
	int reuse = 1;
	if (setsockopt(server_, SOL_SOCKET, SO_REUSEADDR, &reuse, sizeof(reuse))
			< 0) {
		perror("setsockopt");
		exit(-1);
	}

	// call bind to associate the socket with our local address and
	// port
	if (bind(server_, (const struct sockaddr *) &server_addr,
			sizeof(server_addr)) < 0) {
		perror("bind");
		exit(-1);
	}

	// convert the socket to listen for incoming connections
	if (listen(server_, SOMAXCONN) < 0) {
		perror("listen");
		exit(-1);
	}
}

void Server::serve() {
	// setup client
	int client;
	struct sockaddr_in client_addr;
	socklen_t clientlen = sizeof(client_addr);

	while (true) {
		client = accept(server_, (struct sockaddr *) &client_addr, &clientlen);

		if (client > 0) {
			buffer.append(client);
		} else {
			cout << "error accepting client" << endl;
		}
	}
	close(server_);
}

void * doWork(void *vptr) {
	Server* s;
	s = (Server*) vptr;

	while (1) {

		int currClient = s->buffer.take();
		Handler handler = Handler(currClient, &(s->messageList), s->debug,
				&(s->serverLock));
		handler.handle();
		close(currClient);
	}
}

void Server::makeThreads(int numThreads) {
	for (int i = 0; i < numThreads; i++) {
		pthread_t thread;
		pthread_create(&thread, NULL, &doWork, this);
		threads.push_back(&thread);
	}
}
