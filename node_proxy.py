import abc

# abstract interface to other remote nodes (or simulated)
class NodeProxy():
	@abc.abstractmethod
	def node_id(self):
		pass

	# callback param: success/failure
	@abc.abstractmethod
	def store(self, key, value, callback):
		pass

	# callback param: whether the node is alive
	@abc.abstractmethod
	def ping(self, callback):
		pass

	# callback param: k closest nodes to the search key
	@abc.abstractmethod
	def find_node(self, search_key, requester_proxy, callback):
		pass

	# first callback param: whether the value was found
	# second callback param: value if found else closest neighbors
	@abc.abstractmethod
	def find_value(self, search_key, requester_proxy, callback):
		pass
