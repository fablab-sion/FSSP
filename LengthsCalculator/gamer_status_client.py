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
VERBOSE = 0
TCP_IP_ADDRESS = 'geneKranz.local'
TCP_IP_ADDRESS = 'localhost'
TCP_PORT = 16000 + 1

USAGE = 'gamer_status_client.py -v -i <ip_addr> -p <port>'

try:
    opts, args = getopt.getopt(sys.argv[1:], "hp:i:",["port=", "ip="])
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
        TCP_PORT = int(arg)

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
index = 0
while True:
    command = s.recv(TCP_BUFFER_SIZE)
    print 2*INDENT + 'received "' + command.rstrip() +'"'
    g_code = 'G29 S' + str(index) +  " 1\n"
    s.send(g_code)
    index = index+1
s.close()
