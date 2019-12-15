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
SEND_TCP = True
WINCH_ID = 2
DISTANCE = 10
MAX_HEIGHT = 2000
MAX_SPEED = 15000
GET_RESPONSE = False
SAMPLING_PERIOD = 2.0
END_DELAY = 1.0

USAGE = 'winch_lift.py -i <ip_addr> -p <port> -f <file>'

try:
    opts, args = getopt.getopt(
        sys.argv[1:], "hvi:p:rsw:d:", ["ip=", "port=", "winch=", "distance="]
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
    elif opt == '-r':
        GET_RESPONSE = True
    elif opt == '-s':
        SEND_TCP = False
    elif opt in ('-w', '--winch'):
        WINCH_ID = int(arg)
    elif opt in ('-d', '--distance'):
        DISTANCE = int(arg)

if len(args) >= 1:
    CODE_FILE = args[0]

# ==============================================================================
# Functions
#
# ------------------------------------------------------------------------------
# send displacement command
#
def send_displacement(socket, winch_id, position, speed):
    #                                                  send displacement command
    command = "g6 m%d l%d f%d" % (winch_id, position, speed)
    if VERBOSE > 0:
        print INDENT + command
    if SEND_TCP:
        tcp_socket.send(command + "\n")
    #                                                         check for response
    if GET_RESPONSE:
        try:
            response = tcp_socket.recv(TCP_BUFFER_SIZE)
            print 2*INDENT + response.rstrip()
        except:
            print 2*INDENT + 'no response'

# ==============================================================================
# Main
#
# ------------------------------------------------------------------------------
# Open socket
#
if SEND_TCP:
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    tcp_socket.connect((TCP_IP_ADDRESS, TCP_PORT))
    tcp_socket.settimeout(0.1)
    if VERBOSE == 1:
        print INDENT + 'to "' + TCP_IP_ADDRESS + '" on port ' + str(TCP_PORT)
        print ''
else:
    tcp_socket = None

# ------------------------------------------------------------------------------
# Send function
#
send_displacement(tcp_socket, WINCH_ID, -DISTANCE, MAX_SPEED)

if SEND_TCP:
    tcp_socket.close()
