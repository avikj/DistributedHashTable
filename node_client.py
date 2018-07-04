from copy import deepcopy
import socket
import random
import json
class NodeClient:
	def __init__(self, global_vars, client_port=0):
		self.global_vars = global_vars

		self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # Internet, UDP
		self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
		self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

		self.sock.bind((self.global_vars.host, client_port))

	def send_request(self, request_dict, addr, callback, MSG_ID_BITS=16):
		request = deepcopy(request_dict)
		msg_id = random.randint(0, 1<<MSG_ID_BITS-1)
		request['msg_id'] = msg_id
		request['is_response'] = False
		request['requester'] = {
			'node_id': self.global_vars.node_id,
			'host': self.global_vars.host,
			'port': self.global_vars.service_port
		}
		self.global_vars.callback_table.sent_request(msg_id, callback)
		self.send_message(json.dumps(request), addr)
		print 'Sent %s to %s:%d'%(json.dumps(request), addr[0], addr[1])

	def send_message(self, data, addr):
		self.sock.sendto(data, addr)