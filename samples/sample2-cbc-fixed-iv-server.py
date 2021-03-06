import SocketServer
import zlib
import os
import struct
from Crypto.Cipher import DES

secret = "a5Sdfg#$fu7\x9f43aZxcrwe%&0988"

def encrypt(data):
    des = DES.new('01234567', DES.MODE_CBC, '09876543') # <- FIXED IV
    data += '\x00' * (8 - len(data) % 8)
    return des.encrypt(data)

def send_blob(s, data):
    s.sendall(struct.pack('<I', len(data)))
    s.sendall(data)
    return

def recv_blob(s):
    data = s.recv(4)
    length, = struct.unpack('<I', data)

    data = ''
    while len(data) < length:
        newdata = s.recv(length - len(data))
        if newdata == '':
            raise Exception('connection closed?')
        data += newdata

    return data

class MyTCPHandler(SocketServer.BaseRequestHandler):

    def handle(self):
        # self.request is the TCP socket connected to the client

        plaintext = recv_blob(self.request)
        message = "data=%s,secret=%s" % (plaintext, secret)

        ciphertext = encrypt(message)
        send_blob(self.request, ciphertext)

        self.request.close()
        return

if __name__ == "__main__":
    HOST, PORT = "0.0.0.0", 30000

    # Create the server, binding to localhost on port 9999
    SocketServer.allow_reuse_address = True
    server = SocketServer.TCPServer((HOST, PORT), MyTCPHandler)

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    server.serve_forever()
