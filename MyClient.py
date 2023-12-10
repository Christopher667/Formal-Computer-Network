#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# @Author: Liu Junyang
# @Student_ID: 21722094
# @Time: 2023/12/09

import socket

def http_client(ip_address, port):
    # Create a socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Connect to the server
    client_socket.connect((ip_address, port))
    print("MyClient is connected to server!\n")

    request_head = "GET /index.html HTTP/1.1\r\n"
    request_content = "Host: localhost:" + str(port) + "\r\nConnection: close\r\nUser-agent: Mozilla/5.0\r\n\r\n"
    request = request_head + request_content

    # Send the request to the server
    client_socket.sendall(request.encode('UTF-8'))

    # Receive and print the response
    response = b''
    while True:
        data = client_socket.recv(1024)
        if not data:
            break
        response += data

    # Decode and print the response
    print(response.decode('utf-8'))
    print("\nMessage is over!")

    # Close the socket
    client_socket.close()



if __name__ == "__main__":

    ip_address = '127.0.0.1'
    print("Run WebServer before start MyClient.")
    port = int(input("Enter the port number: "))
    http_client(ip_address, port)
