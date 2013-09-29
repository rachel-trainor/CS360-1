/*
 * Handler.cpp
 *
 *  Created on: Sep 28, 2013
 *      Author: adamjc
 */

#include "Handler.h"

Handler::Handler() {
	this->client = -1;
	this->debug = false;
	buflen_ = 1024;
	buf_ = new char[buflen_ +1];
}

Handler::Handler(int client, map<string, vector<Message> >* messageList, bool debug, sem_t* serverLock) {
	this->client = client;
	this->messageList = messageList;

	this->debug = debug;
	buflen_ = 1024;
	buf_ = new char[buflen_ + 1];
	this->serverLock = serverLock;
}

Handler::~Handler() {
	delete buf_;
}

void Handler::handle() {

	// loop to handle all requests
	while (1) {
		// get a request
		string request = get_request(client);

		// break if client is done or an error occurred
		if (request.empty()) {
			if (debug)
				cout << "connection closed" << endl;
			break;
		}
		if (debug) {
			cout << "server received this request: " << request << endl;
		}

		string response = parseRequest(request);

		if (debug) {
			cout << "Server response: " << response << endl;
		}

		// send response
		bool success = send_response(client, response);
		// break if an error occurred
		if (not success)
			break;
	}
}

string Handler::parseRequest(string line) {
	size_t index = readToSentinel(' ', line);
	string command = line.substr(0, index);

	if (line.size() > index + 1) {
		line = line.substr(index + 1);
	} else {
		//cout << "- Not Enough Parameters -" << endl;
		//string error = "error - Not Enough Parameters -\n";
		//return error;
	}

	string toReturn = isSpecial(command, line);
	return toReturn;
}

int Handler::readToSentinel(char sentinel, string line) {
	string toReturn = "";
	size_t i = 0;

	for (i = 0; i < line.size(); i++) {
		if (line.at(i) != sentinel) {
			toReturn += line.at(i);
		} else {
			break;
		}
	}
	return i;
}

string Handler::isSpecial(string value, string theRest) {

	if (value == "put") {
		return put(theRest);
	} else if (value == "list") {
		return list(theRest);
	} else if (value == "get") {
		return get(theRest);
	} else if (value == "reset\n") {
		return reset();
	} else {
		return "error - Command Not Recognized -\n";
	}
}

string Handler::put(string line) {

	size_t index = readToSentinel(' ', line);
	string user = line.substr(0, index);

	if (line.size() > index + 1) {
		line = line.substr(index + 1);
	} else {
		return "error - Not Enough Parameters -\n";
	}

	index = readToSentinel(' ', line);
	string subject = line.substr(0, index);

	if (line.size() > index + 1) {
		line = line.substr(index + 1);
	} else {
		return "error - Not Enough Parameters -\n";
	}

	index = readToSentinel('\n', line);
	string length = line.substr(0, index);

	if (line.size() > index + 1) {
		line = line.substr(index + 1);
	} else {
		return "error - Not Enough Parameters -\n";
	}

	string message = line;

	Message m(user, subject, message, message.size());
	string toReturn = addToMap(m);

	return toReturn;
}

string Handler::list(string line) {

	int index = readToSentinel('\n', line);
	string user = line.substr(0, index);

	sem_wait(serverLock); //lock around contains method
	if (contains(user)) {
		sem_post(serverLock);
		string lResponse = listResponse(user);
		return lResponse;
	} else {
		sem_post(serverLock);
		string error =
				"error user doesn't exist so he has no messages to list\n";
		return error;
	}
}

string Handler::get(string line) {

	size_t index = readToSentinel(' ', line);
	string user = line.substr(0, index);

	if (line.size() > index + 1) {
		line = line.substr(index + 1);
	} else {
		string error = "error - Not Enough Parameters -\n";
		return error;
	}

	index = readToSentinel('\n', line);
	string messageNum = line.substr(0, index);

	// TODO check that num is a valid number, not random chars
	int num = atoi(messageNum.c_str());

	sem_wait(serverLock); //locking around contains
	if (contains(user)) {
		sem_post(serverLock);
		string gResponse = getResponse(user, num);
		return gResponse;
	} else {
		sem_post(serverLock);
		string error = "error user doesn't exist so can't get message\n";
		return error;
	}

}

string Handler::reset() {
	sem_wait(serverLock);

	messageList->clear();

	sem_post(serverLock);
	return "OK\n";
}

string Handler::addToMap(Message& m) {
	sem_wait(serverLock);

	map<string, vector<Message> >::iterator it;
	string name = m.getUser();

	if (contains(name)) {
		for (it = messageList->begin(); it != messageList->end(); ++it) {
			if (it->first == name) {
				it->second.push_back(m);
				//break;
				sem_post(serverLock);
				return "OK\n";
			} else {
				sem_post(serverLock);
				return "error in addToMap\n";
			}
		}
	} else {
		vector<Message> tempVector;
		tempVector.push_back(m);
		messageList->insert(pair<string, vector<Message> >(name, tempVector));
	}

	sem_post(serverLock);
	return "OK\n";
}

bool Handler::contains(string name) {

	if (messageList->find(name) != messageList->end()) {
		return true;
	} else {
		return false;
	}
}

string Handler::listResponse(string name) {
	sem_wait(serverLock);
	map<string, vector<Message> >::iterator it;
	string toReturn = "list ";

	for (it = messageList->begin(); it != messageList->end(); ++it) {
		if (it->first == name) {
			toReturn += intToString(it->second.size());
			toReturn += "\n";
			for (size_t i = 0; i < it->second.size(); i++) {
				toReturn += intToString(i + 1);
				toReturn += " ";
				toReturn += it->second.at(i).getSubject();
				toReturn += "\n";
			}
		}
	}

	sem_post(serverLock);
	return toReturn;
}

string Handler::getResponse(string name, size_t index) {
	sem_wait(serverLock);
	map<string, vector<Message> >::iterator it;
	string toReturn = "";

	for (it = messageList->begin(); it != messageList->end(); ++it) {
		if (it->first == name) {
			if (it->second.size() > index - 1) {
				toReturn = it->second.at(index - 1).toString();
				//toReturn += "\n";
				sem_post(serverLock);
				return toReturn;
			} else {
				toReturn = "error no message at that index\n";
			}
		}
	}

	sem_post(serverLock);
	return toReturn;
}

string Handler::printMap() {
	sem_wait(serverLock);
	map<string, vector<Message> >::iterator it;
	string toReturn = intToString(messageList->size());
	toReturn += "\n";

	for (it = messageList->begin(); it != messageList->end(); ++it) {
		toReturn += it->first;
		toReturn += "\n";
		toReturn += "\t";

		for (size_t i = 0; i < it->second.size(); i++) {
			toReturn += it->second.at(i).toString();
		}
	}

	sem_post(serverLock);
	return toReturn;
}

string Handler::intToString(int num) {
	stringstream myStringStream;
	string toReturn;
	myStringStream << num;
	toReturn = myStringStream.str();

	return toReturn;
}

string Handler::get_request(int client) {
	string request = "";
	int nread = -1;
	// read until we get a newline

	//sem_wait(&requestLock);
	while (request.find("\n") == string::npos) {
		nread = recv(client, buf_, 1024, 0);
		if (nread < 0) {
			if (errno == EINTR)
				// the socket call was interrupted -- try again
				continue;
			else
				// an error occurred, so break out
				//sem_post(&requestLock);
				return "";
		} else if (nread == 0) {
			// the socket is closed
			//sem_post(&requestLock);
			return "";
		}
		// be sure to use append in case we have binary data
		request.append(buf_, nread);
	}
	//sem_post(&requestLock);

	// a better server would cut off anything after the newline and
	// save it in a cache

	int mLength = determineLength(request);
	int headerLength = deterHeaderLength(request);
	int difference = 0;

	if (mLength > 0) {
		if (mLength + headerLength > 1024) {
			difference = (mLength + headerLength) - nread;	//1024;

			while (difference > 0) {
				nread = recv(client, buf_, 1024, 0);
				if (nread < 0) {
					if (errno == EINTR)
						// the socket call was interrupted -- try again
						continue;
					else
						// an error occurred, so break out
						return "";
				} else if (nread == 0) {
					// the socket is closed
					return "";
				}
				// be sure to use append in case we have binary data
				request.append(buf_, nread);

				difference -= nread;
			}
		}
	}

	if (debug) {
		cout << "~~~" << request << endl;
	}
	return request;
}

int Handler::determineLength(string line) {
	size_t index = readToSentinel(' ', line);
	string command = line.substr(0, index);

	if (command == "put") {

		if (line.size() > index + 1) {
			line = line.substr(index + 1);
		} else {
			if (debug) {
				cout << "error in determinLength()" << endl;
			}
		}

		index = readToSentinel(' ', line);
		string user = line.substr(0, index);

		if (line.size() > index + 1) {
			line = line.substr(index + 1);
		} else {
			if (debug) {
				cout << "error - Not Enough Parameters -\n" << endl;
			}
		}

		index = readToSentinel(' ', line);
		string subject = line.substr(0, index);

		if (line.size() > index + 1) {
			line = line.substr(index + 1);
		} else {
			if (debug) {
				cout << "error - Not Enough Parameters -\n" << endl;
			}
		}

		index = readToSentinel('\n', line);
		string length = line.substr(0, index);

		if (line.size() > index + 1) {
			line = line.substr(index + 1);
		} else {
			if (debug) {
				cout << "error - Not Enough Parameters -\n" << endl;
			}
		}
		string message = line;
		return atoi(length.c_str());

	} else {
		return -1;
	}
}

int Handler::deterHeaderLength(string line) {
	int index = readToSentinel('\n', line);
	string header = line.substr(0, index);
	return header.size() + 1;
}

bool Handler::send_response(int client, string response) {
	// prepare to send response
	const char* ptr = response.c_str();
	int nleft = response.length();
	int nwritten;
	// loop to be sure it is all sent
	while (nleft) {
		if ((nwritten = send(client, ptr, nleft, 0)) < 0) {
			if (errno == EINTR) {
				// the socket call was interrupted -- try again
				continue;
			} else {
				// an error occurred, so break out
				perror("write");
				return false;
			}
		} else if (nwritten == 0) {
			// the socket is closed
			return false;
		}
		nleft -= nwritten;
		ptr += nwritten;
	}
	return true;
}
