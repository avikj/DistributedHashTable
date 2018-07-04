import socket
from node_proxy import NodeProxy
from node_client import NodeClient
class UdpNodeProxy(NodeProxy):
	def __init__(self, remote_node_id, remote_host, remote_port, global_vars):
		'''
		self.local_node_host = local_node_host
		self.local_node_service_port = local_node_service_port
		self.callback_table = callback_table
		'''
		self.global_vars = global_vars
		self.remote_node_id = remote_node_id
		self.remote_host = remote_host
		self.remote_port = remote_port

	def node_id(self):
		return self.remote_node_id
	# callback param: success/failure
	def store(self, key, value, callback):
		self.create_node_client().send_request({
			'method': 'STORE',
			'key': key,
			'value': value
		}, (self.remote_host, self.remote_port), lambda response_dict: callback(response_dict['success']))

	# callback param: whether the node is alive	
	# implement a timeout or something so this doesnt just return true or never reply
	def ping(self, callback):
		self.create_node_client().send_request({
			'method': 'PING',
		}, (self.remote_host, self.remote_port), lambda response_dict: callback(True))
		
	
	# callback param: k closest nodes to the search key
	# doesn't use requester proxy parameter because the requester will always be the node running the local_node_client
	def find_node(self, search_key, requester_proxy, callback):
		self.create_node_client().send_request({
			'method': 'FIND_NODE',
			'search_key': search_key,
		}, (self.remote_host, self.remote_port), lambda response_dict: callback(
			[
				UdpNodeProxy(node_dict['node_id'], node_dict['host'], node_dict['port'], self.global_vars) 
				for node_dict 
				in response_dict['nodes']
			]
		))

	# first return value: whether the value was found
	# second return value: value if it was found at this node, else closest neighbors to the key
	def find_value(self, search_key, requester_proxy, callback):
		self.create_node_client().send_request({
			'method': 'FIND_VALUE',
			'search_key': search_key,
		}, (self.remote_host, self.remote_port), lambda response_dict: callback(response_dict['found'],
			response_dict['value']
			if 
			response_dict['found']
			else
			[
				UdpNodeProxy(node_dict['node_id'], node_dict['host'], node_dict['port'], self.global_vars) 
				for node_dict 
				in response_dict['nodes']
			]
		))

	def create_node_client(self):
		return NodeClient(self.global_vars)

	def as_dict(self):
		return {
			'node_id': self.remote_node_id,
			'host': self.remote_host,
			'port': self.remote_port
		}

	def __repr__(self):
		return 'DHTNodeProxy(%s, %s:%d)'%(self.remote_node_id, self.remote_host, self.remote_port)