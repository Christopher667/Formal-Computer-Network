#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# @Author: Liu Junyang
# @Student_ID: 21722094
# @Time: 2023/12/03

import socket
import os
import struct
import time
import select
import sys

ICMP_ECHO_REQUEST = 8  # ICMP type code for echo request messages
ICMP_ECHO_REPLY = 0  # ICMP type code for echo reply messages
SEQUENCE = 0
ICMP_FORMAT = '!bbHHh'  # ICMP header format string, used to pack and unpack ICMP headers
DATA_FORMAT = '!d'  # Data format string, used to pack and unpack timestamp data


def checksum(string):
    csum = 0
    countTo = (len(string) // 2) * 2
    count = 0

    while count < countTo:
        thisVal = string[count + 1] * 256 + string[count]
        csum = csum + thisVal
        csum = csum & 0xffffffff
        count = count + 2

    if countTo < len(string):
        csum = csum + string[len(string) - 1]
        csum = csum & 0xffffffff

    csum = (csum >> 16) + (csum & 0xffff)
    csum = csum + (csum >> 16)
    answer = ~csum
    answer = answer & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)
    answer = socket.htons(answer)

    return answer


def receiveOnePing(icmpSocket, destinationAddress, ID, timeout):
    remaining_time = timeout
    while True:
        start_time = time.time()
        select_object = select.select([icmpSocket], [], [], timeout)
        run_time = time.time() - start_time
        remaining_time -= run_time

        if select_object[0] == [] or remaining_time <= 0:
            return -1, -1, -1

        rec_packet, _ = icmpSocket.recvfrom(1024)
        rec_header = rec_packet[20:28]
        rec_type, rec_code, _, rec_id, _ = struct.unpack(ICMP_FORMAT, rec_header)

        if rec_id == ID:
            sent_time = struct.unpack(DATA_FORMAT, rec_packet[28:28 + struct.calcsize(DATA_FORMAT)])[0]
            delay = (time.time() - sent_time) * 1000
            return delay, rec_type, rec_code


def sendOnePing(icmpSocket, destinationAddress, ID):
    # Build ICMP header
    msg_checksum = 0
    msg_header = struct.pack(ICMP_FORMAT, ICMP_ECHO_REQUEST, 0, msg_checksum, ID, SEQUENCE)
    msg_data = struct.pack(DATA_FORMAT, time.time())

    # Checksum ICMP packet using given function
    msg_packet = msg_header + msg_data
    msg_checksum = checksum(msg_packet)

    if sys.platform == 'darwin':  # Get the current system type, 'darwin' stands for MAC OS X system
        # Convert 16-bit integers from host to network byte order
        msg_checksum = socket.htons(msg_checksum) & 0xffff
    else:  # At this time, the system type is Windows
        # Convert host byte order to network byte order
        msg_checksum = socket.htons(msg_checksum)

    # Insert checksum into packet
    header = struct.pack(ICMP_FORMAT, ICMP_ECHO_REQUEST, 0, msg_checksum, ID, SEQUENCE)
    packet = header + msg_data

    # Send packet using socket
    try:
        icmpSocket.sendto(packet, (destinationAddress, 80))
    except socket.gaierror:
        print("Invalid ip address!")


def doOnePing(destinationAddress, timeout):
    # Execute a ping function
    # Create ICMP socket
    icmp_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.getprotobyname("icmp"))
    my_id = os.getpid() & 0xFFFF

    # Call the sendOnePing function to send a ping request
    sendOnePing(icmp_socket, destinationAddress, my_id)

    # Call the receiveOnePing function to receive the ping reply
    time_delay, rec_type, rec_code = receiveOnePing(icmp_socket, destinationAddress, my_id, timeout)

    # Close ICMP socket
    icmp_socket.close()

    # Return total network delay
    return time_delay, rec_type, rec_code


# Function to determine whether timeout occurs
def is_timeout(time_delay, rec_type, rec_code):
    return time_delay == -1 and rec_type == -1 and rec_code == -1


# Function to determine whether it is unreachable
def is_unreachable(rec_code, i, dest_ip):
    if rec_code == 0:
        print("Measurement: %d, ping ip: %s, network unreachable" % (i, dest_ip))
    elif rec_code == 1:
        print("Measurement: %d, ping ip: %s, host unreachable" % (i, dest_ip))
    elif rec_code == 3:
        print("Measurement: %d, ping ip: %s, port unreachable" % (i, dest_ip))


# Function to execute ping
def ping(host, number, timeout):
    lost, receive = 0, 0
    max_time, min_time, sum_time = 0, 1000, 0
    send = number

    # Look up hostname, resolving it to an IP address
    dest_ip = socket.gethostbyname(host)
    print("Ping " + host + " IP: " + dest_ip)

    # Call doOnePing function, approximately every second
    for i in range(0, number):
        time_delay, rec_type, rec_code = doOnePing(dest_ip, timeout)
        i += 1

        if is_timeout(time_delay, rec_type, rec_code):
            print("Measurement: %d, ping ip: %s, request timeout" % (i, dest_ip))
            lost += 1
        elif rec_type == 3:
            lost += 1
            is_unreachable(rec_code, i, dest_ip)
        elif rec_type == 0 and rec_code == 0:
            print("Measurement: %d, ping ip: %s, delay: %5.0f ms" % (i, dest_ip, time_delay))
            receive += 1
            max_time = max(max_time, time_delay)
            min_time = min(min_time, time_delay)
            sum_time += time_delay

        time.sleep(0.5)

    if receive != 0:
        avg_time = sum_time / receive
        recv_rate = receive / send * 100.0
        print(f"\nTotal Send: {send}, Success: {receive}, Lost: {lost}, Success Rate: {recv_rate:.2f}%.")
        print(f"Max Time = {int(max_time)}ms, Minimum Time = {int(min_time)}ms, Average Time = {int(avg_time)}ms")
    else:
        print(f"\nTotal send: {send}, Success: {receive}, lost: {lost}, All Lost!")


if __name__ == '__main__':
    while True:
        try:
            host = input("Please input domain name to ping:")
            number = int(input("Please enter the number of measurement:"))
            timeout = int(input("Please enter timeout:"))
            ping(host, number, timeout)
            break
        except Exception as e:
            print(e)
            continue
