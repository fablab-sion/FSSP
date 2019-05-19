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
TCP_PORT_LANDER = TCP_PORT_GAMER+1

USAGE = 'tcp_servers.py -i <ip_addr> -g <port> -l <port>'

try:
    opts, args = getopt.getopt(sys.argv[1:], "hi:g:l:",["port=","ip="])
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
    elif opt in ('-l', '--lander'):
        TCP_PORT_LANDER = int(arg)

# ==============================================================================
# Main
#
# ------------------------------------------------------------------------------
# Open socket
#
gamer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
gamer_socket.bind((TCP_IP_ADDRESS, TCP_PORT_GAMER))
gamer_socket.listen(1)
#gamer_socket.settimeout(1.0)
gamer_socket.setblocking(0)
print 'Listening to gamer TCP/IP port ' + str(TCP_PORT_GAMER)
print INDENT + 'on "' + TCP_IP_ADDRESS + '"'
# ------------------------------------------------------------------------------
# Run server and restart a new one when client has disconnected
#
previous = time.time()
gamer_connected = False
data_received = False
while True:
    #                                                      test gamer connection
    if not gamer_connected:
        try:
            gamer_connected = True
            gamer_conn, addr = gamer_socket.accept()
            gamer_conn.settimeout(1.0)
            print 'Received connection from', addr[0]
        except socket.error:
            gamer_connected = False
            print 'Waiting for connection'
            time.sleep(1);
    #                                                          get gamer command
    if gamer_connected:
        data_received = False
        try:
            data_received = True
            data = gamer_conn.recv(TCP_BUFFER_SIZE)
        except socket.timeout:
            print 'Waiting for data'
            data_received = False
        except socket.error:
            print 'Socket error'
            gamer_conn.close()
            gamer_connected = False
            data_received = False
        if data_received:
            if data != '':
                now = time.time()
                print INDENT + 'received "' + data.rstrip() + '"'
                print 2*INDENT + 'after ' + str(int((now - previous) * 1000.0)) + ' ms'
                previous = now
                try:
                    gamer_conn.send('OK')
                except socket.error:
                    print 'Socket error'
                    gamer_conn.close()
                    gamer_connected = False
            else:
                try:
                    gamer_conn.send('KO')
                except socket.error:
                    print 'Socket error'
                    gamer_conn.close()
                    gamer_connected = False
