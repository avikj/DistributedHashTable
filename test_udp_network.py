from node_service import NodeService

def main():
	# initialize DHTNodes and associated NodeServices
	n_nodes = 10
	node_services = [NodeService(DHTNode(), port=6000+i) for i in range(20)]
	for i in range(n_nodes):
