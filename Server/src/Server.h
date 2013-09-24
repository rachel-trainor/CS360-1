#include <arpa/inet.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <unistd.h>

#include <string>
#include <iostream>
#include <sstream>
#include <map>
#include <vector>
#include "Message.h"

using namespace std;

class Server {
public:
	Server(int);
	Server(int, bool);
	~Server();

private:

	void create();
	void serve();
	void handle(int);
	string parseRequest(string);
	int readToSentinel(char, string);
	string isSpecial(string, string);
	string put(string);
	string list(string);
	string get(string);
	string reset();
	string addToMap(Message);
	bool contains(string);
	string listResponse(string);
	string getResponse(string, int);
	string printMap();
	string intToString(int);
	string get_request(int);
	int determineLength(string);
	int deterHeaderLength(string);
	bool send_response(int, string);

	int port_;
	bool debug;
	int server_;
	int buflen_;
	char* buf_;
	map<string, vector<Message> > messageList;
};
