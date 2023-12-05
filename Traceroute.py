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
import binascii

ICMP_ECHO_REQUEST = 8
CODE_ECHO_REQUEST_DEFAULT = 0
# ICMP echo_reply
ICMP_ECHO_REPLY = 0
CODE_ECHO_REPLY_DEFAULT = 0
# ICMP overtime
TYPE_ICMP_OVERTIME = 11
CODE_TTL_OVERTIME = 0
# ICMP unreachable
TYPE_ICMP_UNREACHED = 3

MAX_HOPS = 30  # set max hops-30
TRIES = 3  # detect 3 times

SEQUENCE = 1
ICMP_FORMAT = 'bbHHh'
DATA_FORMAT = 'd'


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

def receiveUdpPacket():
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind(("0.0.0.0", 33434))
    try:
        while True:
            rec_packet, rec_address = udp_socket.recvfrom(1024)
            print(f"Received UDP packet from {rec_address}: {rec_packet}")
    except socket.error as e:
        print(f"Socket error: {e}")
    finally:
        udp_socket.close()
def receiveUdpPing(udp_socket, timeout):
    udp_socket.settimeout(timeout)  # 确保超时时间正确设置
    while True:
        try:
            start_time = time.time()
            rec_packet, rec_address = udp_socket.recvfrom(1024)
            time_delay = (time.time() - start_time) * 1000
            print(f"Received UDP packet in {time_delay} ms")
            if time_delay > timeout or not rec_packet:
                print("No UDP packet received.")
                return -1, -1, -1, '-1'

            address = rec_address[0]
            try:
                host_info = socket.gethostbyaddr(address)
            except socket.error as e:
                host_name = '{0}'.format(address)
            else:
                host_name = '{0} ({1})'.format(address, host_info[0])

            return time_delay, 11, 0, host_name
        except socket.timeout:
            print("UDP socket timeout. No packet received.")
            return -1, -1, -1, '-1'


def receiveOnePing(icmpSocket, destinationAddress, ID, timeout):
    start_time = time.time()
    select_object = select.select([icmpSocket], [], [], timeout)
    run_time = time.time() - start_time

    if run_time > timeout or run_time == 0:
        return -1, -1, -1, '-1'

    rec_packet, rec_address = icmpSocket.recvfrom(1024)
    rec_header = rec_packet[20:28]
    rec_type, rec_code, rec_checksum, rec_id, rec_sequence = struct.unpack(ICMP_FORMAT, rec_header)
    address = rec_address[0]

    try:
        host_info = socket.gethostbyaddr(address)
    except socket.error as e:
        host_name = '{0}'.format(address)
    else:
        host_name = '{0} ({1})'.format(address, host_info[0])

    return run_time, rec_type, rec_code, host_name


def sendOnePing(socket, destinationAddress, ID, protocol):
    # 1. Build ICMP header
    msg_checksum = 0
    msg_header = struct.pack(ICMP_FORMAT, ICMP_ECHO_REQUEST, 0, msg_checksum, ID, SEQUENCE)
    msg_data = struct.pack(DATA_FORMAT, time.time())

    # 2. Checksum ICMP packet using given function
    msg_packet = msg_header + msg_data
    msg_checksum = checksum(msg_packet)

    if sys.platform == 'darwin':  # Get the current system type, 'darwin' stands for MAC OS X system
        # Convert 16-bit integers from host to network byte order
        msg_checksum = msg_checksum & 0xffff
    else:  # At this time, the system type is Windows
        # Convert host byte order to network byte order
        msg_checksum = msg_checksum

    # 3. Insert checksum into packet
    header = struct.pack(ICMP_FORMAT, ICMP_ECHO_REQUEST, 0, msg_checksum, ID, SEQUENCE)
    packet = header + msg_data

    # 4. Send packet using socket
    try:
        if protocol == 'icmp':
            socket.sendto(packet, (destinationAddress, 80))
        elif protocol == 'udp':
            socket.sendto(packet, (destinationAddress, 33434))

    except socket.gaierror as e:
        print("Invalid ip address!")


def doOnePing(destinationAddress, timeout, ttl, protocol):
    # Build icmp_socket
    icmp_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.getprotobyname("icmp"))
    icmp_socket.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, struct.pack('I', ttl))
    icmp_socket.settimeout(timeout)
    # Bind port
    #icmp_socket.bind(("", 1))
    #
    # Build udp_socket
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    udp_socket.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, struct.pack('I', ttl))
    udp_socket.settimeout(timeout)
    udp_socket.listen(10)
    #udp_socket.bind(("", 8001))

    #
    my_id = os.getpid() & 0xFFFF

    if protocol == 'icmp':
        sendOnePing(icmp_socket, destinationAddress, my_id, protocol)
    elif protocol == 'udp':
        sendOnePing(udp_socket, destinationAddress, my_id, protocol)
        time.sleep(0.1)
    udp_socket.close()
    time_delay, rec_type, rec_code, host_name = receiveOnePing(icmp_socket, destinationAddress, my_id, timeout)
    icmp_socket.close()
    return time_delay, rec_type, rec_code, host_name

def traceroute(host, timeout, protocol):
    print("Host: %s  [%s]" %(host, socket.gethostbyname(host)))
    for ttl in range(1, MAX_HOPS ):
        host_name = ''
        send = 0
        print("\nMeasurement %d: " % ttl)

        for hops in range(0, 3):
            delay, rec_type, rec_code, ip_name = doOnePing(host, timeout, ttl, protocol)
            time.sleep(0.5)
            #print("\nrec_type: %d, rec_code: %d"%(rec_type, rec_code))
            if delay == -1 and rec_type == -1 and rec_code == -1:
                print("  *  ", end='\t')
            elif rec_type == 3 and rec_code == 0:
                print("Network Unreachable!")
                break
            elif rec_type == 3 and rec_code == 1:
                print("Host Unreachable!")
                break
            elif rec_type == 3 and rec_code == 2:
                print("Protocol Unreachable!")
                break
            elif rec_type == 3 and rec_code == 3:
                print("Port Unreachable! Finish!")
                return
            elif rec_type == 11 and rec_code == 0:
                print("%3.0dms" % (delay*1000), end='\t')
                host_name = ip_name
                send += 1
            elif rec_type == 0 and rec_code == 0:
                print("%3.0dms [ip: %s]" % (delay * 1000, ip_name), end='\t')
                print("Finish!")
                return
            else:
                print("Error!")

        if send != 0:
            print("Host: %s" % host_name, end='\t')
        else:
            print("Request timeout!", end='\t')


if __name__ == '__main__':
    while True:
        try:
            host = input("Please input domain name to ping:")
            timeout = int(input("Please enter timeout:"))
            protocol = input("Please choose protocol to test (icmp/udp):")
            traceroute(host, timeout, protocol)
            break
        except Exception as e:
            print(e)
            continue
