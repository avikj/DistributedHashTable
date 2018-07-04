from __future__ import print_function
import threading
import time
import uuid
import math
import random
import networkx as nx 
import matplotlib.pyplot as plt 
import hashlib
import progressbar
from simulated_node_proxy import SimulatedNodeProxy
import heapq
import threading
import logging



class DHTNode():
	def __init__(self, id=None, K=20, BIT_COUNT=16):
		self.K = K
		self.BIT_COUNT = BIT_COUNT
		self.id = id
		if id is None:
			self.id = int(uuid.uuid4()) % (1 << self.BIT_COUNT)
		self.routing_table = [[] for i in range(self.BIT_COUNT)]
		self.data = {}
		self.proxy = SimulatedNodeProxy(self)

	def __repr__(self):
		return 'DHTNode(id=%s)'%format(self.id,'0%db'%self.BIT_COUNT)

	########## Network Protocol #################################
	def check_compatibility(self):
		return self.K, self.BIT_COUNT

	def store(self, key, value):
		if not self.is_valid_key(key):
			raise ValueError('Key %s is invalid format.'%str(key))
		self.data[key] = value
		logging.info('Stored key %s at node %s.'%(self.format_bin(key), self))

	# return k closest (XOR distance) neighbors to search id
	def find_node(self, search_key, requester_proxy):
		logging.info("find_node(%s) called on %s"%(self.format_bin(search_key), self))
		all_neighbors = self.all_neighbors()
		all_neighbors.sort(key=DHTNode.dist_from(search_key))
		self.update_table(requester_proxy)
		return [neighbor for neighbor in all_neighbors[:self.K]] #if (neighbor.node_id()^search_key < self.id^search_key)]

	# first return value: whether the value was found
	# second return value: value if found else closest neighbors
	def find_value(self, search_key, requester_proxy):
		if search_key in self.data:
			return True, self.data[search_key]
		all_neighbors = self.all_neighbors()
		all_neighbors.sort(key=DHTNode.dist_from(search_key))
		self.update_table(requester_proxy)
		return False, all_neighbors[:self.K]

	##########Functions for Node's Own Use#########################
	def update_table(self, encountered_node_proxy):
		if encountered_node_proxy.node_id() == self.id:
			return
		kbucket_index = 0
		x = self.id ^ encountered_node_proxy.node_id()
		while x != 1:
			x >>= 1
			kbucket_index += 1
		# print 'Placing %s in the %dth bucket of %s, since xor was %s'%(encountered_node_proxy, kbucket_index, self, format(self.id^encountered_node_proxy.id, '0%db'%self.BIT_COUNT))
		if len(self.routing_table[kbucket_index]) > self.K:
			pass # TODO determine whether nodes already in list are active, otherwise replace with new one
		elif encountered_node_proxy.node_id() not in {proxy.node_id() for proxy in self.routing_table[kbucket_index]}:
			self.routing_table[kbucket_index].append(encountered_node_proxy)

	# run the algorithm to actually find nodes closest to a given hash
	# TODO remove repeats
	def locate_nodes_near_key(self, search_key, located_nodes_callback, alpha=3):
		logging.info('%s is locating nodes near %s'%(self, self.format_bin(search_key)))
		# find alpha nodes in routing table closest to key
		# list of tuples: (dist_from_search_key, node_proxy)
		nodes = sorted([(neighbor.node_id()^search_key, neighbor) for neighbor in self.all_neighbors()])[:alpha]
		queried = set() # set of node id's that we've already queried
		# callback factory
		def found_nodes_callback_with_event(event):
			def found_nodes_callback(returned_nodes):
				logging.info('found_nodes_callback called and event was set')
				nodes.extend([(search_key^node_proxy.node_id(), node_proxy) for node_proxy in returned_nodes])
				event.set()
			return found_nodes_callback
		while True:
			# pick alpha nodes that have not yet been queried (out of the first k)
			nodes_to_query = []
			i = 0
			while len(nodes_to_query) < alpha and i < self.K and i < len(nodes):
				if nodes[i][1].node_id() not in queried:
					nodes_to_query.append(nodes[i][1])
					queried.add(nodes[i][1].node_id())
				i += 1
			if len(nodes_to_query) == 0: # search is complete
				break
			# query the alpha chosen nodes and wait for a response from all of them
			completion_events = []
			for node_proxy in nodes_to_query:
				event = threading.Event()
				completion_events.append(event)
				node_proxy.find_node(search_key, self.proxy, found_nodes_callback_with_event(event))
			for event in completion_events:
				logging.info('Waiting for found_nodes_callback')
				event.wait()
				logging.info('Done waiting for found_nodes_callback')
			nodes.sort()
			nodes = nodes[:self.K]
		located_nodes_callback([node_proxy for dist, node_proxy in nodes])

	# returns found, value
	def find_value_in_network(self, key, found_value_in_network_callback):
		# callback factory function (closure)
		def found_value_in_node_callback_with_events(success_event, completed_event): # success event is shared among callbacks
			def found_value_in_node_callback(found, value):

				if found and not success_event.is_set():
					success_event.set()
					found_value_in_network_callback(True, value)
				completed_event.set()
			return found_value_in_node_callback
		def located_nodes(nodes):
			completion_events = []
			success_event = threading.Event()
			for node in nodes:
				completed_event = threading.Event()
				completion_events.append(completed_event)
				node.find_value(key, self.proxy, found_value_in_node_callback_with_events(success_event, completed_event))
			for event in completion_events:
				event.wait()
			if not success_event.is_set():
				found_value_in_network_callback(False, None)
		self.locate_nodes_near_key(key, located_nodes)

	def find_bucket(self, node_id):
		if self.id == node_id:
			raise ValueError('Calling find_bucket with node_id == self.id')
		x = self.id ^ node_id
		kbucket_index = 0
		while x != 1:
			x >>= 1
			kbucket_index += 1
		return kbucket_index

	# callback parameter: success
	def join_network(self, bootstrap_node_proxy, joined_network_callback):
		if self.id == bootstrap_node_proxy.node_id():
			raise ValueError('Can\'t bootstrap with self')
		'''if self.K != bootstrap_node_proxy.K:
			raise ValueError('Can\'t join network with different k    ')
		if self.BIT_COUNT != bootstrap_node_proxy.BIT_COUNT:
			raise ValueError('Can\'t join network with different BIT_COUNT value')'''
			# joined_network_callback(False)
		logging.info('%s is joining network using %s as bootstrap'%(self, bootstrap_node_proxy))
		self.update_table(bootstrap_node_proxy)

		# callback factory
		def located_nodes_with_event(event):
			def located_nodes(nodes):
				event.set()
			return located_nodes
		def located_nodes_near_self(nodes):
			logging.info('Self lookup for %s completed.'%self)
			# refresh k-buckets further away than bootstrap node
			kbucket_index = self.find_bucket(bootstrap_node_proxy.node_id())
			completion_events = []
			for refresh_bit in range(kbucket_index, self.BIT_COUNT): # refresh by looking up an id in the range of each larger kbucket
				event = threading.Event()
				completion_events.append(event)
				self.locate_nodes_near_key((1<<refresh_bit)+random.randint(0,1<<refresh_bit), located_nodes_with_event(event))
			for event in completion_events:
				event.wait()
			joined_network_callback(True)
		self.locate_nodes_near_key(self.id, located_nodes_near_self) # self lookup populates other nodes with this one's id
		
	def all_neighbors(self):
		all_neighbors = []
		for kbucket in self.routing_table:
			for node in kbucket:
				all_neighbors.append(node)
		return all_neighbors

	# locate nodes closest to key in the network, and store the key/value pair in them
	# callback param: nodes where values was stored
	def store_in_network(self, key, value, stored_in_network_callback):

		def located_nodes(node_proxies):
			completion_events = []
			for node in node_proxies:
				event = threading.Event()
				completion_events.append(event)
				node.store(key, value, lambda _: event.set())
			for event in completion_events:
				event.wait()
			stored_in_network_callback(node_proxies)
		self.locate_nodes_near_key(key, located_nodes)

	def format_bin(self, key):
		return format(key,'0%db'%self.BIT_COUNT)
	def hash(self, input):
		m = hashlib.sha1()
		m.update(input)
		return int(m.hexdigest(), 16) % (1 << self.BIT_COUNT)
	def is_valid_key(self, key):
		if not isinstance(key, (int, long)):
			return False
		if key < 0 or key >= 1<<self.BIT_COUNT:
			return False
		return True
	@staticmethod
	def dist_from(search_key):
		return lambda node_proxy: (node_proxy.node_id() ^ search_key)

def main():
	logging.basicConfig(level=logging.ERROR)
	n_nodes = 1000
	# print 'Added %s'%(bin(nodes[0].id))
	# add nodes and bootstrap each with a random previously included node
	print('Initializing nodes in simulation...')
	with progressbar.ProgressBar(max_value=n_nodes) as bar:
		nodes = [DHTNode()]
		while(len(nodes) < n_nodes):
			logging.info('len(nodes): %d'%len(nodes))
			nodes.append(DHTNode())
			event = threading.Event()
			logging.info('%s is joining network'%nodes[-1])
			nodes[-1].join_network(nodes[random.randint(0, len(nodes)-2)].proxy, lambda _: event.set())
			logging.info('waiting for callback event from join_network for %s'%nodes[-1])
			event.wait()
			logging.info('Done waiting for callback event from join_network')
			# print 'Adding %s'%(bin(nodes[-1].id))
			bar.update(len(nodes))

	unhashed_key = str(random.randint(0, 10000000000))

	def stored_in_network_callback(_):
		print('stored at nodes %s'%_)
		nodes[999].find_value_in_network(DHTNode.hash(unhashed_key), print)
	print(len(nodes))
	nodes[998].store_in_network(DHTNode.hash(unhashed_key), 'asdf', stored_in_network_callback) # hash function TODO

	'''
	G = nx.DiGraph()
	for node in nodes:
		G.add_node(node.id)
		print node, len(node.all_neighbors())
	for node in nodes:
		for neighbor in node.all_neighbors():
			G.add_edge(node.id, neighbor.id)'''
	'''
	plt.subplot(111)
	nx.draw(G, node_size=30)
	plt.show()
	'''

if __name__ == '__main__':
	main()