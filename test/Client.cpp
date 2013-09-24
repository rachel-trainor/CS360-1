#include "Client.h"

Client::Client(string host, int port) {
	// setup variables
	host_ = host;
	port_ = port;
	buflen_ = 1024;
	buf_ = new char[buflen_ + 1];

	// connect to the server and run echo program
	create();
	parseInput();
}

Client::Client(string host, int port, bool debug) {
	// setup variables
	host_ = host;
	port_ = port;
	this->debug = debug;
	buflen_ = 1024;
	buf_ = new char[buflen_ + 1];

	// connect to the server and run echo program
	create();
	parseInput();
}

Client::~Client() {
}

void Client::create() {
	struct sockaddr_in server_addr;

	// use DNS to get IP address
	struct hostent *hostEntry;
	hostEntry = gethostbyname(host_.c_str());
	if (!hostEntry) {
		cout << "No such host name: " << host_ << endl;
		exit(-1);
	}

	// setup socket address structure
	memset(&server_addr, 0, sizeof(server_addr));
	server_addr.sin_family = AF_INET;
	server_addr.sin_port = htons(port_);
	memcpy(&server_addr.sin_addr, hostEntry->h_addr_list[0],
			hostEntry->h_length);

	// create socket
	server_ = socket(PF_INET, SOCK_STREAM, 0);
	if (!server_) {
		perror("socket");
		exit(-1);
	}

	// connect to server
	if (connect(server_, (const struct sockaddr *) &server_addr,
			sizeof(server_addr)) < 0) {
		perror("connect");
		exit(-1);
	}
}

void Client::parseInput() {
	string line;
	char c;

	while (getline(cin, line)) {
		string subStr = line.substr(0, 5);
		string theRest = "";
		if (line.size() > 5) {
			theRest = line.substr(5);
		}

		if (isSpecial(subStr, theRest) < 0) {
			//not special
			cout << "% ";
		} else {
			//is special
			cout << "% ";
		}
	}
}

int Client::isSpecial(string value, string theRest) {

	if (value == "send ") {
		foundSend(theRest);
		return 0;
	} else if (value == "list ") {
		foundList(theRest);
		return 0;
	} else if (value == "read ") {
		foundRead(theRest);
		return 0;
	} else if (value == "quit") {
		quit();
		return 0;
	} else {
		cout << "- Command Not Recognized -" << endl;
		return -1;
	}
}

void Client::foundSend(string line) {

	int index = readToSentinel(' ', line);
	string user = line.substr(0, index);

	if (line.size() > index + 1) {
		line = line.substr(index + 1);
	} else {
		cout << "- Not Enough Parameters -" << endl;
		return;
	}

	index = readToSentinel('\n', line);
	string subject = line.substr(0, index);

	cout << "- Type your message. End with a blank line -" << endl;

	string message = getMessage();

	string request = "put ";
	request += user;
	request += " ";
	request += subject;
	request += " ";
	request += intToString(message.size());
	request += "\n";
	request += message;

	if(debug){
		cout << "Client is sending the message: " << request << endl;
	}

	bool success = send_request(request);
	if (not success) {
		cout << "send_request failed" << endl;
	}
	success = get_response();
	if (not success) {
		cout << "get_response failed" << endl;
	}

}

void Client::foundList(string line) {

	int index = readToSentinel('\n', line);
	string user = line.substr(0, index);

	string request = "list ";
	request += user;
	request += "\n";

	if(debug){
		cout << "Client is sending the message: " << request << endl;
	}

	bool success = send_request(request);
	if (not success) {
		cout << "send_request failed" << endl;
	}
	success = get_response();
	if (not success) {
		cout << "get_response failed" << endl;
	}
}

void Client::foundRead(string line) {

	int index = readToSentinel(' ', line);
	string user = line.substr(0, index);

	if (line.size() > index + 1) {
		line = line.substr(index + 1);
	} else {
		cout << "- Not Enough Parameters -" << endl;
		return;
	}

	index = readToSentinel('\n', line);
	string messageNum = line.substr(0, index);

	string request = "get ";
	request += user;
	request += " ";
	request += messageNum;
	request += "\n";

	if(debug){
		cout << "Client is sending the message: " << request << endl;
	}

	bool success = send_request(request);
	if (not success) {
		cout << "send_request failed" << endl;
	}
	success = get_response();
	if (not success) {
		cout << "get_response failed" << endl;
	}
}

void Client::quit() {
	exit(0);
}

int Client::readToSentinel(char sentinel, string line) {
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

string Client::getMessage() {
	string line = "";
	string message = "";
	while (getline(cin, line)) {
		if (line.size() > 0) {
			message += line;
			message += " ";
		} else {
			break;
		}
	}
	return message;
}

string Client::intToString(int num) {
	stringstream myStringStream;
	string toReturn;
	myStringStream << num;
	toReturn = myStringStream.str();

	return toReturn;
}

bool Client::send_request(string request) {
	// prepare to send request
	const char* ptr = request.c_str();
	int nleft = request.length();
	int nwritten;
	// loop to be sure it is all sent
	while (nleft) {
		if ((nwritten = send(server_, ptr, nleft, 0)) < 0) {
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

bool Client::get_response() {
	string response = "";
	// read until we get a newline
	while (response.find("\n") == string::npos) {
		int nread = recv(server_, buf_, 1024, 0);
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
		response.append(buf_, nread);
	}
	// a better client would cut off anything after the newline and
	// save it in a cache
	cout << response;
	return true;
}
