class ByteOutputBuffer:
	# The buffer where the data is stored
	buf = [0]*0x4000
	
	# The number of valid bytes in the buffer
	count = 0
	
	def __init__(self):
		pass
	
	# Writes the specified byte to this byte array output stream
	def write(self, b):
		self.buf[self.count] = b
		self.count += 1
	
	# Returns the number of valid bytes in the output buffer (count class
	# variable).
	def size(self):
		return self.count
	
	# Discards all the buffered data, by resetting the counter of written
	# bytes to 0
	def reset(self):
		self.count = 0
	
	# Returns the byte buffered at the given position in the buffer.
	def getByte(self, pos):
		assert pos < self.count
		
		return self.buf[pos] & 0xff
	
	# Returns all the buffered data to stream.
	def toStream(self):
		result = ''
		for i in range(self.count):
			result += chr(self.buf[i])
		return result
	
	# Returns all the buffered data to hex string
	def tohex(self):
		result = ''
		for i in range(self.count):
			result += '\\x{:02x}'.format(self.buf[i])
		return result