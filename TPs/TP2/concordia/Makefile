CC=gcc
CFLAGS=-I.

all: concordia_daemon concordia_client

concordia_daemon: concordia_daemon.o
	$(CC) -o concordia_daemon concordia_daemon.o $(CFLAGS)

concordia_client: concordia_client.o
	$(CC) -o concordia_client concordia_client.o $(CFLAGS)

install:
	cp concordia_daemon /usr/local/bin
	cp concordia_client /usr/local/bin
	cp concordia.service /etc/systemd/system/
	systemctl daemon-reload
	systemctl enable concordia.service
	systemctl start concordia.service

clean:
	rm -f *.o concordia_daemon concordia_client

.PHONY: all install clean
