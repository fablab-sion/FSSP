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
TCP_PORT = 16000
CODE_FILE = 'cartesian.txt'
END_DELAY = 3.0

USAGE = 'tcp_client.py -i <ip_addr> -p <port>'

try:
    opts, args = getopt.getopt(sys.argv[1:], "hvp:i:",["port=", "ip="])
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
    elif opt in ('-n', '--packets'):
        PACKET_NB = int(arg)
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
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
s.connect((TCP_IP_ADDRESS, TCP_PORT))
s.settimeout(0.01)
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
        s.send(line + "\n")
        try:
            response = s.recv(TCP_BUFFER_SIZE)
            print 2*INDENT + response.rstrip()
        except:
            print 2*INDENT + 'no response'
time.sleep(END_DELAY)
try:
    response = s.recv(TCP_BUFFER_SIZE)
    print response
except:
    print ''
s.close()
