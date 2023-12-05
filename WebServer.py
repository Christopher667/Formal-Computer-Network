#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# @Author: Liu Junyang
# @Student_ID: 21722094
# @Time: 2023/12/05

import socket
import sys


def handleRequest(tcpSocket):
	print("Server is on, please start a connection.")
	# 1. Receive request message from the client on connection socket
	connect_socket, client_address = tcpSocket.accept()
	print("Connection has been established")
	print("Client address: ", client_address)
	# 2. Extract the path of the requested object from the message (second part of the HTTP header)
	request_data = connect_socket.recv(1024)
	request_list = request_data.decode().split('\r\n')
	request_headerline = request_list[0]
	print("Request line: " + request_headerline)
	file_name = request_headerline.split(' ')[1].replace('/', '')
	print("File name: "+file_name)

	try:
		file = open('F:/PyCharm/ComputerNetworkFormal/' + file_name, 'rb')
	except FileNotFoundError:
		response_content = "404 NOT FOUND\n"
		response_header = "HTTP/1.1 404 Not Found\r\n" + \
						  "Server: 127.0.0.1\r\n" + "\r\n"
		response_message = (response_header + response_content).encode(encoding='UTF-8')
		connect_socket.sendall(response_message)
	else:
		response_content = file.read().decode()
		response_header = "HTTP/1.1 200 OK\r\n" + \
						  "Server: 127.0.0.1\r\n" + "\r\n"
		response_message = (response_header + response_content).encode(encoding='UTF-8')
		connect_socket.sendall(response_message)
	connect_socket.close()

def startServer(serverAddress, serverPort):
	# 1. Create server socket
	tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

	# 2. Bind the server socket to server address and server port
	tcp_socket.bind((serverAddress, serverPort))

	# 3. Continuously listen for connections to server socket
	tcp_socket.listen(0)

	# 4. When a connection is accepted, call handleRequest function, passing new connection socket (see https://docs.python.org/3/library/socket.html#socket.socket.accept)
	while True:
		try:
			handleRequest(tcp_socket)
		except Exception as e:
			print("Error!")
			break
	#  5. Close server socket
	tcp_socket.close()


if __name__ == '__main__':
	port_number = int(input("Please enter the server prot number: "))
	startServer('127.0.0.1', port_number)
