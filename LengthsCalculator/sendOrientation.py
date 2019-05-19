#!/usr/bin/env python

import socket
import time
import sys, getopt

# ------------------------------------------------------------------------------
# Constants
#
TCP_BUFFER_SIZE = 20  # Normally 1024, but we want fast response
TCP_BUFFER_SIZE = 1024

MAX_ANGLE = 30

INDENT = '  '

# ------------------------------------------------------------------------------
# Command line options
#
TCP_IP_ADDRESS = 'geneKranz.local'
TCP_PORT = 16005
SEND_DELAY = 1.0

USAGE = 'sendOrientation.py -i <ip_addr> -p <port>'

try:
    opts, args = getopt.getopt(sys.argv[1:], "hp:i:",["port=","ip="])
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

# ==============================================================================
# Main
#
# ------------------------------------------------------------------------------
# Open socket
#
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((TCP_IP_ADDRESS, TCP_PORT))
s.listen(1)
print 'Listening to TCP/IP port ' + str(TCP_PORT)
print INDENT + 'on "' + TCP_IP_ADDRESS + '"'

# ------------------------------------------------------------------------------
# Run server and restart a new one when client has disconnected
#
pitch = 0
yaw = 0
while True:
                                                               # open connection
    conn, addr = s.accept()
    print 'Received connection from', addr[0]
                                                            # send start command
    conn.send("g28\n")
    time.sleep(SEND_DELAY)
                                                    # loop on current connection
    while True:
                                                              # check for status
        try:
            data = conn.recv(TCP_BUFFER_SIZE)
        except socket.error:
            break
        if not data: break
        print INDENT + 'received "' + data.rstrip() + '"'
                                                            # update orientation
        if yaw = 0:
          if pitch < MAX_ANGLE:
            pitch = pitch + 1
          else
            yaw = yaw + 1
        elif pitch = MAX_ANGLE:
          if yaw < MAX_ANGLE:
            yaw = yaw + 1
          else
            pitch = pitch - 1
        elif yaw = MAX_ANGLE:
          if pitch > 0:
            pitch = pitch - 1
          else
            yaw = yaw + 1
        elif pitch = 0:
          if yaw > 0:
            yaw = yaw - 1
          else
            pitch = pitch + 1
                                                      # send orientation command
        conn.send(data)  # echo
        time.sleep(SEND_DELAY)

    conn.close()
