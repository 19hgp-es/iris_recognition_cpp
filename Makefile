
CC = g++

OBJ = 

VERSION = --std=c++11

CFLAGS = -I `pkg-config --cflags opencv4`

CLIBS = -L `pkg-config --libs opencv4`

test: iris_recognition.cpp
	$(CC) -o DisplayImage iris_recognition.cpp $(VERSION) $(CFLAGS) $(CLIBS)

clean:
	rm DisplayImage

all: test
