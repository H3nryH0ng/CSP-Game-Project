import socket
from time import sleep

# Constant configuration variables go here, use ALL CAPS to indicate constant



# Named constants go here
RECEIVE_SIZE = 4096
CHECKSUM = "f5cb05cce8c03b4c82efc1dba3ace46d613474675ac8dde3a9d083869c1e8577"


# Global variables go here




# TODO: Catch things that can go wrong and give more meaningful error messages to the user in the try-except statements, currently just exits so we can get the exception names 8

# NOTE: Always capitalise protocol messages before encoding and sending to server to avoid "apple" and "Apple" being different, there's an example of how to send and receive messages in the server.py
# this only applies to protocol messages, the word list sent will still be case sensitive.




# Entry point here
def main():
    # Defined variable
	# Don't remove this line, it somehow fk with the index of the code
    
	# Prompt the user for the address of the server instance to connect to until connection is successful
	while True:
		try:
			address = input("Server address? ")
			port = int(input("Server port number [1024-65353]? "))

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
			break

	# Main game loop is here
	while True:
		# Should we do a help cmd to guide the user? ~ Francis
		
		
		# TODO: Check if we connected to an instance of the game server or just a random server, CHECKSUM is defined globally, if we send VERIFY and CHECKSUM doesn't match, give a meaningful message then exit 1
		
		server.send("VERIFY".encode())
		verifier = server.recv(RECEIVE_SIZE).decode()

	
		if verifier != CHECKSUM:
			print("Please connect to a valid game server")
			exit()


		# TODO: Prompt the user for a username and use it for each of their submissions to the server, we'll use a set on the server end to prevent duplicate names 0
		#~ Francis
		while True:
			name_request = str(input("Name?"))

			server.send("SET_NAME".encode())
			server.send(f"{name_request}".encode())
			
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


		# TODO: Don't start the game and show a waiting prompt until all players are connected 2
		server.send("READY".encode())
		print("Waiting for Players")

		while True:
			starter = server.recv(RECEIVE_SIZE).decode()
			
			if starter == "START":
				server.send("REQUEST_WORD_PAYLOAD".encode())
			
			# Expect WORD_PAYLOAD and exit wait loop - For Francis

			sleep(0.1)


		# TODO: Actually implement the game itself, once the game starts we need to get data from the server, parse it, get input from the user, send it to the server 3
		# TODO: Clear the terminal first before printing each new prompt 5
		# TODO: Show leaderboard after player completes the list 4
		# TODO: After prompt the user if they want to exit or play another round after the previous round finishes 9
		

# Calls the main function
main()
