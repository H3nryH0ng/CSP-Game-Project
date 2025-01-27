import socket
from time import sleep
import pickle
from collections import deque
import datetime
import os


# Named constants go here
RECEIVE_SIZE = 4096
CHECKSUM = "f5cb05cce8c03b4c82efc1dba3ace46d613474675ac8dde3a9d083869c1e8577"
DEBUG = 1

# Global variables go here
word_list = []

width, height = os.get_terminal_size()

# Centered printing
def printC(text):
	print(text.center(width))

# To clear the terminal
def clear_terminal():
	if (os.name == "posix"):
		os.system('clear')
	else:
		os.system('cls')


def print_leaderboard(Ldb):
	#width, height = os.get_terminal_size()
	
	clear_terminal()
	
	for i in range(height // 2 - 4):
		print("")
		
	printC("=====> G A E M <=====")
	print("")
	printC("LEADERBOARD")
	print("")
	printC("(Player : Score)")
	print("")

	length = len(Ldb)

	if length <= 5:
		for name, score in Ldb:
			printC(f"{name} : {score}")
			print("")
			
	else:
		for i in range(5):
			name, score = Ldb[i]
			printC(f"{name} : {score}")
			print("")
		
		print("")
		rank, score = Ldb[5]
		printC(f"You placed {rank} with a score of {score}")
		print("Press CTRL+C to quit")


def main():
	
	# Prompt the user for the address of the server instance to connect to until connection is successful
	while True:
		try:
			address = input("Enter server address: ")
			port = int(input("Enter server port number [1024-65353]: "))

			if port < 1024 or port > 65353:
				raise Exception("Invalid port number")
			
			# Creates a socket, server, which uses AF_INET (Internet Protocol), and SOCK_STREAM (TCP)
			server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			# Connect to address and port given
			server.connect((address, port))
		
		except Exception as e:
			print(f"{e}")
			exit()
		
		else:
			clear_terminal()
			break

	# Should we do a help cmd to guide the user? ~ Francis
	
	printC("=====> G A E M <=====")
	print(" ")
	printC("Welcome to GAEM, a multiplayer speed typing game where the fastest and most accurate player comes up on top.")
	printC("To exit press CTRL + C.")
	printC("It is recommended for you to zoom into your console for better visibility.")
	print(" ")
	print("-".center(width, "-"))
	
	server.sendall("VERIFY".encode())
	verifier = server.recv(RECEIVE_SIZE).decode()

	if verifier != CHECKSUM:
		print("Please connect to a valid game server")
		exit()

	while True:
		name_request = str(input("Enter your name: ")).strip()

		if not name_request.isalnum():
			print("Name must be alphanumeric")
			continue

		if len(name_request) > 16:
			print("Name must be less than 16 characters")
			continue

		server.sendall("SET_NAME".encode())
		server.sendall(f"{name_request}".encode())

		print(f"Requesting name set to {name_request}")

		# Waiting for server to respond
		server_msg = server.recv(RECEIVE_SIZE).decode()

		# Name request is taken
		if server_msg == "NAME_UNAVAILABLE":
			print("Name taken, please use another name")

		# Name request is okay
		elif server_msg == "NAME_OK":
			print(f"Name set to {name_request}")
			break


	# Don't start the game and show a waiting prompt until all players are connected
	server.sendall("READY".encode())
	print("Waiting for Players")

	starter = server.recv(RECEIVE_SIZE).decode()
	
	if starter == "START":
		clear_terminal()
		server.sendall("REQUEST_TEMP_RECEIVE_SIZE".encode())


	response = server.recv(RECEIVE_SIZE).decode()
	if response == "TEMP_RECEIVE_SIZE":
		temp_receive_size_bytes = server.recv(RECEIVE_SIZE)
		temp_receive_size = pickle.loads(temp_receive_size_bytes)

	server.sendall("REQUEST_WORD_PAYLOAD".encode())
	
	response = server.recv(RECEIVE_SIZE).decode()
	if response == "WORD_PAYLOAD":
		word_list_bytes = server.recv(temp_receive_size)
		
		if DEBUG:
			print(word_list_bytes)

		global word_list
		word_list = pickle.loads(word_list_bytes)

		if DEBUG:
			print(word_list)


	# Actually implement the game itself, once the game starts we need to get data from the server, parse it, get input from the user, send it to the server
	# Plan to make this a func?
	next_list = deque([])

	
	if len(word_list) == 0:
		print("No word list received, please check on server side")
		exit()

	if len(word_list) > 5:
		for i in range(1,6):
			next_list.append(word_list[i])
	else:
		next_list = deque(word_list)
		next_list.popleft()
		
	# Game start here
	for n in range(len(word_list)):
		server.sendall("CLIENT_PACKET".encode())
		printC("=====> G A E M <=====")
		print(" ")
		printC(word_list[n]) # Show word to print
		print(" ")
		
		print('Next: \n', end='') # Show next 5 words

		for word in next_list:
			print(word, end='')
			if word != next_list[-1]:
				print(', ', end='')
		print(" ")
		print(" ")
		print("-".center(width, "-"))

		# Create a list with the next 5 words
		if n < (len(word_list) - 6):
			next_list.popleft()
			next_list.append(word_list[n+6])
		
		elif len(next_list) != 0:
			next_list.popleft()
		
		time_start = datetime.datetime.now()
		player_input = input().strip()
		time_end = datetime.datetime.now()

		if player_input == word_list[n]:
			delta = int(((time_end - time_start).total_seconds())*1000)
			clear_terminal()
		else:
			delta = -1
			clear_terminal()

		if DEBUG:
			print(type(delta), delta)
		
		delta_byte = pickle.dumps(delta)
		server.sendall(delta_byte)
		sleep(0.1) # This delay is here to stop the server from being overwhelmed with packets
		
		print('')


	# Show leaderboard after player completes the list
	while True:
		server.send("REQUEST_LEADERBOARD".encode())
		Leaderboard = server.recv(RECEIVE_SIZE)

		if DEBUG:
			print(Leaderboard)
		
		Ldb = pickle.loads(Leaderboard)
		print_leaderboard(Ldb)
		sleep(10)

# Calls the main function
main()
