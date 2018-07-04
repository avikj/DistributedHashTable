from threading import Lock
class CallbackTable:
	def __init__(self): 
		self.table = {}
		self.mutex = Lock()

	def sent_request(self, msg_id, callback):
		self.mutex.acquire()
		self.table[msg_id] = callback
		self.mutex.release()

	def received_response(self, msg_id, response_dict):
		self.mutex.acquire()
		callback = self.table.pop(msg_id)
		callback(response_dict)
		self.mutex.release()