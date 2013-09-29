/*
 * Handler.h
 *
 *  Created on: Sep 28, 2013
 *      Author: adamjc
 */

#pragma once
#include <map>
#include <vector>
#include <string>
#include "Message.h"
#include <semaphore.h>

#include <pthread.h>
#include <arpa/inet.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <unistd.h>

using namespace std;

class Handler {
public:
	Handler();
	Handler(int, map<string, vector<Message> >*, bool, sem_t*);
	virtual ~Handler();

	void handle();
	string parseRequest(string);
	int readToSentinel(char, string);
	string isSpecial(string, string);
	string put(string);
	string list(string);
	string get(string);
	string reset();
	string addToMap(Message&);
	bool contains(string);
	string listResponse(string);
	string getResponse(string, size_t);
	string printMap();
	string intToString(int);
	string get_request(int);
	int determineLength(string);
	int deterHeaderLength(string);
	bool send_response(int, string);
	map<string, vector<Message> >& getMap();

private:
	int client;
	map<string, vector<Message> >* messageList;
	bool debug;
	int buflen_;
	char* buf_;
	sem_t* serverLock;
};
