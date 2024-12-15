import threading
import socket

# Constant configuration variables go here, use ALL CAPS to indicate constant
MAX_CONNECTIONS = 1
PORT = 6969


# Named constants go here
RECEIVE_SIZE = 1024



# Global variables go here
names = set() 
names_lock = threading.Lock() # Global thread locks just in case to prevent race conditions


'''
Target function to handle each client in a separate thread to avoid blocking functions like socket.recv() from blocking the main thread, this allows us to handle multiple clients
client is a client socket to the client, which is what we use to send data to it
address contains the ip address and the port of the client
'''
class player():
	def __init__(self):
		self.username = username
		self.score = 0
		self.total_time = 0.0
	
	def add_time(self, time_delta):
		self.total_time += time_delta
	
	def set_name(self, username):
		self.username = username



def handle_connection(client, address):
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
			
			# NOTE:	ALL strings sent should be converted to UPPERCASE before sending to avoid "apple" and "Apple" being different
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
			# TODO: Add more cases to implement protocol for sending data to client, currently just prints out what the client sent and sends 'men' back
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

# Entry point here
def main():
	if PORT < 1024 or PORT > 65353:
		print("Invalid port number")
		exit()

	if type(MAX_CONNECTIONS) != int or type(PORT) != int:
		print("MAX_CONNECTIONS and PORT must be of type int")
		exit()

	
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
		while connected <= MAX_CONNECTIONS:
			# socket.accept() returns two things, the client socket, and the client IP address
			client, address = sock.accept()
			print(f"Accepted connection from {address}")
			
			# Creates a new thread and calls handle_connection() with arguements client, address we got from socket.accept()
			# This is not accurate but just think of it as assigning one core out of many from your CPU to execute this function
			new_thread = threading.Thread(target = handle_connection, args=(client, address))
			new_thread.start()
			connected += 1
	
	except Exception as e:  
		print(f"Caught: {e}")
		exit()
	



# calls the main function
main()
