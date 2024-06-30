# Import the necessary modules

import socket
import sys
import time

# Creating the sockets and retrieving the hostname

new_socket = socket.socket()
host_name = socket.gethostname()
s_ip = socket.gethostbyname(host_name)
port = 8080

# Bind the host and port

new_socket.bind(host_name, port)
print("Binding successful...")
print("This is your ip: ", s_ip)

# Listening for connections
name = input("Enter your nickname: ")
new_socket.listen(1)

# Accepting incoming connections

conn, add = new_socket.accept()

print("Received connection from ", add[0])
print("connection Established. Connected from: ", add[0])

# Storing incoming connection data

client = (conn;recv(1024)).decode()
print(client + " has connected.")
conn.send(name.encode())

# Delivering messages

while True:
    message = input("Me : ")
    conn.send(message.encode())
    message = conn.recv(1024)
    message = message.decode()
    print(client, ":", message)