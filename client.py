# Import the necessary modules

import socket
import sys
import time

# Creating the socket and accepting user input hostname

socket_server = socket.socket()
server_host = socket.gethostname()
ip = socket.gethostbyname(server_host)
sport = 8080

# Connection to the server
print("This is your IP address:", ip)
server_host = input("Enter friend\'s IP address: ")
name = input("Enter Friend\'s name: ")

socket_server.connect((server_host, sport))

# Receiving the message from the server
socket_server.send(name.encode())
server_name = socket_server.recv(1024)
server_name = server_name.decode()

print(server_name, " has joined...")
while True:
    message = (socket_server.recv(1024)).decode()
    print(server_name, ":", message)
    message = input("Me: ")
    socket_server.send(message.encode())
