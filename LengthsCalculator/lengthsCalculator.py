#!/usr/bin/env python

import socket
import time
import sys, getopt
import re

# ------------------------------------------------------------------------------
# Constants
#
TCP_BUFFER_SIZE = 20  # Normally 1024, but we want fast response
TCP_BUFFER_SIZE = 1024

INDENT = '  '

# ------------------------------------------------------------------------------
# System parameters
#
actual_position = [0.0, 0.0, 0.0]
fixing_points = [
    [0.0, 0.0, 0.0],
    [0.0, 0.0, 0.0],
    [0.0, 0.0, 0.0]
]

# ==============================================================================
# Command line options
#
VERBOSE = 0
TCP_IP_ADDRESS = 'geneKranz.local'
TCP_PORT = 16000
FIXING_POINT_NB = 4

USAGE = 'tcp_server.py -i <ip_addr> -p <port> -f <fixing_point_nb>'

try:
    opts, args = getopt.getopt(
        sys.argv[1:],
        "hvp:i:f:",["port=", "ip=", "fixingpointnb="]
    )
except getopt.GetoptError:
    print USAGE
    sys.exit(2)

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
    elif opt in ('-f', '--fixingpointnb'):
        FIXING_POINT_NB = int(arg)

# ==============================================================================
# Functions
#
# ------------------------------------------------------------------------------
# Parse command
#
def parse_command(command):
                                                                  # parse string
    g_code = re.sub(';.*', '', command.lower()).rstrip()
    code_type = ''
    code_id = 0
    code_params = ''
    valid = False
    if len(g_code) > 1:
        parts = g_code.split(' ', 1)
        code_type = parts[0]
        code_params = ''
        if len(parts) > 1:
            code_params = parts[1]
                                                                   # strip parts
        try:
            code_id = int(code_type[1:])
            code_type = code_type[0]
        except:
            code_id = 0
            code_type = ''
                                                                # interpret code
        if code_type == 'g':
            if (code_id == 0) or (code_id == 1):
                valid = True
            elif code_id == 4:
                valid = True
            elif code_id == 28:
                valid = True
            elif code_id == 91:
                valid = True
        elif code_type == 'm':
            if code_id == 0:
                valid = True
            elif (code_id >= 131) and (code_id <= 130+FIXING_POINT_NB):
                valid = True
                                                                  # display info
        if VERBOSE >= 1:
            if valid:
                print 2*INDENT + 'code   : "' + code_type + '"'
                print 2*INDENT + 'id     : "' + str(code_id) + '"'
                print 2*INDENT + 'params : "' + code_params + '"'
            else:
                print 2*INDENT + 'command unknown : ' + command

    return (valid, code_type, code_id, code_params)

# ------------------------------------------------------------------------------
# parse displacement values
#
def g_coordinates(parameters, actual_pos):
    """returns 3 coordinates from a g-code"""
                                                                # default values
    x = actual_pos[0]
    y = actual_pos[0]
    z = actual_pos[0]
                                                                    # parse text
    params = parameters.split(' ')
    for param in params:
        coordinate = param[0]
        value = float(param[1:])
        if coordinate == 'x':
            x = value
        elif coordinate == 'y':
            y = value
        elif coordinate == 'z':
            z = value

    return([x, y, z])

# ------------------------------------------------------------------------------
# parse time value
#
def g_time(parameters):
    """returns a time from a g-code"""
                                                                 # default value
    time = 0.0
                                                                    # parse text
    params = parameters.split(' ')
    for param in params:
        coordinate = param[0]
        value = float(param[1:])
        if coordinate == 's':
            time = time + value
        elif coordinate == 'p':
            time = time + value * 1.0E-3

    return(time)

# ------------------------------------------------------------------------------
# Interpret command
#
def interpret_command(code_type, code_id, code_params):
    if code_type == 'g':
                                                                          # wait
        if code_id == 4:
            wait_delay = g_time(code_params)
            if VERBOSE >= 1:
                print(3*INDENT + "waiting for %.3f sec." % (wait_delay))
                time.sleep(wait_delay)
    if code_type == 'm':
                                                                 # fixing points
        if (code_id > 130) and (code_id <= 130 + FIXING_POINT_NB):
            index = code_id - 131
            while len(fixing_points) < index+1:
                fixing_points.append([0.0, 0.0, 0.0])
            fixing_points[index] = g_coordinates(
                code_params, fixing_points[index]
            )
            if VERBOSE >= 1:
                for coord in fixing_points:
                    print 3*INDENT + "(%d, %d, %d)" % (coord[0], coord[1], coord[2])

# ==============================================================================
# Main
#
# ------------------------------------------------------------------------------
# Open socket
#
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((TCP_IP_ADDRESS, TCP_PORT))
s.listen(1)
if VERBOSE >= 1:
    print 'Listening to TCP/IP port ' + str(TCP_PORT)
    print INDENT + 'on "' + TCP_IP_ADDRESS + '"'

# ------------------------------------------------------------------------------
# Run server and restart a new one when client has disconnected
#
previous = time.time()
while True:
                                                            # start a new server
    conn, addr = s.accept()
    if VERBOSE >= 1:
        print "\n\n", 'Received connection from', addr[0], "\n"
    while True:
                                                                   # get command
        commands = ''
        try:
            commands = conn.recv(TCP_BUFFER_SIZE)
        except socket.error:
            if VERBOSE >= 1:
                print 'closing connection'
            conn.close()
            break
        if not commands:
            break
        # print '->' + commands
        command_list = commands.splitlines()

        for command in command_list:
            print INDENT + command
            now = time.time()
                                                                  # parse g-code
            (valid, code_type, code_id, code_params) = parse_command(command)
                                                           # acknowledge command
            reply = 'ko'
            if valid:
                reply = 'ok'
            conn.send(reply)
                                                             # interpret command
            if valid:
                interpret_command(code_type, code_id, code_params)

            previous = now
