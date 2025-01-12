import threading
import socket
import linecache
import pickle

from random import randint
from time import sleep
from sys import getsizeof


# Constant configuration variables go here, use ALL CAPS to indicate constant
MAX_CONNECTIONS = 1
PORT = 6969
DICTIONARY_PATH = "test.txt"
WORD_SET_LENGTH = 10


# Named constants go here
RECEIVE_SIZE = 4096
CHECKSUM = "f5cb05cce8c03b4c82efc1dba3ace46d613474675ac8dde3a9d083869c1e8577"
DEBUG = 1


# Global variables go here
names = set()
lock = threading.Lock()
threads = []
players = []
word_list = []
word_list_bytes = b""
word_list_bytes_size = 0
ready = 0


class player():
	def __init__(self):
		self.username = ""
		self.current_combo = 0
		self.score = 0
		self.placement = -1
	
	def add_time(self, time_delta):
		self.total_time += time_delta
	
	def set_name(self, requested_username):
		self.username = requested_username
	
	def add_correct(self):
		self.num_correct += 1

	def add_combo(self):
		self.current_combo += 1

	def reset_combo(self):
		self.current_combo = 0

	def calculate_score(self, time_delta):
		if time_delta < 1500:
			self.score += (1100 - (time_delta * 2 // 3)) + self.current_combo * 300
		else:
			self.score += 100 + self.current_combo * 300


def gen_leaderboard():
	result = []
	
	with lock:
		current_leaderboard = sorted(players, key = lambda player: player.score, reversed = True)

	if MAX_CONNECTIONS < 5:
		for player in current_leaderboard:
			result.append((player.username, player.score))
	else:
		for i in range(5):
			result.append((current_leaderboard[i].username, current_leaderboard[i].score))
		# Imma add another function to sent the player own placement if they are not top 10 ~ Francis	
	
	if DEBUG:
		print(result)
	
	return result


'''
Target function to handle each client in a separate thread to avoid blocking functions like socket.recv() from blocking the main thread, this allows us to handle multiple clients
client is a client socket to the client, which is what we use to send data to it
address contains the ip address and the port of the client
'''
def handle_connection(client, address, player_object):
	# For debugging purposes only
	if DEBUG:
		print(f"{client}")
		print(f"{address}")
	
	# Try to execute the code inside the block, catch _ANY_ exception, aka errors, print them to the console, and exit
	try:
		# Infinite loop to keep checking, getting, and sending new data
		while True:
			'''
			message contains what we received in a string
			client.recv() recieves RAW BYTES transmitted from the client
			.decode is a method we use to decode the raw bytes to a string
			socket.recv is a blocking call meaning execution will stop here until there's more data to read
			'''
			message = client.recv(RECEIVE_SIZE).decode()

			'''
			NOTE: ALL strings sent should be converted to UPPERCASE before sending to avoid "apple" and "Apple" being different, 
			this should only apply to protocol keywords, the contents of messages sent in two parts should remain case sensitive/
			'''
			
			# if message is FF, it means the client surrendered
			if message == "FF":
				print(f"Client {address} surrendered")
				
				# Close the connection
				client.close()
				
				# break out of the infinite loop
				break
			
			# if message received is empty, client has disconnected
			elif message == "":
				print(f"Client {address} disconnected")
				client.close()
				break
			
			elif message == "CLIENT_PACKET":
				game_packet = client.recv(RECEIVE_SIZE).decode()
				
				
				if DEBUG:
					print(f"{game_packet[0]}\n{game_packet[1]}")
				
				if int(game_packet[1]):
					player_object.add_time(game_packet[0])
					player_object.add_correct()

			elif message == "END":
				leaderboard = gen_leaderboard()
				leaderboard_bytes = pickle.dumps(leaderboard)
				
				if DEBUG:
					print(leaderboard_bytes)

				client.send(leaderboard_bytes)

			elif message == "VERIFY":
				client.send(CHECKSUM.encode())
			
			elif message == "SET_NAME":
				requested_name = client.recv(RECEIVE_SIZE).decode()
				print(f"Client {address} requested name {requested_name}.")

				with lock:
					if requested_name in names:
						client.send("NAME_UNAVAILABLE".encode())
					else:
						client.send("NAME_OK".encode())
						names.add(requested_name)
				
				player_object.set_name(requested_name)
			
			elif message == "REQUEST_WORD_PAYLOAD":
				print(f"{address} requested word payload")

				client.send("TEMP_SET_RECEIVE_SIZE")
				client.send(pickle.dumps(word_list_bytes_size))

				if DEBUG:
					print(f"{word_list}")
					print(type(word_list_bytes))
					print(word_list_bytes)
				
				client.send("WORD_PAYLOAD".encode())
				client.send(word_list_bytes)
			
			elif message == "READY":
				with lock:
					global ready
					ready += 1
				
				# After the above the server would be waiting for the client's message by calling recv originally, took me hours to figure it out.
				while ready != MAX_CONNECTIONS:
					sleep(0.1)

				client.send("START".encode())
			else:
				print(f"{message}")
				'''
				example of how to send data through a socket, "men" is a python string object, not just the characters m,e, and n
				str.encode() encodes the string in UTF-8 and returns the byte representation of it back which is what we want to send
				client.send("men") will try to send a python object
				same goes for receiving messages as well
				'''
				client.send("men".upper().encode())
			
			if DEBUG:
				print(f"Connection thread handler for client {address} alive.")

	except Exception as e:
		print(f"Caught: {e}")
		client.close()


def count_lines():
	lines = 0
	
	try:
		with open(DICTIONARY_PATH, "r") as dictionary:
			for line in dictionary:
				lines += 1

				if DEBUG:
					print(lines, line, end="")
	except FileNotFoundError:
		print("DICTIONARY_PATH does not point to an existing file. Try changing it.")
		exit()
	else:
		print(f"Dictionary file {DICTIONARY_PATH} found with {lines} lines")
	
	return lines


def generate_word_list(lines):
	result = []
	
	while len(result) < WORD_SET_LENGTH:
		random_number = randint(1, lines)

		# linecache has to be used to get a random line from a file, inclusive of the \n character, [:-1] slices the trailing \n off
		word = linecache.getline(DICTIONARY_PATH, random_number)[:-1]

		if random_number % 3 and random_number % 5:
			result.append(word.upper())
		elif random_number % 13 == 0:
			result.append(word.capitalize())
		else:
			result.append(word)

	return result


def pickle_list(list_object):
	result = pickle.dumps(list_object)
	size = getsizeof(result) + 16
	
	if DEBUG:
		print(result, size)
	
	return (result, size)


#Entry point here
def main():
	if PORT < 1024 or PORT > 65353:
		print("Invalid port number")
		exit()

	if type(MAX_CONNECTIONS) != int or type(PORT) != int or type(DICTIONARY_PATH) != str or type(WORD_SET_LENGTH) != int:
		print("MAX_CONNECTIONS, PORT, and WORD_SET_LENGTH must be of type int.\n DICTIONARY_PATH must be of type str.")
		exit()

	lines = count_lines()
	
	if WORD_SET_LENGTH > lines:
		print("WORD_SET_LENGTH greater than the size of the dictionary file provided, try lowering WORD_SET_LENGTH")
		exit()
	
	global word_list
	word_list = generate_word_list(lines)
	print(f"Word set of length {WORD_SET_LENGTH} successfully generated")
	
	if DEBUG:
		print(f"{word_list}")
	
	global word_list_bytes
	global word_list_bytes_size
	word_list_bytes, word_list_bytes_size = pickle_list(word_list)

	try:
		'''
		Create a socket object, sock, which is a bytestream of RAW data.
		AF_INET tells the socket to use Internet Protocol
		SOCK_STREAM tells the socket to use TCP
		'''
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		
		#Binds sock to all interfaces and port specified in PORT
		sock.bind(("0.0.0.0", PORT))
		
		# Start listening on socket sock, with a limit on the maximum number of connections specified in MAX_CONNECTIONS
		sock.listen(MAX_CONNECTIONS)
		print(f"Listening on port {PORT}")
		
		
		# Keep accepting connections until MAX_CONNECTIONS is reached
		connected = 0
		while connected < MAX_CONNECTIONS:
			# socket.accept() returns two things, the client socket, and the client IP address
			client, address = sock.accept()
			print(f"Accepted connection from {address}")
			
			new_player_object = player()
			players.append(new_player_object)
			
			# Creates a new thread and calls handle_connection() with arguements client, address we got from socket.accept()
			# This is not accurate at all but just think of it as assigning one core out of many from your CPU to execute this function
			new_thread = threading.Thread(target = handle_connection, args=(client, address, new_player_object))
			
			# For each thread we create, add them to the list threads
			threads.append(new_thread)
			new_thread.start()
			connected += 1
			print(f"{MAX_CONNECTIONS - connected} players remaining before game starts")
		
		print("MAX_CONNECTIONS reached")
		
		while ready < MAX_CONNECTIONS:
			sleep(0.1)

		print("All players ready, starting game.")
		
		# Wait for all threads to complete
		for thread in threads:
			thread.join()
		
	except Exception as e:
		print(f"Caught: {e}")
		exit()

# calls the main function
main()
