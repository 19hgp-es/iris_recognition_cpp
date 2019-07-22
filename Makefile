all: iris test

CC = g++

OBJ = 

VERSION = --std=c++11

CFLAGS = -I `pkg-config --cflags opencv4`

CLIBS = -L `pkg-config --libs opencv4`

test: DisplayImage.cpp
		$(CC) -o DisplayImage DisplayImage.cpp $(VERSION) $(CFLAGS) $(CLIBS)

iris: iris_recognition.cpp
		$(CC) -o iris_recognition iris_recognition.cpp $(VERSION) $(CFLAGS) $(CLIBS)

clean:
		rm DisplayImage
		rm iris_recognition

