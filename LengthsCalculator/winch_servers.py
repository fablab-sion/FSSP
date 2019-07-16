#!/usr/bin/env python
#
# netstat -an | grep 1600

import socket
import time
import sys, getopt
import re

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
    opts, args = getopt.getopt(sys.argv[1:], "hvp:i:c:",["port=","ip=","count="])
except getopt.GetoptError:
    print USAGE
    sys.exit(2)

for opt, arg in opts:
    if opt == '-h':
        print USAGE
        sys.exit()
    elif opt in ('-v', '--verbose'):
        VERBOSE = VERBOSE + 1
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
        print INDENT + 'Received connection from', client_address[0]
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
    except socket.timeout:
        if VERBOSE >= 2:
            print 'Waiting for data'
        data_received = False
    except Exception as e:
        if VERBOSE >= 2:
            print 'Exception ' + str(e)
        client_connected = False
        data_received = False
    #     data_received = False
    #     if str(e) == 'timed out':
    #         if VERBOSE >= 2:
    #             print 'Waiting for data'
    #         data_received = False
    #     else:
    #         print '> ' + str(e)
    #         if VERBOSE >= 1:
    #             print 'Connection end'
    #         client_connection.close()
    #         client_connected = False
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
    except socket.error:
        client_connection.close()
        client_connected = False

    if not client_connected:
        if VERBOSE >= 1:
            print INDENT + client_name + ' not connected'

    return(client_connected)


# ==============================================================================
# Main
#
# ------------------------------------------------------------------------------
# Open sockets
#
print 'Creating TCP/IP sockets:'
ports = []
sockets = []
connections = []
for index in range(TCP_PORT_NB):
    tcp_port = BASE_TCP_PORT + index
    ports.append(tcp_port)
    s = open_socket(TCP_IP_ADDRESS, tcp_port)
    sockets.append(s)
    print INDENT + 'on "' + TCP_IP_ADDRESS + '", port ' + str(tcp_port)
    connections.append(None)

# ------------------------------------------------------------------------------
# Run server and restart a new one when client has disconnected
#
previous = time.time()

while True:
    print 'Waiting for a new connection'
    connection_status = []
    for index in range(TCP_PORT_NB):
        connection_status.append('waiting')
    running = True
    while running:
        for index in range(TCP_PORT_NB):
            sock = sockets[index]
#                                                                  read commands
            if connection_status[index] == 'waiting':
                (client_connected, client_connection) = connect_to_client(sock)
                if client_connected:
                    connection_status[index] = 'connected'
                    connections[index] = client_connection
            elif connection_status[index] == 'connected':
                conn = connections[index]
                (client_connected, data_received, data) = get_client_data(conn)
                if data_received:
                    now = time.time()
                    time_difference_ms = int((now - previous) * 1000.0)
                    if time_difference_ms > 1100:
                        print 2*INDENT + 'after ' + \
                            str(time_difference_ms) + ' ms'
                    port = ports[index]
                    data = re.sub('\n', '|', data.rstrip())
                    print 3*INDENT + "received \"%s\" from port %d" % (data, port)
                    previous = now
                    client_connected = send_client_data(
                        conn, 'client ' + str(index+1), 'OK'
                    )
                if not client_connected:
                    connection_status[index] = 'disconnected'
                    running = False
        time.sleep(1)
