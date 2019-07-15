#!/usr/bin/env python
#
# netstat -an | grep 1600

import socket
import time
import sys, getopt

# ------------------------------------------------------------------------------
# Constants
#
VERBOSE = 0
TCP_BUFFER_SIZE = 20  # Normally 1024, but we want fast response
TCP_BUFFER_SIZE = 1024

INDENT = '  '

# ------------------------------------------------------------------------------
# Command line options
#
TCP_IP_ADDRESS = 'geneKranz.local'
TCP_IP_ADDRESS = 'localhost'
BASE_TCP_PORT = 16003
TCP_PORT_NB = 4

USAGE = 'winch_servers.py -i <ip_addr> -p <port> -c <count>'

try:
    opts, args = getopt.getopt(sys.argv[1:], "hp:i:c:",["port=","ip=","count="])
except getopt.GetoptError:
    print USAGE
    sys.exit(2)

for opt, arg in opts:
    if opt == '-h':
        print USAGE
        sys.exit()
    elif opt in ('-i', '--ip'):
        TCP_IP_ADDRESS = arg
    elif opt in ('-p', '--port'):
        BASE_TCP_PORT = int(arg)
    elif opt in ('-c', '--count'):
        TCP_PORT_NB = int(arg)

# ==============================================================================
# Functions
#
# ------------------------------------------------------------------------------
# open server TCP socket
#
def open_socket(ip_address, tcp_port):
    new_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    new_socket.bind((ip_address, tcp_port))
    new_socket.listen(1)
    #gamer_socket.settimeout(1.0)
    new_socket.setblocking(0)

    return(new_socket)

# ------------------------------------------------------------------------------
# Check for client
#
def connect_to_client(client_socket):
    client_connected = True
    client_connection = None
    try:
        client_connection, client_address = client_socket.accept()
        client_connection.settimeout(1.0)
        print 'Received connection from', client_address[0]
    except:
        client_connected = False

    return(client_connected, client_connection)

# ------------------------------------------------------------------------------
# Get data from client
#
def get_client_data(client_connection):
    client_connected = True
    data_received = True
    data = ''
    try:
        data = client_connection.recv(TCP_BUFFER_SIZE)
    # except socket.timeout:
    except Exception as e:
        data_received = False
        if str(e) == 'timed out':
            if VERBOSE >= 2:
                print 'Waiting for data'
            data_received = False
        else:
            print '> ' + str(e)
            if VERBOSE >= 1:
                print 'Connection end'
            client_connection.close()
            client_connected = False
    # except socket.error:
    #     if VERBOSE >= 1:
    #         print 'Connection end'
    #     client_connection.close()
    #     client_connected = False
    #     data_received = False

    return(client_connected, data_received, data.rstrip())

# ------------------------------------------------------------------------------
# Send data to client
#
def send_client_data(client_connection, client_name, data):
    client_connected = True
    try:
        client_connection.send(data)
    # except socket.error:
    except:
        client_connection.close()
        client_connected = False

    if not client_connected:
        if VERBOSE >= 1:
            print client_name + ' not connected'

    return(client_connected)


# ==============================================================================
# Main
#
# ------------------------------------------------------------------------------
# Open sockets
#
print 'Creating TCP/IP sockets:'
sockets = []
ports = []
for index in range(TCP_PORT_NB):
    tcp_port = BASE_TCP_PORT + index
    ports.append(tcp_port)
    s = open_socket(TCP_IP_ADDRESS, tcp_port)
    sockets.append(s)
    print INDENT + 'on "' + TCP_IP_ADDRESS + '", port ' + str(tcp_port)

# ------------------------------------------------------------------------------
# Run server and restart a new one when client has disconnected
#
previous = time.time()
connection_status = []
while True:
#                                                                  start servers
    print 'Listening to'
    for index in range(TCP_PORT_NB):
        print INDENT + str(ports[index])
        s = sockets[index]
        connect_to_client(s)
        connection_status.append('waiting')
#                                                                  read commands
    running = True
    while running:
        for index in range(TCP_PORT_NB):
            (client_connected, data_received, data) = get_client_data(sockets[index])
            if data_received:
                now = time.time()
                print INDENT + 'received "' + data.rstrip() + '"'
                print 2*INDENT + 'after ' + str(int((now - previous) * 1000.0)) + ' ms'
                previous = now
                send_client_data(sock, '', 'OK')
            if connection_status[index] == 'waiting':
                if client_connected:
                    connection_status[index] == 'connected'
            elif connection_status[index] == 'connected':
                if not client_connected:
                    running = False
        time.sleep(1)
