CXX=			g++ $(CCFLAGS)

SERVERMAIN	=	serverMain.o Server.o Message.o
CLIENTMAIN	=	clientMain.o Client.o
SERVER		=	Server.o
CLIENT		= 	Client.o
MESSAGE		=	Message.o

OBJS 		=	$(SERVERMAIN) $(CLIENTMAIN) 

LIBS=

CCFLAGS= -g

all:	msgd msg

msgd:$(SERVERMAIN) 
	$(CXX) -o msgd $(SERVERMAIN) $(LIBS)

msg:$(CLIENTMAIN)
	$(CXX) -o msg $(CLIENTMAIN)  $(LIBS)

clean:
	rm -f $(OBJS) $(OBJS:.o=.d)

realclean:
	rm -f $(OBJS) $(OBJS:.o=.d) msgd msg


# These lines ensure that dependencies are handled automatically.
%.d:	%.cpp
	$(SHELL) -ec '$(CC) -M $(CPPFLAGS) $< \
		| sed '\''s/\($*\)\.o[ :]*/\1.o $@ : /g'\'' > $@; \
		[ -s $@ ] || rm -f $@'

include $(OBJS:.o=.d)
