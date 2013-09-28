//============================================================================
// Name        : serverMain.cpp
// Author      :
// Version     :
// Copyright   : Your copyright notice
// Description : Hello World in C++, Ansi-style
//============================================================================

#include <iostream>
#include "Server.h"

using namespace std;

int main(int argc, char **argv) {
	cout << "Server Main" << endl;
	int option, port;

	// setup default arguments
	port = 8080;
	bool debug = false;

	// process command line options using getopt()
	// see "man 3 getopt"
	while ((option = getopt(argc, argv, "p:d")) != -1) {
		switch (option) {
		case 'p':
			port = atoi(optarg);
			break;
		case 'd':
			debug = true;
			break;
		default:
			cout << "server [-p port]" << endl;
			exit(EXIT_FAILURE);
		}
	}

	Server server = Server(port, debug);
}
