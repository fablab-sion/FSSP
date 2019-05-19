#!/usr/bin/env python

import socket
import time
import sys, getopt

# ------------------------------------------------------------------------------
# Constants
#
TCP_BUFFER_SIZE = 20  # Normally 1024, but we want fast response
#TCP_BUFFER_SIZE = 1024

INDENT = '  '

# ------------------------------------------------------------------------------
# Command line options
#
TCP_IP_ADDRESS = 'geneKranz.local'
TCP_PORT_GAMER = 16000
TCP_BASE_PORT_WINCHES = TCP_PORT_GAMER+1
WINCH_NB = 4
TCP_PORT_LANDER = TCP_BASE_PORT_WINCHES+WINCH_NB

USAGE = 'tcp_servers.py -i <ip_addr> -g <port> -l <port> -w <port> -n <nb>'

try:
    opts, args = getopt.getopt(sys.argv[1:], "hi:g:w:n:l:", 
        ["ip=", "gamer=", "winches=", "winchNb=", "lander="])
except getopt.GetoptError:
    print USAGE
    sys.exit(2)

for opt, arg in opts:
    if opt == '-h':
        print USAGE
        sys.exit()
    elif opt in ('-i', '--ip'):
        TCP_IP_ADDRESS = arg
    elif opt in ('-g', '--gamer'):
        TCP_PORT_GAMER = int(arg)
    elif opt in ('-w', '--winches'):
        TCP_BASE_PORT_WINCHES = int(arg)
    elif opt in ('-n', '--winchNb'):
        WINCH_NB = int(arg)
    elif opt in ('-l', '--lander'):
        TCP_PORT_LANDER = int(arg)

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
    except socket.error:
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
        print 'Waiting for data'
        data_received = False
    except socket.error:
        print 'Socket error'
        client_connection.close()
        client_connected = False
        data_received = False
#    if data == '':
#        client_connection.close()
#        client_connected = False
#        data_received = False

    return(client_connected, data_received, data)

# ------------------------------------------------------------------------------
# Send data to client
#
def send_client_data(client_connection, data):
    client_connected = True
    try:
        client_connection.send(data)
    except socket.error:
        client_connection.close()
        client_connected = False

    return(client_connected)

# ==============================================================================
# Main
#
# ------------------------------------------------------------------------------
# Open sockets
#
print 'Listening on "' + TCP_IP_ADDRESS + '"'
#                                                                   gamer socket
gamer_socket = open_socket(TCP_IP_ADDRESS, TCP_PORT_GAMER)
print INDENT + 'for gamer on TCP/IP port ' + str(TCP_PORT_GAMER)
#                                                                  lander socket
lander_socket = open_socket(TCP_IP_ADDRESS, TCP_PORT_LANDER)
print INDENT + 'for lander on TCP/IP port ' + str(TCP_PORT_LANDER)

# ------------------------------------------------------------------------------
# Run server and restart a new one when client has disconnected
#
previous = time.time()
gamer_connected = False
lander_connected = False
while True:
    #                                                      test gamer connection
    if not gamer_connected:
        (gamer_connected, gamer_conn) = connect_to_client(gamer_socket)
    if not gamer_connected:
        print 'Waiting for gamer connection'
    #                                                      test gamer connection
    if not lander_connected:
        (lander_connected, lander_conn) = connect_to_client(lander_socket)
    if not lander_connected:
        print 'Waiting for lander connection'
    #                                           wait for at least one connection
    if (not gamer_connected) or (not lander_connected):
        time.sleep(1);
    #                                                          get gamer command
    if gamer_connected:
        (gamer_connected, data_received, data) = get_client_data(gamer_conn)
        if data_received:
            if data != '':
                now = time.time()
                print INDENT + 'received "' + data.rstrip() + '" from gamer'
                print 2*INDENT + 'after ' + str(int((now - previous) * 1000.0)) + ' ms'
                previous = now
                if lander_connected:
                    gamer_connected = send_client_data(gamer_conn, 'OK')
                    if not gamer_connected:
                        print 'Gamer socket error'
                    lander_connected = send_client_data(lander_conn, data)
                    if not lander_connected:
                        print 'Lander socket error'
                else:
                    gamer_connected = send_client_data(gamer_conn, 'KO')
                    if not gamer_connected:
                        print 'Gamer socket error'
            else:
                gamer_conn.close()
                gamer_connected = False
                print 'closing gamer connection'
    if lander_connected:
        (lander_connected, data_received, data) = get_client_data(lander_conn)
        if data_received:
            print INDENT + 'received "' + data.rstrip() + '" from lander'
