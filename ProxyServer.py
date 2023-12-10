#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# @Author: Liu Junyang
# @Student_ID: 21722094
# @Time: 2023/12/05

import socket
import os.path

INDEX = '/index.html'  # Default cache file name


# Auxiliary functions for printing file names and file paths
def print_info(file_name, file_path):
    print("File name: ", file_name)
    print("File path: ", file_path)


# Function that handles requests initiated by the proxy server to the real server
def response_to_server(client_socket, receive_data, file_name, file_path):
    print("File is not found in proxy server!")
    print("[Web Server] Request is sent to Web Server.\n")
    try:
        # Extract the hostname of the server
        server_name = file_name.split(':')[0]

        # Create a new socket to connect to the real web server
        proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        proxy_socket.connect((server_name, 80))

        # Send the client's request message to the real web server
        proxy_socket.sendall(receive_data.encode('UTF-8'))

        # Send the response of the real web server to the client
        server_response = proxy_socket.recv(4096)
        client_socket.sendall(server_response)
        print("Request has been sent!")

        # If the cache path does not exist, create it
        if not os.path.exists(file_path):
            os.makedirs(file_path)
            print("Folder has been created.")

        # Write the response of the real web server to the cache file
        file_cache = open(file_path + INDEX, 'w')
        file_cache.write(server_response.decode('UTF-8').replace('\r\n', '\n'))
        file_cache.close()
        print("File cache finished!")
    except Exception:
        print("File cache time out!")


# Function that handles the proxy server returning cached content to the client
def response_to_host(client_socket, file_path):
    file = open(file_path + INDEX, 'rb')  # file = index.html, open file to read binary data.
    print("File is found in proxy server.")
    response = file.read()
    client_socket.sendall(response)
    print("[Proxy Server] Request is sent to Proxy Server!\n")


# Function to handle DELETE requests
def delete_handle(receive_data):
    file_name = receive_data.split()[1].split('//')[1].replace('/', '')
    file_path = './' + file_name.split(':')[0].replace('.', '_')
    print_info(file_name, file_path)
    if os.path.exists(file_path):
        os.remove('./' + file_path + INDEX)
        os.rmdir(file_path)
    else:
        print("No such file in server!")


# Function to handle HEAD request
def head_handle(client_socket, receive_data):
    file_name = receive_data.split()[1].replace('/', '')
    file_path = file_name.split(':')[0].replace('.', '_')
    print_info(file_name, file_path)
    if os.path.exists(file_path):
        header = "HTTP/ 1.1 200 OK\r\n\r\n"
        client_socket.send(header.encode())
        print("HEAD request successfully finished!\n")
    else:
        header = "HTTP/ 1.1 404 NOT FOUND\r\n\r\n"
        client_socket.send(header.encode())
        print("No such file in server!")


# Function to handle GET requests
def get_handle(client_socket, receive_data):
    file_name = receive_data.split()[1].split('//')[1].replace('/', '')
    file_path = './' + file_name.split(':')[0].replace('.', '_')
    print_info(file_name, file_path)
    try:
        response_to_host(client_socket, file_path)
    except Exception:
        response_to_server(client_socket, receive_data, file_name, file_path)


# Function to handle client requests
def handle_request(tcp_socket):
    receive_data = tcp_socket.recv(4096).decode('UTF-8')
    request_type = receive_data.split(" ")[0]
    print("Http request type:", request_type)
    if request_type == 'GET':
        get_handle(tcp_socket, receive_data)
    elif request_type == 'HEAD':
        head_handle(tcp_socket, receive_data)
    elif request_type == 'DELETE':
        delete_handle(receive_data)


def start_proxy_server(address, port):
    # Create proxy server socket
    proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    proxy_socket.bind((address, port))
    proxy_socket.listen(10)

    # Continuously listen for connections to the proxy server socket
    while True:
        try:
            print("Server is on, please start a connection.")
            client_socket, client_address = proxy_socket.accept()
            print("Connection has been established")
            print("Client address: ", client_address)
            handle_request(client_socket)
            client_socket.close()
        except Exception:
            print("Connection Error!")
            break

    # Close the proxy server socket
    proxy_socket.close()


if __name__ == '__main__':
    port_number = int(input("Please enter the proxy server port number: "))
    start_proxy_server('127.0.0.1', port_number)
