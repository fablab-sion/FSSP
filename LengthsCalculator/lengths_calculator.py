#!/usr/bin/env python
#
# netstat -an | grep 1600

import socket
import time
import sys, getopt
import re
import numpy as np

# ------------------------------------------------------------------------------
# Constants
#
SIMULATE_WINCHES = False
SEND_G_CODES = True

TCP_BUFFER_SIZE = 20  # Normally 1024, but we want fast response
TCP_BUFFER_SIZE = 1024
MAX_SPEED = 15000

INDENT = '  '

# ------------------------------------------------------------------------------
# System parameters
#
absolute_displacement = True
inital_position = [1350, 1800, 400]
actual_position = inital_position[:]
actual_orientation = [0.0, 0.0]
actual_speed = 0.0
fixing_points = [
    [  0.0,   0.0, 2500],
    [ 2900,   0.0, 2500],
    [ 2900,  4200, 2500],
    [  0.0,  4200, 2500],
]
winch_nb = len(fixing_points)  # this number can increase with M13n commands

# ==============================================================================
# Command line options
#
VERBOSE = 0
TCP_IP_ADDRESS = 'geneKranz.local'
TCP_IP_ADDRESS = 'localhost'
TCP_BASE_PORT_GAMER = 16000
TCP_PORT_LANDER = TCP_BASE_PORT_GAMER+2
TCP_BASE_PORT_WINCHES = TCP_PORT_LANDER+1
WINCH_ADDRESSES = [
    ('winch_0DF4.local', 3000),
    ('winch_02B4.local', 3000),
    ('winch_5820.local', 3000),
    ('winch_24E8.local', 3000),
]
if SIMULATE_WINCHES:
    WINCH_ADDRESSES = []
    for index in range(len(fixing_points)):
        WINCH_ADDRESSES.append(('localhost', TCP_BASE_PORT_WINCHES+index))

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
        WINCH_ADDRESSES = []
        for index in range(len(fixing_points)):
            WINCH_ADDRESSES.append(('localhost', TCP_BASE_PORT_WINCHES+index))
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
        (address, port) = client_connection.getsockname()
        print "Received connection on port %d" % port
    except:
        client_connected = False

    return(client_connected, client_connection)

# ------------------------------------------------------------------------------
# Check for server
#
def connect_to_server(ip_address, tcp_port):
    server_socket = None
    try:
        # server_socket = socket.socket()
        # server_socket.connect((ip_address, tcp_port))
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        server_socket.connect((ip_address, tcp_port))
    except:
        server_socket = None
        # pass
    return(server_socket)

# ------------------------------------------------------------------------------
# Get data from client
#
def get_client_data(client_connection):
    # print client_connection.fileno()
    # print client_connection.getpeername()
    # print client_connection.getsockname()
    # print client_connection.gettimeout()
    # print "checking for data from %s, port %d" % (client_connection.getsockname())
    client_connected = True
    data_received = True
    data = ''
    try:
        data = client_connection.recv(TCP_BUFFER_SIZE)
    except Exception as e:
        error_id = e.errno
        # print str(error_id) + ' : ' + str(e)
        (address, port) = client_connection.getsockname()
        if error_id == 104:  # Connection reset by peer
            if VERBOSE >= 1:
                print "End of connection to port %d" % port
            client_connection.close()
            client_connected = False
            data_received = False
        # elif error_id == 107:  # Transport endpoint is not connected
        #     if VERBOSE >= 1:
        #         print "End of connection to port %d" % port
        #     client_connection.close()
        #     client_connected = False
        #     data_received = False
        elif str(e) == 'timed out':
            if VERBOSE >= 3:
                print "Waiting for data on port %d" % port
            data_received = False
        else:
            print "Exception %s on port %d" % (str(e), port)

    data = data.rstrip()
    if (len(data) == 0) and data_received:
        (address, port) = client_connection.getsockname()
        if VERBOSE >= 1:
            print "End of connection to port %d" % port
        data_received = False
        client_connected = False

    return(client_connected, data_received, data)

# ------------------------------------------------------------------------------
# Send data to client
#
def send_client_data(client_connection, client_name, data):
    client_connected = True
    try:
        client_connection.send(data)
    # except socket.error:
    except:
        client_connection.close()
        client_connected = False

    if not client_connected:
        if VERBOSE >= 1:
            print(client_name + ' not connected')

    return(client_connected)

# ------------------------------------------------------------------------------
# Send data to server
#
def send_server_data(server_connection, server_name, data):
    server_connected = True
    print data
    try:
        server_connection.send(data + "\n")
    # except socket.error:
    except:
        server_connected = False

    if not server_connected:
        if VERBOSE >= 1:
            print(server_name + ' not connected')

    return(server_connected)

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
            elif (code_id >= 131) and (code_id <= 130+winch_nb):
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
# parse length value
#
def g_length(parameters):
    """returns a length from a g-code"""
                                                                 # default value
    length = 0
                                                                    # parse text
    params = parameters.split(' ')
    for param in params:
        coordinate = param[0]
        value = float(param[1:])
        if coordinate == 'l':
            length = value

    return(length)

# ------------------------------------------------------------------------------
# parse winch id
#
def g_motor(parameters):
    """returns a motor (winch) id from a g-code"""
                                                                 # default value
    motor_id = 0
                                                                    # parse text
    params = parameters.split(' ')
    for param in params:
        coordinate = param[0]
        value = int(param[1:])
        if coordinate == 'm':
            motor_id = value

    return(motor_id)

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
    lengths = np.zeros(len(fixing_points))
    for fixing_index in range(len(fixing_points)):
        temp = 0
        for coordinate_index in range(len(position)):
            temp = temp + (
                position[coordinate_index] -
                fixing_points[fixing_index][coordinate_index]
            )**2
        lengths[fixing_index] = np.sqrt(temp)
    return(lengths)

# ------------------------------------------------------------------------------
# Interpret command
#
def interpret_command(code_type, code_id, code_params):
    global winch_nb
    global absolute_displacement
    global actual_position
    global actual_orientation
    global actual_speed
    lander_command = ''
    winches_commands = []
    displacement = [0, 0, 0]
    if code_type == 'g':
        #                                                        lander commands
        if (code_id == 0) or (code_id == 1):
            #                                                 lander orientation
            if re.search('u', code_params):
                actual_orientation = \
                    g_orientation(code_params, actual_orientation)
                lander_command = "G%d U%d v%d" \
                    % (code_id, actual_orientation[0], actual_orientation[1])
                if code_id == 1:
                    actual_speed = g_speed(code_params, actual_speed)
                    lander_command = lander_command + " F%d" % actual_speed
            #                                                   winches commands
            if re.search('x', code_params):
                next_position = g_coordinates(code_params, (0, 0, 0))
                for index in range(len(actual_position)):
                    if absolute_displacement:
                        displacement[index] = next_position[index] \
                            - actual_position[index]
                    else:
                        displacement[index] = next_position[index]
                    actual_position[index] += displacement[index]
                lengths = position_to_lengths(actual_position, fixing_points)
                # Fix for the length of initial positions
                lengths_initial = position_to_lengths(
                    inital_position, fixing_points
                )
                for i, o in enumerate(lengths_initial):
                    lengths[i] -= o
                for l in lengths:
                    winches_commands.append(
                        "G%d X%d" % (code_id, l)
                    )
                if code_id == 1:
                    actual_speed = g_speed(code_params, actual_speed)
                    print "actual speed : %d" % actual_speed
                    total_displacement = 0.0
                    for distance in displacement:
                        total_displacement += distance**2
                    total_displacement = total_displacement ** 0.5
                    print lengths
                    print total_displacement
                    for index in range(len(winches_commands)):
                        ratio = 1.0
                        if total_displacement > 0:
                            ratio = abs(lengths[index])/total_displacement
                        winch_speed = int(ratio*actual_speed)
                        print "speed of winch %d : %d" % (index, winch_speed)
                        winches_commands[index] += " F%d" % winch_speed
        #                                                                   wait
        elif code_id == 4:
            wait_delay = g_time(code_params)
            if VERBOSE >= 1:
                print(3*INDENT + "waiting for %.3f sec." % (wait_delay))
            time.sleep(wait_delay)
        #                                                   single winch command
        elif code_id == 6:
            next_position = g_length(code_params)
            actual_speed = g_speed(code_params, actual_speed)
            motor_id = g_motor(code_params)
            actual_speed = g_speed(code_params, actual_speed)
            if VERBOSE >= 1:
                print(
                    3*INDENT + "moving winch %d to %d at speed %d" \
                    % (motor_id, next_position, actual_speed)
                )
            winches_commands.append(
                "G1 X%d F%d" \
                % (next_position, actual_speed)
            )
        #                                                  absolute displacement
        elif code_id == 90:
            if VERBOSE >= 1:
                print(3*INDENT + 'Switching to absolute displacements')
            absolute_displacement = True
        #                                                  relative displacement
        elif code_id == 91:
            if VERBOSE >= 1:
                print(3*INDENT + 'Switching to relative displacements')
            absolute_displacement = True
    if code_type == 'm':
        #                                                          fixing points
        if (code_id > 130) and (code_id <= 130 + winch_nb):
            index = code_id - 131
            while len(fixing_points) < index+1:
                fixing_points.append([0.0, 0.0, 0.0])
            winch_nb = len(fixing_points)
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
#                                                                  lander socket
lander_socket = open_socket(TCP_IP_ADDRESS, TCP_PORT_LANDER)
print INDENT + 'for lander on TCP/IP port ' + str(TCP_PORT_LANDER)
#                                                                  winch sockets
print 'Trying to connect to winches'
winch_sockets = []
for (address, port) in WINCH_ADDRESSES:
    winch_socket = connect_to_server(address, port)
    winch_sockets.append(winch_socket)
    if winch_socket:
        print INDENT + 'Connected to winch ' + address
    else:
        print INDENT + 'Not connected to winch ' + address

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
    if VERBOSE >= 3:
        if not gamer_connected:
            print 'Waiting for gamer connection'
        if not gamer_status_connected:
            print 'Waiting for gamer status connection'
    #                                                     test lander connection
    if not lander_connected:
        (lander_connected, lander_conn) = connect_to_client(lander_socket)
    if VERBOSE >= 3:
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
                    #                                send command to single winch
                    if code_id == 6:
                        winch_id = g_motor(code_params)
                        socket = winch_sockets[winch_id]
                        if SEND_G_CODES:
                            server_connected = send_server_data(
                                socket,
                                WINCH_ADDRESSES[winch_id][0],
                                winches_commands[0]
                            )
                            if not server_connected:
                                (address, port) = WINCH_ADDRESSES[winch_id]
                                print "reconnectong to %s : %d" % (address, port)
                                winch_socket = connect_to_server(address, port)
                                print winch_socket
                                winch_sockets[winch_id] = winch_socket
                        elif VERBOSE > 0:
                            print("-> " + winches_commands[0])
                    #                                    send command to winches
                    else:
                        for (index, command) in enumerate(winches_commands):
                            socket = winch_sockets[index]
                            if SEND_G_CODES:
                                if socket:
                                    socket.send(command + '\n')
                            elif VERBOSE > 0:
                                print("-> " + command)
                    if lander_connected:
                        if lander_command != '':
                            if valid:
                                reply = 'OK'
#                                if VERBOSE >= 1:
                                if VERBOSE >= 0:
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
