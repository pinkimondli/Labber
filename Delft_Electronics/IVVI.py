import InstrumentDriver
import numpy as np
import os, sys, inspect, re, math
from VISA_Driver import VISA_Driver
from BaseDriver import LabberDriver
import visa
from pyvisa.resources.serial import SerialInstrument
import time

class Driver(LabberDriver):
	
	def performOpen(self, options={}):
		self.visa_handle = visa.ResourceManager().open_resource(self.getAddress())
		
		"""Perform the operation of opening the instrument connection"""
		self.visa_handle.parity=self.visa_handle.parity.odd
		self.visa_handle.baud_rate=115200
		self.visa_handle.write_termination=None
		self.visa_handle.read_termination=None
		
		# disable all termination characters
		self.visa_handle.set_visa_attribute(0x3FFF0038,0) # VI_ATTR_TERMCHAR_EN
		self.visa_handle.set_visa_attribute(0x3FFF00B3,0) # VI_ATTR_ASRL_END_IN
		self.visa_handle.set_visa_attribute(0x3FFF00B4,0) # VI_ATTR_ASRL_END_OUT
		self.visa_handle.set_visa_attribute(0x3FFF0016,0) # VI_ATTR_SEND_END_EN
		self.visa_handle.read_bytes(self.visa_handle.bytes_in_buffer)
		# TODO : set dacs to zero
		
	def performClose(self, options={}):
		"""Perform the close instrument connection operation"""
		self.visa_handle.read_bytes(self.visa_handle.bytes_in_buffer)
		self.visa_handle.close()
		
	def performSetValue(self, quant, value, sweepRate=0.0, options={}):
		"""Perform the Set Value instrument operation. This function should
		return the actual value set by the instrument"""
		self.visa_handle.read_bytes(self.visa_handle.bytes_in_buffer)
		
		if quant.name in ['Dac1','Dac2','Dac3','Dac4','Dac5','Dac6','Dac7','Dac8','Dac9','Dac10','Dac11','Dac12','Dac13','Dac14','Dac15','Dac16']:
			dacNr = int(quant.name[3:])
			pol_offset = self._polarity_offset(dacNr)
						
			# convert the value to the correct byte value, taking into account the polarity
			bytevalue = int(round((value*1000+pol_offset) / 4000 * 65535))
			
			# create a message and send it to the instrument
			msg=bytevalue.to_bytes(length=2, byteorder='big')
			message=bytes([7,0,2,1,dacNr])+msg
			self.visa_handle.write_raw(message)
			self.wait(0.005) #  NOTE: really needed?		
		
		if 'Polarity' in quant.name:
			if value in ['pos', 'Pos']:
				value = 'POS'
			if value in ['neg', 'Neg']:
				value = 'NEG'
			if value in ['bip', 'Bip']:
				value = 'BIP'
			if not value in ['POS','NEG','BIP']:
				raise 'Value should be POS, NEG, BIP'
			quant.setValue(value)
			pass
			
			# TODO: update all DAC values when changing the polarity
#			rackNr = int(list(quant.name)[-1])-3
#			for i in range(rackNr,rackNr+3):
#				qname='Dac'+str(i)
#				self.readValueFromOther(qname)

		self.visa_handle.read_bytes(self.visa_handle.bytes_in_buffer) # NOTE: not anymore necessary I guess
		return value
		
	def performGetValue(self, quant, options={}):
		self.visa_handle.read_bytes(self.visa_handle.bytes_in_buffer)
		if quant.name in ['Dac1','Dac2','Dac3','Dac4','Dac5','Dac6','Dac7','Dac8','Dac9','Dac10','Dac11','Dac12','Dac13','Dac14','Dac15','Dac16']:
			dacNr = int(quant.name[3:])
			if dacNr <1 or dacNr>16:
				raise 'Invalid dacNr'
			pol_offset = self._polarity_offset(dacNr)
			
			msg = [34,2]
			answer_len = msg[0]
			message = bytes([len(msg)+2])+bytes([0])+bytes(msg)
		
			
			valueisset = False
			while valueisset == False:
				self.visa_handle.write_raw(message)
				self.wait(0.01) #  NOTE: does it need to be so long and is it necessary at all?
			
				i=0
				byte_mess=[]
				while i < answer_len:
					self.wait(0.001)
					chunk = self.visa_handle.read_bytes(1)
					byte_mess += chunk
					i+=1			
				if byte_mess[1]:
					value = byte_mess[1]
					valueisset = False
				if self.visa_handle.bytes_in_buffer == 0:
					value = ((byte_mess[2+2*(dacNr-1)]*256 + byte_mess[3+2*(dacNr-1)]) / 65535.0 * 4000 - pol_offset) / 1000
					valueisset = True
				else:
					self.visa_handle.read_bytes(self.visa_handle.bytes_in_buffer)
				

		if 'Polarity' in quant.name:
			value = quant.getValue()

		self.visa_handle.read_bytes(self.visa_handle.bytes_in_buffer) # NOTE: not anymore necessary I guess	
		return value
		
	def _polarity_offset(self,dacNr):
		# first ask for the polarity
		if dacNr <1 or dacNr > 16:
			raise 'dacNr invalid' 
		if dacNr <= 4:
			polarity = self.readValueFromOther('Polarity 1-4')
		elif dacNr <= 8:
			polarity = self.readValueFromOther('Polarity 5-8')
		elif dacNr <= 12:
			polarity = self.readValueFromOther('Polarity 9-12')
		elif dacNr <= 16:
			polarity = self.readValueFromOther('Polarity 13-16')
		
		# set the offset according to the polarity
		if polarity == 'NEG':
			pol_offset = 4000
		elif polarity == 'BIP':
			pol_offset = 2000
		elif polarity == 'POS':
			pol_offset = 0	
		return pol_offset
