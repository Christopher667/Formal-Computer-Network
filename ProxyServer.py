#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# @Author: Liu Junyang
# @Student_ID: 21722094
# @Time: 2023/12/05

import socket
import os.path
import sys

def responseToServer(client_socket, receive_data, file_name, file_path):
    print("File is not found in proxy server!")
    print("Request is sent to server.")
    try:
        server_name = file_name.split(':')[0]
        proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        proxy_socket.connect((server_name, 80))
        proxy_socket.sendall(receive_data.encode('UTF-8'))

        server_response = proxy_socket.recv(4096)
        client_socket.sendall(server_response)
        print("Request has been sent!")

        if not os.path.exists(file_path):
            os.makedirs(file_path)
            print("Folder has been created.")

        file_cache = open(file_path + '/index.html', 'w')
        file_cache.write(server_response.decode('UTF-8').replace('\r\n', '\n'))
        file_cache.close()
        print("File cache finished!")
    except:
        print("File cache time out!")


def responseToHost(client_socket, file_path):
    file = open(file_path + '/index.html', 'rb')  # file = index.html, open file to read binary data.
    print("File is found in proxy server.")
    response = file.read()
    client_socket.sendall(response)
    print("Request has been sent!")

def getHandle(client_socket, receive_data):
    file_name = receive_data.split()[1].split('//')[1].replace('/', '')
    file_path = './' + file_name.split(':')[0].replace('.', '_')
    print("File name: ", file_name)
    print("File path: ", file_path)
    try:
        responseToHost(client_socket, file_path)
    except:
        responseToServer(client_socket, receive_data, file_name, file_path)


def handleRequest(tcpSocket):
    receive_data = tcpSocket.recv(4096).decode('UTF-8')
    request_type = receive_data.split(" ")[0]
    print("Http request type:", request_type)
    if request_type == 'GET':
        getHandle(tcpSocket, receive_data)



def startProxyServer(address, port):
    proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    proxy_socket.bind((address, port))
    proxy_socket.listen(10)

    while True:
        try:
            print("Server is on, please start a connection.")
            client_socket, client_address = proxy_socket.accept()
            print("Connection has been established")
            print("Client address: ", client_address)
            handleRequest(client_socket)
            client_socket.close()
        except Exception as e:
            print("Connection Error!")
            break

    proxy_socket.close()


if __name__ == '__main__':
    port_number = int(input("Please enter the proxy server prot number: "))
    startProxyServer('127.0.0.1', port_number)