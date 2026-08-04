CC = gcc
CFLAGS = -O3 -Wall
SRC = src/c_aggregator/aggregator.c
TARGET_WIN = src/c_aggregator/aggregator.exe
TARGET_NIX = src/c_aggregator/aggregator

all: build

build:
ifeq ($(OS),Windows_NT)
	$(CC) $(CFLAGS) $(SRC) -o $(TARGET_WIN)
else
	$(CC) $(CFLAGS) $(SRC) -o $(TARGET_NIX)
endif

clean:
	rm -f $(TARGET_WIN) $(TARGET_NIX)
