import socket
import datetime
import os
import pickle

from time import sleep
from collections import deque


# Named constants go here
RECEIVE_SIZE = 4096
CHECKSUM = "f5cb05cce8c03b4c82efc1dba3ace46d613474675ac8dde3a9d083869c1e8577"

# Global variables go here
word_list = []

# Center the player input
def centered_input(current_word):
	width, height = os.get_terminal_size()
	remainder = len(current_word) % 2
	mid_char = None
	
	# Calculations according to the length of the current word so later the centered input positions itself correctly
	if remainder == 1:
		mid_char = (len(current_word) // 2)
	else:
		mid_char = (len(current_word) // 2) - 1
		
	# Moves the input to the center, with its width spacing measured so it looks nice (refer to the mid_char calculation)
	user_input = input(f"\033[{height // 2};{(width // 2) - mid_char}H")

	return user_input

# For centered printing
def printC(text):
	width, height = os.get_terminal_size()
	print(text.center(width))

# To clear the terminal
def clear_terminal():
	width, height = os.get_terminal_size()
	if (os.name == "posix"):
		os.system('clear')
	else:
		os.system('cls')


def print_leaderboard(Ldb):
	clear_terminal()

	print("\n")
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
	printC("CTRL+C to quit")
	print("")
	printC("-" * 30)


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

	print("\n")
	printC("=====> G A E M <=====")
	print(" ")
	printC("Welcome to GAEM, a multiplayer speed typing game where the fastest and most accurate player comes up on top.")
	printC("To exit press FF.")
	printC("It is recommended for you to zoom into your console for better visibility.")
	print(" ")
	printC("-" * 30)
	
	server.sendall("VERIFY".encode())
	verifier = server.recv(RECEIVE_SIZE).decode()

	if verifier != CHECKSUM:
		print("Please connect to a valid game server")
		exit()
	
	# name.txt
	try:
		with open("name.txt", "r") as file:
			saved_name = file.readlines()
			print(f"Saved name detected\nWelcome back {saved_name[0]}, to continue press Enter without typing anything.\nEnter a new one if you want a new name :D\n")

	except FileNotFoundError:
			saved_name = None


	while True:
		name_request = str(input("Enter your name: ")).strip()

		if name_request == "":
			if saved_name != None:
				name_request = saved_name[0]
			else:
				print("No saved name detected, please enter your name again")
				continue

		if not name_request.isalnum():
			print("Name must be alphanumeric, please try again")
			continue

		if len(name_request) > 16:
			print("Name must be less than 16 characters, please try again")
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
			
			with open("name.txt", "w") as file:
				file.write(name_request)
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
		
		global word_list
		word_list = pickle.loads(word_list_bytes)

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
		print("\n")
		printC("=====> G A E M <=====")
		print(" ")
		printC("TYPE THE WORD BELOW CORRECTLY AS QUICK AS POSSIBLE!")
		printC("-" * 30)
		printC(word_list[n]) # Show word to print
		print("\n" * 2)

		width, height = os.get_terminal_size()
		print("\n" * (height // 3))

		print("\n" * 5)
		print('Next: \n', end='') # Show next 5 words

		for word in next_list:
			print(word, end='')
			if word != next_list[-1]:
				print(', ', end='')
		print("\n")
		print("FF to forfeit :(")
		print("\n")
		printC("-" * 30)

		# Create a list with the next 5 words
		if n < (len(word_list) - 6):
			next_list.popleft()
			next_list.append(word_list[n+6])
		
		elif len(next_list) != 0:
			next_list.popleft()
		
		player_input = centered_input(word_list[n])  # Get centered input
		time_start = datetime.datetime.now()
		player_input = player_input.strip()  # Clean up the input
		time_end = datetime.datetime.now()

		if player_input == word_list[n]:
			delta = int(((time_end - time_start).total_seconds())*1000)
		elif player_input == "FF": # FF to forfeit
			server.send("FF".encode())
			server.close()
			exit()
		else:
			delta = -1
		
		clear_terminal()
		
		delta_byte = pickle.dumps(delta)
		server.sendall(delta_byte)
		sleep(0.1) # This delay is here to stop the server from being overwhelmed with packets
		
	# Show leaderboard after player completes the list
	while True:
		server.send("REQUEST_LEADERBOARD".encode())
		Leaderboard = server.recv(RECEIVE_SIZE)

		Ldb = pickle.loads(Leaderboard)
		print_leaderboard(Ldb)
		sleep(10) # Don't spam the server for leaderboard requests

# Calls the main function
main()
