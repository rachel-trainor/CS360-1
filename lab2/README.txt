Synchronization is used:
	In my Buffer class with append and take which add and remove clients from a queue.

	And in my Handler whenever I read from or write to my map which maps users to a vector of messages. Specifically I use synchronization in list(), get(), reset(), addToMap(), listResponse() and getResponse() which are all in Handler.cpp
