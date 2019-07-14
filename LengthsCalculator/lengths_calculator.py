#!/usr/bin/env python

import socket
import time
import sys, getopt
import re
import numpy as np

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
actual_orientation = [0.0, 0.0]
actual_speed = 0.0
fixing_points = [
    [0.0,     0.0, 0.0],
    [  0.0, 100.0, 0.0],
    [100.0,   0.0, 0.0],
    [100.0, 100.0, 0.0]
]

# ==============================================================================
# Command line options
#
VERBOSE = 0
TCP_IP_ADDRESS = 'geneKranz.local'
TCP_BASE_PORT_GAMER = 16000
TCP_BASE_PORT_WINCHES = TCP_BASE_PORT_GAMER+2
WINCH_ADDRESSES = [
    ('winch_0DF4.local', 3000),
    # ('winch_0DF4.local', 3000),
    # ('winch_5820.local', 3000),
    # ('winch_24E8.local', 3000),
    ('localhost', 3001),
    ('localhost', 3002),
    ('localhost', 3003),
    ('localhost', 3004),
]
WINCH_NB = len(WINCH_ADDRESSES)
TCP_PORT_LANDER = TCP_BASE_PORT_WINCHES+WINCH_NB

USAGE = "lengths_calculator.py -i <ip_addr>\n" + INDENT + \
    "-g <gamer_base_port>\n" + INDENT + \
    "-w <winches_base_port> -n <winch_nb>\n" + INDENT + \
    "-l <lander_port>"

try:
    opts, args = getopt.getopt(sys.argv[1:], "hvi:g:w:n:l:", 
        ["ip=", "gamer=", "winches=", "winchNb=", "lander="])
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
    elif opt in ('-g', '--gamer'):
        TCP_BASE_PORT_GAMER = int(arg)
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
    except:
        client_connected = False

    return(client_connected, client_connection)

def connect_to_socket(address, port):
    sock = None
    try:
        sock = socket.socket()
        sock.connect((address, port))
    except:
        pass
    return sock


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
    except socket.error:
        if VERBOSE >= 1:
            print 'Connection end'
        client_connection.close()
        client_connected = False
        data_received = False
#    if data == '':
#        client_connection.close()
#        client_connected = False
#        data_received = False

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
            print client_name + ' not connected'

    return(client_connected)

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
        if VERBOSE >= 2:
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
# parse orientation values
#
def g_orientation(parameters, actual_orientation):
    """returns yaw and pitch from a g-code"""
                                                                # default values
    yaw = actual_orientation[0]
    pitch = actual_orientation[1]
                                                                    # parse text
    params = parameters.split(' ')
    for param in params:
        coordinate = param[0]
        value = float(param[1:])
        if coordinate == 'u':
            yaw = value
        elif coordinate == 'v':
            pitch = value

    return([yaw, pitch])

# ------------------------------------------------------------------------------
# get speed value
#
def g_speed(parameters, speed):
    """returns the speed from a g-code"""
                                                                    # parse text
    params = parameters.split(' ')
    for param in params:
        coordinate = param[0]
        value = float(param[1:])
        if coordinate == 'f':
            speed = value

    return(speed)

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
# transform cartesian coordinates to cable lengths
#
def position_to_lengths(position, fixing_points):
    """transform position to lengths"""
    lengths = np.zeros(len(position))
    for coordinate_index in range(len(position)):
        temp = 0
        for fixing_index in range(len(fixing_points)):
            temp = temp + (
                position[coordinate_index] -
                fixing_points[fixing_index][coordinate_index]
            )**2
        lengths[coordinate_index] = np.sqrt(temp)

    return(lengths)


# ------------------------------------------------------------------------------
# Interpret command
#
def interpret_command(code_type, code_id, code_params):
    global actual_position
    global actual_orientation
    global actual_speed
    lander_command = ''
    winches_commands = []
    if code_type == 'g':
        #                                                     lander orientation
        if (code_id == 0) or (code_id == 1):
            if re.search('u', code_params):
                actual_orientation = \
                    g_orientation(code_params, actual_orientation)
                lander_command = "G%d U%d v%d" \
                    % (code_id, actual_orientation[0], actual_orientation[1])
                if code_id == 1:
                    actual_speed = g_speed(code_params, actual_speed)
                    lander_command = lander_command + " F%d" % actual_speed
        #                                                      winches commands
            if re.search('x', code_params):
                position = g_coordinates(code_params, (0, 0, 0))
                for i in range(len(actual_position)):
                    actual_position[i] += position[i]
                lengths = position_to_lengths(actual_position, fixing_points)
                for l in lengths:
                    winches_commands.append(
                        "G%d X%d" % (code_id, l)
                    )
                if code_id == 1:
                    actual_speed = g_speed(code_params, actual_speed)
                    winches_commands = [w + " F%d" % actual_speed for w in winches_commands]
        #                                                                   wait
        elif code_id == 4:
            wait_delay = g_time(code_params)
            if VERBOSE >= 1:
                print(3*INDENT + "waiting for %.3f sec." % (wait_delay))
                time.sleep(wait_delay)
    if code_type == 'm':
        #                                                          fixing points
        if (code_id > 130) and (code_id <= 130 + FIXING_POINT_NB):
            index = code_id - 131
            while len(fixing_points) < index+1:
                fixing_points.append([0.0, 0.0, 0.0])
            fixing_points[index] = g_coordinates(
                code_params, fixing_points[index]
            )
            if VERBOSE >= 1:
                print 3*INDENT + 'Fixing points:'
                for coord in fixing_points:
                    print 3*INDENT + \
                        "(%d, %d, %d)" % (coord[0], coord[1], coord[2])

    return(winches_commands, lander_command)

# ==============================================================================
# Main
#
# ------------------------------------------------------------------------------
# Open sockets
#
print 'Opening links on "' + TCP_IP_ADDRESS + '"'
#                                                                  gamer sockets
gamer_socket = open_socket(TCP_IP_ADDRESS, TCP_BASE_PORT_GAMER)
print INDENT + 'for gamer on TCP/IP port ' + str(TCP_BASE_PORT_GAMER)
gamer_status_socket = open_socket(TCP_IP_ADDRESS, TCP_BASE_PORT_GAMER+1)
print INDENT + 'for gamer status on TCP/IP port ' + str(TCP_BASE_PORT_GAMER+1)
#
lander_socket = open_socket(TCP_IP_ADDRESS, TCP_PORT_LANDER)
print INDENT + 'for lander on TCP/IP port ' + str(TCP_PORT_LANDER)
#
print INDENT + 'trying to connect to winches'
winch_sockets = []
for address, port in WINCH_ADDRESSES:
    winch_sockets.append(connect_to_socket(address, port))
if not winch_sockets or any([w is None for w in winch_sockets]):
    print INDENT + 'can not connect to winches'
else:
    print INDENT + 'connected to winches'

# ------------------------------------------------------------------------------
# Run sockets and restart them when client has disconnected
#
previous = time.time()
gamer_connected = False
gamer_status_connected = False
lander_connected = False
while True:
    #                                                      test gamer connection
    if not gamer_connected:
        (gamer_connected, gamer_conn) = connect_to_client(gamer_socket)
    if not gamer_status_connected:
        (gamer_status_connected, gamer_status_conn) = \
            connect_to_client(gamer_status_socket)
    if VERBOSE >= 2:
        if not gamer_connected:
            print 'Waiting for gamer connection'
        if not gamer_status_connected:
            print 'Waiting for gamer status connection'
    #                                                      test gamer connection
    if not lander_connected:
        (lander_connected, lander_conn) = connect_to_client(lander_socket)
    if VERBOSE >= 2:
        if not lander_connected:
            print 'Waiting for lander connection'
    #                                           wait for at least one connection
    if (not gamer_connected) or (not lander_connected):
        time.sleep(0.1);
    #                                                          get gamer command
    if gamer_connected:
        (gamer_connected, data_received, data) = get_client_data(gamer_conn)
        if data_received:
            if data != '':
                now = time.time()
                command_list = data.splitlines()
                for command in command_list:
                    if VERBOSE >= 1:
                        print INDENT + 'received "' +command + '" from gamer'
                        print 2*INDENT + 'after ' + \
                            str(int((now - previous) * 1000.0)) + ' ms'
                    #                                          interpret command
                    reply = 'KO'
                    (valid, code_type, code_id, code_params) = \
                        parse_command(command)
                    (winches_commands, lander_command) = \
                        interpret_command(code_type, code_id, code_params)
                    for i, command in enumerate(winches_commands):
                        socket = winch_sockets[i]
                        if socket:
                            socket.send(command + '\n')
                    if lander_connected:
                        if lander_command != '':
                            if valid:
                                reply = 'OK'
                                if VERBOSE >= 1:
                                    print INDENT + \
                                        'sending "' + lander_command + '"'
                                #                         send command to lander
                                lander_connected = send_client_data(
                                    lander_conn, 'Lander', lander_command
                                )
                                if not lander_connected:
                                    reply = 'KO'
                    #                                             reply to gamer
                    gamer_connected = \
                        send_client_data(gamer_conn, 'Gamer', reply)
                previous = now
            else:
                gamer_conn.close()
                gamer_connected = False
                if VERBOSE >= 1:
                    print 'closing gamer connection'
    #                                                          get lander status
    if lander_connected:
        (lander_connected, data_received, data) = get_client_data(lander_conn)
        if data_received:
            print INDENT + 'received "' + data + '" from lander'
            if gamer_status_connected:
                send_client_data(gamer_status_conn, 'Gamer status', data)
