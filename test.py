import unittest
from node import DHTNode

class DHTNodeTests(unittest.TestCase):
	def setUp(self):
		self.nodeA = DHTNode(id=0)
		self.nodeB = DHTNode(id=1)
		self.nodeC = DHTNode(id=2)
		self.nodeD = DHTNode(id=3)
	def tearDown(self):
		pass
	
	def testStoreRaisesErrorWhenKeyInvalid(self):
		unhashed_key = 'hello'
		value = 'world'
		with self.assertRaises(ValueError):
			self.nodeA.store(unhashed_key, value)

	def testStoreStoresValue(self):
		'''testing DHTNode.store()'''
		hashed_key = self.nodeA.hash('hello')
		value = 'world'
		self.nodeA.store(hashed_key, value)
		assert self.nodeA.data[hashed_key] == value, 'store() not storing values correctly'

	def testFindNodeFindsNode(self):
		'''testing DHTNode.find_node()'''

		assert self.nodeA.find_node(1, self.nodeB.proxy) == [], 'find_node() fails when there are no neighbors'
		self.nodeC.routing_table[0].append(self.nodeD.proxy)
		assert self.nodeC.find_node(3, self.nodeB.proxy) == [self.nodeD.proxy], 'find_node() fails when there is 1 neighbor'

	def testFindValue(self):
		'''testing DHTNode.find_value()'''
		assert self.nodeA.find_value(1, self.nodeB.proxy) == (False, []), 'find_value() fails when there is no value and no neighbors'
		self.nodeC.routing_table[0].append(self.nodeD.proxy)
		assert self.nodeC.find_value(3, self.nodeB.proxy) == (False, [self.nodeD.proxy]), 'find_value() fails when there is no value and 1 neighbor'

		hashed_key = self.nodeC.hash('hello')
		value = 'world'
		self.nodeC.data[hashed_key] = value
		assert self.nodeC.find_value(hashed_key, self.nodeB.proxy) == (True, value)

	def testUpdateTable(self):
		'''testing DHTNode.update_table()'''
		self.nodeA.update_table(self.nodeB.proxy)
		assert self.nodeB.proxy in self.nodeA.all_neighbors(), 'update_table() doesn\'t add the new node to the table'
		assert self.nodeB.proxy in self.nodeA.routing_table[0], 'update_table() doesn\'t add the new node in the right place'

	def testAutoUpdateTable(self):
		'''testing neighbors being added as a result of find_node calls'''
		self.nodeA.find_value(1, self.nodeC.proxy)
		assert self.nodeC.proxy in self.nodeA.all_neighbors()
if __name__ == '__main__':
	unittest.main() # run all tests