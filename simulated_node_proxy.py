from node_proxy import NodeProxy
class SimulatedNodeProxy(NodeProxy):
	def __init__(self, node):
		self.node = node

	def node_id(self):
		return self.node.id

	def store(self, key, value, callback):
		self.node.store(key, value)
		callback(True)
	
	def ping(self, callback):
		callback(self.node.is_alive())
	
	def find_node(self, search_key, requester_proxy, callback):
		callback(self.node.find_node(search_key, requester_proxy))

	# first return value: whether the value was found
	# second return value: value if it was found at this node, else closest neighbors to the key
	def find_value(self, search_key, requester_proxy, callback):
		callback(*(self.node.find_value(search_key, requester_proxy)))

	def __repr__(self):
		return str(self.node)