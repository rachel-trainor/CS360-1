#include "Server.h"

Server::Server(int port) {
	// setup variables
	port_ = port;
	buflen_ = 1024;
	buf_ = new char[buflen_ + 1];

	// create and run the server
	create();
	serve();
}

Server::Server(int port, bool debug) {
	// setup variables
	port_ = port;
	this->debug = debug;
	buflen_ = 1024;
	buf_ = new char[buflen_ + 1];

	// create and run the server
	create();
	serve();
}

Server::~Server() {
	delete buf_;
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

	// accept clients
	while ((client = accept(server_, (struct sockaddr *) &client_addr,
			&clientlen)) > 0) {

		handle(client);
		close(client);
	}

	close(server_);

}

void Server::handle(int client) {
	// loop to handle all requests
	while (1) {
		// get a request
		string request = get_request(client);
		if(debug){
			cout << "server received this request: " << request << endl;
		}

		string response = parseRequest(request);

		if(debug) {
			cout << "Server response: " << response << endl;
		}

		// break if client is done or an error occurred
		if (request.empty())
			break;
		// send response
		bool success = send_response(client, response);
		// break if an error occurred
		if (not success)
			break;
	}
}

string Server::parseRequest(string line) {
	int index = readToSentinel(' ', line);
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

int Server::readToSentinel(char sentinel, string line) {
	string toReturn = "";
	int i = 0;

	for (i = 0; i < line.size(); i++) {
		if (line.at(i) != sentinel) {
			toReturn += line.at(i);
		} else {
			break;
		}
	}
	return i;
}

string Server::isSpecial(string value, string theRest) {

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

string Server::put(string line) {

	int index = readToSentinel(' ', line);
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

string Server::list(string line) {

	int index = readToSentinel('\n', line);
	string user = line.substr(0, index);

	if (contains(user)) {
		string lResponse = listResponse(user);
		return lResponse;
	} else {
		string error = "error user doesn't exist so he has no messages to list\n";
		return error;
	}
}

string Server::get(string line) {

	int index = readToSentinel(' ', line);
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

	if (contains(user)) {
		string gResponse = getResponse(user, num);
		return gResponse;
	} else {
		string error = "error user doesn't exist so can't get message\n";
		return error;
	}

}

string Server::reset() {
	messageList.clear();
	return "OK\n";
}

string Server::addToMap(Message m) {
	map<string, vector<Message> >::iterator it;
	string name = m.getUser();

	if (contains(name)) {
		for (it = messageList.begin(); it != messageList.end(); ++it) {
			if (it->first == name) {
				it->second.push_back(m);
				break;
			} else {
				return "error in addToMap\n";
			}
		}
	} else {
		vector<Message> tempVector;
		tempVector.push_back(m);
		messageList.insert(pair<string, vector<Message> >(name, tempVector));
	}

	return "OK\n";
}

bool Server::contains(string name) {
	map<string, vector<Message> >::iterator it;

	for (it = messageList.begin(); it != messageList.end(); ++it) {
		if (it->first == name) {
			return true;
		}
	}

	return false;
}

string Server::listResponse(string name) {
	map<string, vector<Message> >::iterator it;
	string toReturn = "list ";

	for (it = messageList.begin(); it != messageList.end(); ++it) {
		if (it->first == name) {
			toReturn += intToString(it->second.size());
			toReturn += "\n";
			for (size_t i = 0; i < it->second.size(); i++) {
				toReturn += intToString(i+1);
				toReturn += " ";
				toReturn += it->second.at(i).getSubject();
				toReturn += "\n";
			}
		}
	}

	return toReturn;
}

string Server::getResponse(string name, int index) {
	map<string, vector<Message> >::iterator it;
	string toReturn = "";

	for (it = messageList.begin(); it != messageList.end(); ++it) {
		if (it->first == name) {
			if (it->second.size() > index - 1) {
				toReturn = it->second.at(index - 1).toString();
				//toReturn += "\n";
				return toReturn;
			} else {
				toReturn = "error no message at that index\n";
			}
		}
	}

	return toReturn;
}

string Server::printMap() {
	map<string, vector<Message> >::iterator it;
	string toReturn = intToString(messageList.size());
	toReturn += "\n";

	for(it = messageList.begin(); it != messageList.end(); ++it) {
		toReturn += it->first;
		toReturn += "\n";
		toReturn += "\t";

		for(size_t i = 0; i < it->second.size(); i++) {
			toReturn += it->second.at(i).toString();
		}
	}

	return toReturn;
}

string Server::intToString(int num) {
	stringstream myStringStream;
	string toReturn;
	myStringStream << num;
	toReturn = myStringStream.str();

	return toReturn;
}

string Server::get_request(int client) {
	string request = "";
	int nread = -1;
	// read until we get a newline
	while (request.find("\n") == string::npos) {
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
	}
	// a better server would cut off anything after the newline and
	// save it in a cache

	int mLength = determineLength(request);
	int headerLength = deterHeaderLength(request);
	int difference = 0;

	if(mLength > 0) {
		if(mLength + headerLength > 1024) {
			difference = (mLength + headerLength) - nread;//1024;

			while(difference > 0) {
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

	if(debug) {
		cout<<"~~~"<<request<<endl;
	}
	return request;
}

int Server::determineLength(string line) {
	int index = readToSentinel(' ', line);
	string command = line.substr(0, index);

	if(command == "put") {

		if(line.size() > index + 1) {
			line = line.substr(index+1);
		} else {
			if(debug) {
				cout << "error in determinLength()" << endl;
			}
		}

		int index = readToSentinel(' ', line);
		string user = line.substr(0, index);

		if (line.size() > index + 1) {
			line = line.substr(index + 1);
		} else {
			if(debug) {
				cout << "error - Not Enough Parameters -\n" << endl;
			}
		}

		index = readToSentinel(' ', line);
		string subject = line.substr(0, index);

		if (line.size() > index + 1) {
			line = line.substr(index + 1);
		} else {
			if(debug) {
				cout << "error - Not Enough Parameters -\n" << endl;
			}
		}

		index = readToSentinel('\n', line);
		string length = line.substr(0, index);

		if (line.size() > index + 1) {
			line = line.substr(index + 1);
		} else {
			if(debug) {
				cout << "error - Not Enough Parameters -\n" << endl;
			}
		}
		string message = line;
		return atoi(length.c_str());

	} else {
		return -1;
	}
}

int Server::deterHeaderLength(string line) {
	int index = readToSentinel('\n', line);
	string header = line.substr(0, index);
	return header.size() + 1;
}

bool Server::send_response(int client, string response) {
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
