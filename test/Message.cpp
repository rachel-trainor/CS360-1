/*
 * Message.cpp
 *
 *  Created on: Sep 16, 2013
 *      Author: adamjc
 */

#include "Message.h"

Message::Message() {
	user = "";
	subject = "";
	message = "";
	length = 0;
}

Message::Message(string user) {
	this->user = user;
	subject = "";
	message = "";
	length = 0;
}

Message::Message(string user, string subject) {
	this->user = user;
	this->subject = subject;
	message = "";
	length = 0;
}

Message::Message(string user, string subject, string message) {
	this->user = user;
	this->subject = subject;
	this->message = message;
	length = 0;
}

Message::Message(string user, string subject, string message, int length) {
	this->user = user;
	this->subject = subject;
	this->message = message;
	this->length = length;
}

Message::~Message() {
	// TODO Auto-generated destructor stub
}

string Message::getUser() {
	return user;
}

string Message::getSubject() {
	return subject;
}

string Message::getMessage() {
	return message;
}

int Message::getLength() {
	return length;
}

string Message::toString() {
//message [subject] [length]\n[message]
	string toReturn = "message ";
	toReturn += subject;
	toReturn += " ";
	toReturn += intToString(length);
	toReturn += "\n";
	toReturn += message;

	return toReturn;
}

string Message::intToString(int num) {
	stringstream myStringStream;
	string toReturn;
	myStringStream << num;
	toReturn = myStringStream.str();

	return toReturn;
}

