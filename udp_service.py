import socket
import threading
import logging
import traceback

class UdpService(threading.Thread):
	def __init__(self, host='127.0.0.1', port=5000, timeout=0.01):
		threading.Thread.__init__(self)
		self.host = host
		self.port = port

		self.stopped = False

		self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # Internet, UDP
		self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
		self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.sock.settimeout(timeout)

		self.sock.bind((self.host, self.port))

	def run(self):
		logging.info('UdpService listening at %s:%d'%(self.host, self.port))
		while not self.stopped:
			try:
				data, addr = self.sock.recvfrom(1024) # buffer size is 1024 bytes
				self.handle_message(data, addr)
			except Exception as e: 
				if not isinstance(e, socket.timeout):
					logging.error(traceback.format_exc())
		self.sock.close()
	def handle_message(self, data, addr):
		pass

	def send_message(self, data, addr):
		self.sock.sendto(data, addr)
		logging.info('Sent %s to %s:%d'%(data, addr[0], addr[1]))

	def stop(self):
		self.stopped = True
if __name__ == '__main__':
	s = UdpService()
	s.start()
	print 'started service'