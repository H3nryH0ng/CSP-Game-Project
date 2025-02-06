import threading
import socket
import linecache
import pickle

from random import randint
from time import sleep
from sys import getsizeof


# Constant configuration variables
MAX_CONNECTIONS = 1
PORT = 1234
DICTIONARY_PATH = "default.txt"
WORD_SET_LENGTH = 10


# Named constants
CHECKSUM = "f5cb05cce8c03b4c82efc1dba3ace46d613474675ac8dde3a9d083869c1e8577\n"

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

	return result


'''
Target function to handle each client in a separate thread
client is a client socket to the client, which is what we use to send data to it
address contains the ip address and the port of the client
'''
def handle_connection(client, clientFO, address, player_object):
	while True:
		try:
			message = clientFO.readline().decode()
		except Exception as e:
			print(f"Connection handler for {address} caught {e}. Disconnecting.")
			clientFO.close()
			client.close()
			break
		
		if message == "FF\n":
			print(f"Client {address} surrendered")
			clientFO.close()
			client.close()
			break
		
		# if message received is empty, client has disconnected
		elif message == "":
			print(f"Client {address} disconnected")
			clientFO.close()
			client.close()
			break
		
		elif message == "CLIENT_PACKET\n":
			try:
				delta = pickle.load(clientFO)
			except Exception:
				print(f"Connection handler for {address} got faulty data. Ignoring")
				continue
			
			if delta == -1:
				player_object.reset_combo()
			else:
				player_object.add_combo()
				player_object.calculate_score(delta)

		elif message == "REQUEST_LEADERBOARD\n":
			leaderboard = gen_leaderboard(player_object)
			
			pickle.dump(leaderboard, clientFO)
			clientFO.flush()

		elif message == "VERIFY\n":
			clientFO.write(CHECKSUM.encode())
			clientFO.flush()
		
		elif message == "SET_NAME\n":
			# [:-1] gets rid of trailing \n
			requested_name = clientFO.readline().decode()[:-1]
			print(f"Client {address} requested name {requested_name}.")

			with lock:
				if requested_name in names:
					clientFO.write("NAME_UNAVAILABLE\n".encode())
				else:
					clientFO.write("NAME_OK\n".encode())
					names.add(requested_name)
				clientFO.flush()
			player_object.set_name(requested_name)
		
		elif message == "REQUEST_WORD_PAYLOAD\n":
			print(f"{address} requested word payload")

			clientFO.write("WORD_PAYLOAD\n".encode())
			clientFO.flush()

			pickle.dump(word_list, clientFO)
			clientFO.flush()
		
		elif message == "READY\n":
			with lock:
				global ready
				ready += 1
			
			while ready != MAX_CONNECTIONS:
				sleep(0.1)

			clientFO.write("START\n".encode())
			clientFO.flush()
		else:
			print(f"Got unknown message {message} from {address}. Ignoring")

def count_lines():
	lines = 0
	
	try:
		with open(DICTIONARY_PATH, "r") as dictionary:
			for line in dictionary:
				lines += 1
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


def main():
	if type(MAX_CONNECTIONS) != int or type(PORT) != int or type(DICTIONARY_PATH) != str or type(WORD_SET_LENGTH) != int:
		print("MAX_CONNECTIONS, PORT, and WORD_SET_LENGTH must be of type int.\n DICTIONARY_PATH must be of type str.")
		exit()

	if PORT < 1024 or PORT > 65353 or MAX_CONNECTIONS <= 0:
		print("Invalid port number or MAX_CONNECTIONS less than or equal to 0")
		exit()
	
	lines = count_lines()
	
	if WORD_SET_LENGTH > lines:
		print("WORD_SET_LENGTH greater than the size of the dictionary file provided, try lowering WORD_SET_LENGTH")
		exit()
	
	global word_list
	word_list = generate_word_list(lines)
	print(f"Word set of length {WORD_SET_LENGTH} successfully generated")
	
	'''
	Create a socket object, sock, which is a bytestream of RAW data.
	AF_INET tells the socket to use Internet Protocol
	SOCK_STREAM tells the socket to use TCP
	'''
	try:
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		
		#Binds sock to all interfaces and port specified in PORT
		sock.bind(("0.0.0.0", PORT))
		
		# Start listening on socket sock, with a limit on the maximum number of connections specified in MAX_CONNECTIONS
		sock.listen(MAX_CONNECTIONS)
	except Exception as e:
		print(f"main() caught {e}. Terminating...")
		sock.close()
		exit()

	print(f"Listening on port {PORT}")

	connected = 0
	while connected < MAX_CONNECTIONS:
		# socket.accept() returns two things, the client socket, and the client IP address
		client, address = sock.accept()
		print(f"Accepted connection from {address}")
		
		clientFO = client.makefile("rwb", buffering = 0)

		new_player_object = player()
		players.append(new_player_object)
		
		# Creates a new thread and calls handle_connection() with arguements client, address we got from socket.accept()
		new_thread = threading.Thread(target = handle_connection, args=(client, clientFO, address, new_player_object))
		
		# For each thread we create, add them to the list threads
		threads.append(new_thread)
		new_thread.start()
		connected += 1
		print(f"{MAX_CONNECTIONS - connected} players remaining before game starts")
	
	print("MAX_CONNECTIONS reached")
	
	while ready < MAX_CONNECTIONS:
		sleep(0.1)

	print("All players ready, starting game.")
	
	for thread in threads:
		thread.join()
	
	sock.close()


# Calls the main function
while True:
	# Global variables
	names = set()
	lock = threading.Lock()
	threads = []
	players = []
	word_list = []
	ready = 0

	print("Starting new round. CTRL+C to quit.")
	try:
		main()
	
	except KeyboardInterrupt:
		print("KeyboardInterrupt detected. Terminating server.")
		exit()

