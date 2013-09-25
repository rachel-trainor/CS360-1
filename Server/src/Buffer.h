/*
 * Buffer.h
 *
 *  Created on: Sep 25, 2013
 *      Author: adamjc
 */

#pragma once
#include <pthread.h>
#include <queue>
#include <vector>
#include <semaphore.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <iostream>

using namespace std;

class Buffer {
public:
	Buffer();
	virtual ~Buffer();

	void append(int);
	int take();

private:

	//queue<pthread_t*> buff;
	queue<int> buff; //queue of clients
	sem_t lock,numClients,emptySpots;
};

