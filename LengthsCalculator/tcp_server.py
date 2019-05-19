#!/usr/bin/env python

import socket
import time
import sys, getopt

# ------------------------------------------------------------------------------
# Constants
#
TCP_BUFFER_SIZE = 20  # Normally 1024, but we want fast response
TCP_BUFFER_SIZE = 1024

INDENT = '  '

# ------------------------------------------------------------------------------
# Command line options
#
TCP_IP_ADDRESS = 'geneKranz.local'
TCP_PORT = 16000

USAGE = 'tcp_server.py -i <ip_addr> -p <port>'

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
previous = time.time()
while True:
    conn, addr = s.accept()
    print 'Received connection from', addr[0]
    while True:
        try:
            data = conn.recv(TCP_BUFFER_SIZE)
        except socket.error:
            break
        if not data: break
        now = time.time()
        print INDENT + 'received "' + data.rstrip() + '"'
        print 2*INDENT + 'after ' + str(int((now - previous) * 1000.0)) + ' ms'
        previous = now
        conn.send(data)  # echo
    conn.close()
