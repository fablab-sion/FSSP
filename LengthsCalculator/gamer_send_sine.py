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
INITIAL_POSITION = [1350, 1800, 400]
MAX_HEIGHT = 2000
MAX_SPEED = 15000
GET_RESPONSE = False
SAMPLING_PERIOD = 0.5
END_DELAY = 1.0

USAGE = 'send_file.py -i <ip_addr> -p <port> -f <file>'

try:
    opts, args = getopt.getopt(
        sys.argv[1:], "hvi:p:d:rs", ["ip=", "port=", "delay="]
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
    elif opt in ('-d', '--delay'):
        SAMPLING_PERIOD = int(arg)
    elif opt == '-r':
        GET_RESPONSE = True
    elif opt == '-s':
        SEND_TCP = False

if len(args) >= 1:
    CODE_FILE = args[0]

# ==============================================================================
# Functions
#
# ------------------------------------------------------------------------------
# send displacement command
#
def send_displacement(socket, target, speed, duration):
    #                                                  send displacement command
    command = "g1 x%d y%d z%d" % (target[0], target[1], target[2])
    command += " F%d" % (speed)
    if VERBOSE > 0:
        print INDENT + command
    if SEND_TCP:
        tcp_socket.send(command + "\n")
    time.sleep(duration)
    #                                                         check for response
    if GET_RESPONSE:
        try:
            response = tcp_socket.recv(TCP_BUFFER_SIZE)
            print 2*INDENT + response.rstrip()
        except:
            print 2*INDENT + 'no response'

# ------------------------------------------------------------------------------
# calculate displacement function
#
def displacement(index, max_height):
    new_target = [
        INITIAL_POSITION[0],
        INITIAL_POSITION[1],
        INITIAL_POSITION[2] + (index+1) * max_height/10
    ]
    return(new_target)

# ------------------------------------------------------------------------------
# calculate speed for given displacement
#
def displacement_speed(position1, position2, sampling_period):
    distance = (
        (position2[0] - position1[0])**2 +
        (position2[1] - position1[1])**2 +
        (position2[2] - position1[2])**2
    ) ** 0.5
    speed = distance/sampling_period * 60

    return(speed)


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
target = INITIAL_POSITION
send_displacement(tcp_socket, target, MAX_SPEED, SAMPLING_PERIOD)
command_nb = 10
for index in range(command_nb):
    new_target = displacement(index, MAX_HEIGHT)
    speed = displacement_speed(target, new_target, SAMPLING_PERIOD)
    send_displacement(tcp_socket, new_target, speed, SAMPLING_PERIOD)
    target = new_target

time.sleep(END_DELAY)
if SEND_TCP:
    tcp_socket.close()
