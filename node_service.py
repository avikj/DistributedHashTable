from udp_service import UdpService
from udp_node_proxy import UdpNodeProxy
import json
import random
from copy import deepcopy
import logging

class NodeService(UdpService):
	# global_vars should contain node_id, callback_table, host, service_port
	def __init__(self, node, global_vars, timeout=0.01):

		logging.basicConfig(level=logging.INFO)
		UdpService.__init__(self, host=global_vars.host, port=global_vars.service_port, timeout=timeout)
		self.global_vars = global_vars
		self.node = node
	# All responses we send are JSON, must supply entries for 'is_response', 'method', and 'msg_id'
	# Received messages where is_response is true are responses to requests we previously sent
	def handle_message(self, raw_data, addr):
		print('received message: %s'%raw_data)
		if raw_data == 'close':
			self.sock.close()
			return
		data = json.loads(raw_data)
		# Peer uses this to ensure that K value and BIT_COUNT are the same among the nodes
		if data['is_response'] == True:
			self.global_vars.callback_table.received_response(data['msg_id'], data) # TODO associate timestamp, timeout
			return
		if data['method'] == 'CHECK_COMPATIBILITY':
			self.send_message(json.dumps({
				'is_response': True,
				'msg_id': data['msg_id'],
				'K': self.node.K,
				'BIT_COUNT': self.node.BIT_COUNT
			}), addr)
		# Peer uses this to check if node is online
		elif data['method'] == 'PING':
			self.send_message(json.dumps({
				'is_response': True,
				'msg_id': data['msg_id']
			}), addr)
		# Peer uses this to store data at this node
		elif data['method'] == 'STORE':
			try:
				self.node.store(data['key'], data['value'])
				self.send_message(json.dumps({
					'is_response': True,
					'msg_id': data['msg_id'],
					'success': True
				}), (data['requester']['host'], data['requester']['port']))
			except ValueError:
				self.send_message(json.dumps({
					'is_response': True,
					'msg_id': data['msg_id'],
					'success': False
				}), (data['requester']['host'], data['requester']['port']))
		# Peer uses this to get list of nodes closer to a given node
		elif data['method'] == 'FIND_NODE':
			node_proxies = self.node.find_node(data['search_key'], self.create_requester_node_proxy(data)) 
			self.send_message(json.dumps({
				'is_response': True,
				'msg_id': data['msg_id'],
				'nodes': [node.as_dict() for node in node_proxies]
			}), (data['requester']['host'], data['requester']['port']))
		elif data['method'] == 'FIND_VALUE':
			found, result = self.node.find_value(data['search_key'], self.create_requester_node_proxy(data))
			if found:
				self.send_message(json.dumps({
					'is_response': True,
					'msg_id': data['msg_id'],
					'found': True,
					'value': result
				}), (data['requester']['host'], data['requester']['port']))
			else:
				self.send_message(json.dumps({
					'is_response': True,
					'msg_id': data['msg_id'],
					'found': False,
					'nodes': [node.as_dict() for node in result]
				}), (data['requester']['host'], data['requester']['port']))

	def create_requester_node_proxy(self, request_dict):
		return UdpNodeProxy(request_dict['requester']['node_id'], request_dict['requester']['host'], request_dict['requester']['port'],
								self.global_vars)