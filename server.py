import threading
import socket
import linecache
import pickle

from random import randint
from time import sleep
from sys import getsizeof


# Constant configuration variables go here, use ALL CAPS to indicate constant
MAX_CONNECTIONS = 4
PORT = 6969
DICTIONARY_PATH = "test.txt"
WORD_SET_LENGTH = 5


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
word_list_bytes_size = int(0)
ready = 0


class player():
	def __init__(self):
		self.username = ""
		self.current_combo = 0
		self.score = 0
	
	def set_name(self, requested_username):
		self.username = requested_username
	
	def add_combo(self):
		self.current_combo += 1

	def reset_combo(self):
		self.current_combo = 0

	def calculate_score(self, time_delta):
		if time_delta < 1500:
			self.score += (1100 - (time_delta * 2 // 3)) + self.current_combo * 300
		else:
			self.score += 100 + self.current_combo * 300


def gen_leaderboard(player_object):
	result = []
	
	with lock:
		current_leaderboard = sorted(players, key = lambda player: player.score, reverse = True)

	if MAX_CONNECTIONS < 5:
		for player in current_leaderboard:
			result.append((player.username, player.score))
	else:
		for i in range(5):
			result.append((current_leaderboard[i].username, current_leaderboard[i].score))

		if player_object.username not in [name[0] for name in result]:
			result.append((current_leaderboard.index(player_object), player_object.username, player_object.score))

	if DEBUG:
		print(result)
	
	return result


'''
Target function to handle each client in a separate thread
client is a client socket to the client, which is what we use to send data to it
address contains the ip address and the port of the client
'''
def handle_connection(client, address, player_object):
	if DEBUG:
		print(f"{client}")
		print(f"{address}")
	
	
	try:
		while True:
			message = client.recv(RECEIVE_SIZE).decode()
			
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
				delta_bytes = client.recv(RECEIVE_SIZE)
				delta = pickle.loads(delta_bytes)
				
				if DEBUG:
					print(f"{delta}")
				
				if delta == -1:
					player_object.reset_combo()
				else:
					player_object.add_combo()
					player_object.calculate_score(delta)

				if DEBUG:
					print(player_object.score, player_object.username, player_object.current_combo)

			elif message == "REQUEST_LEADERBOARD":
				print(f"Client {address} requested leaderboard."

				leaderboard = gen_leaderboard(player_object)
				leaderboard_bytes = pickle.dumps(leaderboard)
				
				if DEBUG:
					print(leaderboard_bytes)

				client.sendall(leaderboard_bytes)

			elif message == "VERIFY":
				client.sendall(CHECKSUM.encode())
			
			elif message == "SET_NAME":
				requested_name = client.recv(RECEIVE_SIZE).decode()
				print(f"Client {address} requested name {requested_name}.")

				with lock:
					if requested_name in names:
						client.sendall("NAME_UNAVAILABLE".encode())
					else:
						client.sendall("NAME_OK".encode())
						names.add(requested_name)
				
				player_object.set_name(requested_name)
			
			elif message == "REQUEST_TEMP_RECEIVE_SIZE":
				client.sendall("TEMP_RECEIVE_SIZE".encode())
				client.sendall(pickle.dumps(word_list_bytes_size))

			elif message == "REQUEST_WORD_PAYLOAD":
				print(f"{address} requested word payload")

				if DEBUG:
					print(f"{word_list}")
					print(type(word_list_bytes))
					print(word_list_bytes)
				
				client.sendall("WORD_PAYLOAD".encode())
				client.sendall(word_list_bytes)
			
			elif message == "READY":
				with lock:
					global ready
					ready += 1
				
				# After the above the server would be waiting for the client's message by calling recv originally, took me hours to figure it out.
				while ready != MAX_CONNECTIONS:
					sleep(0.1)

				client.sendall("START".encode())
			else:
				print(f"Got unknown message {message} from {address}. Ignoring")

			if DEBUG:
				print(f"Connection thread handler for client {address} alive.")

	except Exception as e:
		print(f"Thread handler for client {address} caught {e}. Disconnected")
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
		
	
	except KeyboardInterrupt:
		print("KeyboardInterrupt detected. Terminating server.")
		sock.close()
		exit()

	except Exception as e:
		print(f"Caught: {e}")
	
	finally:
		for thread in threads:
			thread.join()
		
		sock.close()
		

# calls the main function
while True:
	names = set()
	lock = threading.Lock()
	threads = []
	players = []
	word_list = []
	word_list_bytes = b""
	word_list_bytes_size = int(0)
	ready = 0
	
	main()
