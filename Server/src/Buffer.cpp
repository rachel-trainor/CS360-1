/*
 * Buffer.cpp
 *
 *  Created on: Sep 25, 2013
 *      Author: adamjc
 */

#include "Buffer.h"

Buffer::Buffer() {
	sem_init(&lock,0,1);
	sem_init(&numClients,0,0);
	sem_init(&emptySpots,0,10); //sem_init(&emptySpots,0,buff.size());
}

Buffer::~Buffer() {
	// TODO Auto-generated destructor stub
}

//void Buffer::append(pthread_t* thread) {
//	sem_wait(&emptySpots);
//	sem_wait(&lock);
//
//	buff.push(thread);
//
//	sem_post(&lock);
//	sem_post(&numClients);
//}

void Buffer::append(int client) {
	sem_wait(&emptySpots);
	sem_wait(&lock);

	buff.push(client);

	sem_post(&lock);
	sem_post(&numClients);
}

int Buffer::take() {
	sem_wait(&numClients);
	sem_wait(&lock);

	int client = buff.front();
	buff.pop();

	sem_post(&lock);
	sem_post(&emptySpots);
	return client;
}

//pthread_t* Buffer::take() {
//	sem_wait(&numClients);
//	sem_wait(&lock);
//
//	pthread_t* thread = buff.front();
//	buff.pop();
//
//	sem_post(&lock);
//	sem_post(&emptySpots);
//	return thread;
//}

