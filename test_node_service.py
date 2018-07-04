from __future__ import print_function
from node_service import NodeService
from callback_table import CallbackTable
from node import DHTNode
from udp_node_proxy import UdpNodeProxy
from threading import Timer
def main():
	# send request from B to A
	# that means B needs to have a proxy to A

	nodeA = DHTNode(id=0)
	class global_vars_a:
		node_id = nodeA.id
		callback_table = CallbackTable()
		host = '127.0.0.1'
		service_port = 6666

	nodeB = DHTNode(id=1)
	class global_vars_b:
		node_id = nodeB.id
		callback_table = CallbackTable()
		host = '127.0.0.1'
		service_port = 6667

	serviceA = NodeService(nodeA, global_vars_a)
	serviceB = NodeService(nodeA, global_vars_b)
	serviceA.start()
	serviceB.start()
	proxy_b_to_a = UdpNodeProxy(nodeA.id, global_vars_a.host, global_vars_a.service_port, global_vars_b)
	nodeB.join_network(proxy_b_to_a, lambda _: print('B JOINED NETWORK'))
	'''def send_store_request_b_to_a():
		print('Sent store request from B to A')
		proxy_b_to_a.store(nodeB.hash('hello'), 'world', print)
	def send_find_value_request_b_to_a():
		print('Sent find_value request from B to A')
		proxy_b_to_a.find_value(nodeB.hash('hello'), proxy_a_to_b, print)
	Timer(0.3, send_store_request_b_to_a).start()
	Timer(0.6, send_find_value_request_b_to_a).start()'''
	Timer(1, serviceA.stop).start()
	Timer(1, serviceB.stop).start()

if __name__ == '__main__':
	main()