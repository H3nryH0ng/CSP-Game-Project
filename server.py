import threading
import socket
import linecache
from random import randint

# Constant configuration variables go here, use ALL CAPS to indicate constant
MAX_CONNECTIONS = 1
PORT = 6969
DICTIONARY_PATH = "test.txt"
WORD_SET_LENGTH = 100


# Named constants go here
RECEIVE_SIZE = 1024
CHECKSUM = "f5cb05cce8c03b4c82efc1dba3ace46d613474675ac8dde3a9d083869c1e8577"


# Global variables go here
names = set() 
lock = threading.Lock()
threads = []
players = []
word_set = set()
start = False


class player:
	def __init__(self):
		self.username = username
		self.num_correct = 0
		self.total_time = 0.0
	
	def add_time(self, time_delta):
		self.total_time += time_delta
	
	def set_name(self, username):
		self.username = username
	
	def add_correct():
		self.num_correct += 1


def gen_leaderboard():
	result = ""
	
	with lock:
		players = sorted(players, key = lambda player: player.num_correct / player.total_time, reversed = True)

	if MAX_CONNECTIONS < 5:
		for i in range(len(players)):
			result.join(f"{i}.\t {players[i].username\t\n}")
	else:
		for i in range(5):
			result.join(f"{i}.\t {players[i].username]\t\n}")
	
	return f"{{result}}"

'''
Target function to handle each client in a separate thread to avoid blocking functions like socket.recv() from blocking the main thread, this allows us to handle multiple clients
client is a client socket to the client, which is what we use to send data to it
address contains the ip address and the port of the client
'''
def handle_connection(client, address, player_object):
	# For debugging purposes only
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
				game_packet = client.recv(RECEIVE_SIZE).decode()[1:-1].split(',')
				'''
				game_packet is a string in the form {TIME_DELTA, CORRECT}
				doing [1:-1] returns a slice of the string from the first character to the last character and doing str.split(',') splits the string using "," as a delimiter
				game_packet[0] contains TIME_DELTA
				game_packet[1] contains CORRECT
				'''
				print(f"{game_packet[0]}\n{game_packet[1]}")
				
				if int(game_packet[1]):
					player_object.add_time(game_packet[0])
					player_object.add_correct()

			elif message == "END":
				players = sorted(players, key = lambda player: player.num_correct / player.total_time, reverse = True)
				leaderboard = gen_leaderboard()

				
				if MAX_CONNECTIONS < 5:
					for i in range(len(players)):
						leaderboard.add()


			elif message == "VERIFY":
				client.send(CHECKSUM.encode())
			
			elif message == "SET_NAME":
				requested_name = client.recv(RECIEVE_SIZE).decode()[1:-1]
				
				with lock:
					if requested_name in names:
						client.send("NAME_UNAVAILABLE".encode())
					else:
						client.send("NAME_OK".encode())
						names.add(requested_name)
				
				player_object.set_name(requested_name)
			
			elif message == "REQUEST_WORD_PAYLOAD":
				client.send(f"WORD_PAYLOAD").encode()
				client.send(f"{str(word_set)[1:-1]}").encode()
			
			elif start == True:
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

	except Exception as e:
		print(f"Caught: {e}")
		client.close()


def count_lines():
	lines = 0
	
	try:
		with open(DICTIONARY_PATH, "r") as dictionary:
			for line in dictionary:
				lines += 1
				print(lines, line, end="")
	except FileNotFoundError:
		print("DICTIONARY_PATH does not point to an existing file. Try changing it.")
		exit()
	else:
		print(f"Dictionary file {DICTIONARY_PATH} found with {lines} lines")
	
	return lines


def generate_word_set(lines):
	result = set()
	
	while len(result) < WORD_SET_LENGTH:
		random_number = randint(1, lines)

		# linecache has to be used to get a random line from a file, inclusive of the \n character, [:-1] slices the trailing \n off
		word = linecache.getline(DICTIONARY_PATH, random_number)[:-1]

		if word in result:
			continue
		
		if random_number % 3 and random_number % 5:
			result.add(word.upper())
		elif random_number % 13 == 0:
			result.add(word.capitalize())
		else:
			result.add(word)

	return result


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
	
	word_set = generate_word_set(lines)
	print(f"Word set of length {WORD_SET_LENGTH} successfully generated")
	print(f"{word_set}")


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
			players.append(new_player_object())

			# Creates a new thread and calls handle_connection() with arguements client, address we got from socket.accept()
			# This is not accurate at all but just think of it as assigning one core out of many from your CPU to execute this function
			new_thread = threading.Thread(target = handle_connection, args=(client, address, new_player_object))
			
			# For each thread we create, add them to the list threads
			threads.append(new_thread)
			new_thread.start()
			connected += 1
			print(f"{MAX_CONNECTIONS - connected} players remaining before game starts")
		
		print("MAX_CONNECTIONS reached, starting game")
		start = True

		# Wait for all threads to complete
		for thread in threads:
			thread.join()

	except Exception as e:  
		print(f"Caught: {e}")
		exit()
	



# calls the main function
main()
