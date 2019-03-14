from ByteOutputBuffer import ByteOutputBuffer

class ArithmeticEncoderStats:
	contextSize = None
	I = []
	mPS = []
	
	def __init__(self, contextSize):
		self.contextSize = contextSize
		self.I = [0]*contextSize
		self.mPS = [0]*contextSize
	
	def reset(self):
		self.codingContextTable = [0]*self.contextSize
	
	def getContextCodingTableValue(self, index):
		return self.codingContextTable[index]
	
	def setContextCodingTableValue(self, index, value):
		self.codingContextTable[index] = value
	
	def getContextSize(self):
		return self.contextSize
	
class ArithmeticEncoder:
	iadhStats  = ArithmeticEncoderStats(1 << 9);
	iadwStats  = ArithmeticEncoderStats(1 << 9);
	iaexStats  = ArithmeticEncoderStats(1 << 9);
	iaaiStats  = ArithmeticEncoderStats(1 << 9);
	iadtStats  = ArithmeticEncoderStats(1 << 9);
	iaitStats  = ArithmeticEncoderStats(1 << 9);
	iafsStats  = ArithmeticEncoderStats(1 << 9);
	iadsStats  = ArithmeticEncoderStats(1 << 9);
	iardxStats = ArithmeticEncoderStats(1 << 9);
	iardyStats = ArithmeticEncoderStats(1 << 9);
	iardwStats = ArithmeticEncoderStats(1 << 9);
	iardhStats = ArithmeticEncoderStats(1 << 9);
	iariStats  = ArithmeticEncoderStats(1 << 9);
	iaidStats  = ArithmeticEncoderStats(1 << 1);
	
	# The data structures containing the probabilities for the LPS
	qe = [0x5601, 0x3401, 0x1801, 0x0ac1, 0x0521, 0x0221, 0x5601,\
			   0x5401, 0x4801, 0x3801, 0x3001, 0x2401, 0x1c01, 0x1601,\
			   0x5601, 0x5401, 0x5101, 0x4801, 0x3801, 0x3401, 0x3001,\
			   0x2801, 0x2401, 0x2201, 0x1c01, 0x1801, 0x1601, 0x1401,\
			   0x1201, 0x1101, 0x0ac1, 0x09c1, 0x08a1, 0x0521, 0x0441,\
			   0x02a1, 0x0221, 0x0141, 0x0111, 0x0085, 0x0049, 0x0025,\
			   0x0015, 0x0009, 0x0005, 0x0001, 0x5601]
	
	# The indexes of the next MPS
	nMPS = [1 , 2, 3, 4, 5,38, 7, 8, 9,10,11,12,13,29,15,16,17,\
					 18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,\
					 35,36,37,38,39,40,41,42,43,44,45,45,46]
	
	# The indexes of the next LPS
	nLPS = [1 , 6, 9,12,29,33, 6,14,14,14,17,18,20,21,14,14,15,\
					 16,17,18,19,19,20,21,22,23,24,25,26,27,28,29,30,31,\
					 32,33,34,35,36,37,38,39,40,41,42,43,46]
	
	# Whether LPS and MPS should be switched
	switchLM = [1,0,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,\
						 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
	
	# The ByteOutputBuffer used to write the compressed bit stream.
	out = None
	
	# The current bit code
	c = None
	
	# The bit code counter
	cT = None
	
	# The current interval
	a = None
	
	# The last encoded byte of data
	b = None
	
	# If a 0xFF byte has been delayed and not yet been written to the output 
	# (in the MQ we can never have more than 1 0xFF byte in a row).
	delFF = None
	
	# The number of written bytes so far, excluding any delayed 0xFF
	# bytes. Upon initialization it is -1 to indicated that the byte buffer
	# 'b' is empty as well.
	nrOfWrittenBytes = -1
	
	
	previous = None
	
	def __init__(self, _out):
		self.out = _out

		# --- INITENC
		
		self.a = 0x8000
		self.c = 0
		if self.b == 0xff:
			self.cT = 13
		else:
			self.cT = 12
		
		# End of INIENC ---
		b = 0
		
	"""
	 * This function puts one byte of compressed bits in the output stream.
	 * The highest 8 bits of c are then put in b to be the next byte to
	 * write. This method delays the output of any 0xFF bytes until a non 0xFF
	 * byte has to be written to the output bit stream (the 'delFF' variable
	 * signals if there is a delayed 0xff byte).
	"""
	def byteOut(self):
		if self.nrOfWrittenBytes >= 0:
			if self.b == 0xff:
				# Delay 0xFF byte
				self.delFF = True
				self.b = self.c>>20
				self.c &= 0xFFFFF
				self.cT = 7
			elif self.c < 0x8000000:
				# Write delayed 0xFF bytes
				if self.delFF:
					self.out.write(0xff)
					self.delFF = False
					self.nrOfWrittenBytes += 1
				self.out.write(self.b)
				self.nrOfWrittenBytes += 1
				self.b = self.c >> 19
				self.c &= 0x7FFFF
				self.cT = 8
			else:
				self.b += 1
				if self.b == 0xff:
					# Delay 0xFF byte
					self.delFF = True
					self.c &= 0x7FFFFFF
					self.b = self.c>>20
					self.c &= 0xFFFFF
					self.cT = 7
				else:
					# Write delayed 0xFF bytes
					if self.delFF:
						self.out.write(0xFF)
						self.delFF = False
						self.nrOfWrittenBytes += 1
					self.out.write(self.b)
					self.nrOfWrittenBytes += 1
					self.b = ((self.c>>19)&0xFF)
					self.c &= 0x7FFFF
					self.cT = 8
				
		else:
			self.b = (self.c >> 19)
			self.c &= 0x7FFFF
			self.cT = 8 
			self.nrOfWrittenBytes += 1

	"""
	 * This function performs the arithmetic encoding of one symbol. The 
	 * function receives a bit that is to be encoded and a context with which
	 * to encode it.
	 *
	 * <p>Each context has a current MPS and an index describing what the 
	 * current probability is for the LPS. Each bit is encoded and if the
	 * probability of the LPS exceeds .5, the MPS and LPS are switched.</p>
	 *
	 * @param bit The symbol to be encoded, must be 0 or 1.
	 *
	 * @param context the context with which to encode the symbol.
	"""
	def encodeBit(self, stats, context, bit):
		li = stats.I[context]
		q = self.qe[li]
		
		if bit == stats.mPS[context]: # Code MPS
			self.a -= q
			
			if self.a >= 0x8000: # Interval big enough
				self.c += q
			else:				 # Interval too short
				if self.a < q:
					self.a = q
				else:
					self.c += q
				
				stats.I[context] = self.nMPS[li]
				
				# -- Renormalization (MPS: no need for while loop)
				self.a <<= 1
				self.c <<= 1
				self.cT -= 1
				if self.cT == 0:
					self.byteOut()
				# -- End of renormalization

		else: # Code LPS
			la = self.a
			la -= q
			
			if la < q:
				self.c += q
			else:
				la = q
			
			if self.switchLM[li] != 0:
				stats.mPS[context] = 1 - stats.mPS[context]
			stats.I[context] = self.nLPS[li]
			
			# -- Renormalization
			n = 0
			while True:
				la <<= 1
				n += 1 # count number of necessary shifts
				if la >= 0x8000:
					break
			
			if self.cT > n:
				self.c <<= n
				self.cT -= n
			else:
				while True:
					self.c <<= self.cT
					n -= self.cT
					self.byteOut()
					if self.cT > n:
						break
				self.c <<= n
				self.cT -= n
			
			#  -- End of renormalization
			self.a = la
	
	"""
	 * This function perform encoding the integer value which is used in jbig2
	 
	 * @param v The value to be encoded
	 
	 * @param stats The ArithmeticEncoder Stats used to encoding
	"""
	def encodeInt(self, stats, v):
		self.previous = 1
		
		s = 1 if v < 0 else 0
		self.encodeIntBit(stats, s)
		
		for i in range(5):		# this part should to be fixed
			self.encodeIntBit(stats, 1)
		
		for i in range(32):
			bit = (v >> (31-i)) & 1
			self.encodeIntBit(stats, bit)
	
	
	def encodeIntBit(self, stats, bit):
		self.encodeBit(stats, self.previous, bit)
		
		if self.previous < 0x100:
			self.previous = ((self.previous << 1)&0xffffffff) | bit
		else:
			self.previous = ((((self.previous << 1)&0xffffffff) | bit) & 0x1ff) | 0x100

if __name__ == '__main__':
	out = ByteOutputBuffer()
	arithEncoder = ArithmeticEncoder(out)
	
	arithEncoder.encodeInt(arithEncoder.iadtStats, 0x31313131)
	arithEncoder.encodeInt(arithEncoder.iadtStats, 0)	# to flush the buffer
	
	print arithEncoder.out.tohex()
					