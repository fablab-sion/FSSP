#!/usr/bin/env python

import socket
import time
import sys, getopt

# ------------------------------------------------------------------------------
# Constants
#
TCP_BUFFER_SIZE = 1024

INDENT = '  '

# ------------------------------------------------------------------------------
# Command line options
#
VERBOSE = 0
TCP_IP_ADDRESS = 'geneKranz.local'
TCP_IP_ADDRESS = 'localhost'
TCP_PORT = 16000
CODE_FILE = 'cartesian.txt'
GET_RESPONSE = False
SEND_DELAY = 0.5
END_DELAY = 1.0

USAGE = 'send_file.py -i <ip_addr> -p <port> -f <file>'

try:
    opts, args = getopt.getopt(
        sys.argv[1:], "hvi:p:f:d:r", ["ip=", "port=", "file=", "delay="]
    )
except getopt.GetoptError:
    print USAGE
    sys.exit(2)
#print(args, opts)

for opt, arg in opts:
    if opt == '-h':
        print USAGE
        sys.exit()
    elif opt == '-v':
        VERBOSE = 1
    elif opt in ('-i', '--ip'):
        TCP_IP_ADDRESS = arg
    elif opt in ('-p', '--port'):
        TCP_PORT = int(arg)
    elif opt in ('-f', '--file'):
        CODE_FILE = arg
    elif opt in ('-d', '--delay'):
        SEND_DELAY = int(arg)
    elif opt == '-r':
        GET_RESPONSE = True

if len(args) >= 1:
    CODE_FILE = args[0]

# ==============================================================================
# Main
#
# ------------------------------------------------------------------------------
# Open socket
#
tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcp_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
tcp_socket.connect((TCP_IP_ADDRESS, TCP_PORT))
tcp_socket.settimeout(0.1)
if VERBOSE == 1:
    print 'Sending "' + CODE_FILE + '"'
    print INDENT + 'to "' + TCP_IP_ADDRESS + '" on port ' + str(TCP_PORT)
    print ''

# ------------------------------------------------------------------------------
# Send file
#
with open(CODE_FILE) as g_code_file:
    for line in g_code_file:
        line = line.rstrip()
        print(INDENT + line)
        if line != '':
            tcp_socket.send(line + "\n")
            time.sleep(SEND_DELAY)
            if GET_RESPONSE:
                try:
                    response = tcp_socket.recv(TCP_BUFFER_SIZE)
                    print 2*INDENT + response.rstrip()
                except:
                    print 2*INDENT + 'no response'
time.sleep(END_DELAY)
tcp_socket.close()
#time.sleep(END_DELAY)
