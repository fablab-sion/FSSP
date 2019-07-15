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
# TCP_IP_ADDRESS = '192.168.2.68'
# TCP_PORT = 3000
TCP_IP_ADDRESS = 'geneKranz.local'
TCP_IP_ADDRESS = 'localhost'
TCP_PORT = 16000
GET_RESPONSE = False
PACKET_NB = 2

USAGE = 'tcp_client.py -i <ip_addr> -p <port> -n <packet_nb> -r'

try:
    opts, args = getopt.getopt(sys.argv[1:], "hrp:i:n:",["port=", "ip=", "packets="])
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
        TCP_PORT = int(arg)
    elif opt in ('-n', '--packets'):
        PACKET_NB = int(arg)
    elif opt == '-r':
        GET_RESPONSE = True

# ==============================================================================
# Main
#
# ------------------------------------------------------------------------------
# Open socket
#
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
s.connect((TCP_IP_ADDRESS, TCP_PORT))
print 'Listening to "' + TCP_IP_ADDRESS + '" on port ' + str(TCP_PORT)

# ------------------------------------------------------------------------------
# Send loop
#
for index in range(1, PACKET_NB+1):
    print INDENT + 'packet ' + str(index)
    #                                                       send winches command
    g_code = 'G0 X' + str(index) + ' Y' + str(index) + ' Z' + str(index) + "\n"
    s.send(g_code)
    if GET_RESPONSE:
        response = s.recv(TCP_BUFFER_SIZE)
        print 2*INDENT + 'received "' + response.rstrip() +'"'
    #                                                        send lander command
    g_code = 'G0 U' + str(index) + ' V' + str(index) + "\n"
    s.send(g_code)
    if GET_RESPONSE:
        response = s.recv(TCP_BUFFER_SIZE)
        print 2*INDENT + 'received "' + response.rstrip() +'"'
    #                                                      wait between commands
    time.sleep(100.0 / 1000.0);
    # time.sleep(3);
time.sleep(2);
s.close()
