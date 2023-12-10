#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# @Author: Liu Junyang
# @Student_ID: 21722094
# @Time: 2023/12/05

import socket


# Parse the HTTP request and extract the request line and file name
def request_format(data):
    request_list = data.decode().split('\r\n')
    request_headerline = request_list[0]
    file_name = request_headerline.split(' ')[1].replace('/', '')
    return request_headerline, file_name


# Function to handle client requests
def handleRequest(tcpSocket):
    print("Server is on, please start a connection.")
    # Receive request message from the client on connection socket
    connect_socket, client_address = tcpSocket.accept()
    print("Connection has been established")
    print("Client address: ", client_address)
    # Extract the path of the requested object from the message (second part of the HTTP header)
    request_data = connect_socket.recv(1024)
    request_headerline, file_name = request_format(request_data)
    print("Request line: " + request_headerline)
    print("File name: " + file_name)

    try:
        # Try to open the requested file.
        # Make sure index.html is in the directory where the WebServer.py program is located.
        file = open('F:/PyCharm/ComputerNetworkFormal/' + file_name, 'rb')
    except FileNotFoundError:
        # If the file is not found, return a 404 Not Found error
        response_content = "404 NOT FOUND\n"
        response_header = "HTTP/1.1 404 Not Found\r\n" + \
                          "Server: 127.0.0.1\r\n" + "\r\n"
        response_message = (response_header + response_content).encode(encoding='UTF-8')
        connect_socket.sendall(response_message)
    else:
        # If the file exists, return 200 OK and the file content
        response_content = file.read().decode()
        response_header = "HTTP/1.1 200 OK\r\n" + \
                          "Server: 127.0.0.1\r\n" + "\r\n"
        response_message = (response_header + response_content).encode(encoding='UTF-8')
        connect_socket.sendall(response_message)
    connect_socket.close()


def startServer(serverAddress, serverPort):
    # Create server socket
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Bind the server socket to server address and server port
    tcp_socket.bind((serverAddress, serverPort))

    # Continuously listen for connections to server socket
    tcp_socket.listen(0)


    while True:
        try:
            handleRequest(tcp_socket)
        except Exception:
            print("Error!")
            break
    # Close server socket
    tcp_socket.close()


if __name__ == '__main__':
    port_number = int(input("Please enter the server prot number: "))
    startServer('127.0.0.1', port_number)
