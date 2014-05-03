import socket
import struct
import string
import binascii

from chosen_plaintext import ChosenPlaintext

HOST = '127.0.0.1'    # The remote host
PORT = 30000          # The same port as used by the server

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

class Client(ChosenPlaintext):

	def __init__(self):
		ChosenPlaintext.__init__(self)
		return

	def ciphertext(self, plaintext):

		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect((HOST, PORT))

		send_blob(s, plaintext)
		data = recv_blob(s)

		s.close()
		return data

c = Client()
c.run()
print 'recovered', repr(c.plaintext)
