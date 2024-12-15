import socket

# Constant configuration variables go here, use ALL CAPS to indicate constant



# Named constants go here
RECEIVE_SIZE = 1024



# Global variables go here




# TODO: Prompt the user for a username and use it for each of their submissions to the server, we'll use a set on the server end to prevent duplicate names
# TODO: Check if we connected to an instance of the game server or just a random server, maybe we can just a "magic string" to identify itself
# TODO: Don't start the game and show a waiting prompt until all players are connected
# TODO: Actually implement the game itself, once the game starts we need to get data from the server, parse it, get input from the user, send it to the server
# TODO: Show leaderboard if possible
# TODO: Clear the terminal first before printing each new prompt
# TODO: Establish more game rules, do we just eliminate the player if they submit a mistake or do we implement a life system, stuff like that
# TODO: Establish a text based protocol to enable communication between client and server. e.g. receiving START from the server triggers the game from clients, we can discuss this out later
# TODO: Establish game rules down below
# TODO: Catch things that can go wrong and give more meaningful error messages to the user in the try-except statements, currently just exits so we can get the exception names
# TODO: After prompt the user if they want to exit or play another round after the previous round finishes

# NOTE: Always capitalise messages using str.upper() method before encoding and sending to server to avoid "apple" and "Apple" being different, there's an example of how to send and receive messages in the server.py


'''
Current gameplay idea: 
Players start by receiving a randomly determined word by the server that they have to type out as fast as possible.
We can measure time and take the difference between each new prompt to get time taken
We send the string and the time taken to the server to update the player's status
We can add more ideas here
'''

# Entry point here
def main():
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
		to_send = input("Input? ").upper()
		
		if to_send == "FF":
			server.send(to_send.encode())
			server.close()
			break
		else:
			server.send(to_send.encode())

		print(server.recv(RECEIVE_SIZE).decode())

	
# Calls the main function
main()
