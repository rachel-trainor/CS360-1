/*
 * Message.h
 *
 *  Created on: Sep 16, 2013
 *      Author: adamjc
 */
#pragma once
#include <string>
#include <iostream>
#include <sstream>

using namespace std;

class Message {
public:
	Message();
	Message(string);
	Message(string, string);
	Message(string, string, string);
	Message(string, string, string, int);
	~Message();

	string getUser();
	string getSubject();
	string getMessage();
	int getLength();
	string toString();
	string intToString(int);

private:
	string user;
	string subject;
	string message;
	int length;
};
