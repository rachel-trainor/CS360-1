#include <arpa/inet.h>
#include <errno.h>
#include <netdb.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <unistd.h>

#include <fstream>
#include <iostream>
#include <sstream>
#include <string>

using namespace std;

class Client {
public:
	Client(string, int);
	Client(string, int, bool);
	~Client();

private:

	void create();
	void parseInput();
	int isSpecial(string, string);
	void foundSend(string);
	void foundList(string);
	void foundRead(string);
	void quit();
	int readToSentinel(char, string);
	string getMessage();
	string intToString(int);
	bool send_request(string);
	bool get_response();

	int port_;
	string host_;
	bool debug;
	int server_;
	int buflen_;
	char* buf_;
};
