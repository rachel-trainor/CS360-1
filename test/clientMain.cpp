//============================================================================
// Name        : clientMain.cpp
// Author      : 
// Version     :
// Copyright   : Your copyright notice
// Description : Hello World in C++, Ansi-style
//============================================================================

#include <iostream>
#include "Client.h"

using namespace std;

//int main() {
//	cout << "client main" << endl; // prints !!!Hello World!!!
//	cout << "% ";
//
//
//
//	Client c("localhost", 8081);
//	return 0;
//}


int main(int argc, char **argv)
{
	cout << "% ";
    int option;

    // setup default arguments
    int port = 8080;
    string host = "localhost";
    bool debug = false;

    // process command line options using getopt()
    // see "man 3 getopt"
    while ((option = getopt(argc,argv,"s:p:d")) != -1) {
        switch (option) {
            case 'p':
                port = atoi(optarg);
                break;
            case 's':
                host = optarg;
                break;
            case 'd':
            	debug = true;
            	break;
            default:
                cout << "client [-s server] [-p port]" << endl;
                exit(EXIT_FAILURE);
        }
    }

    Client client = Client(host, port, debug);
}
