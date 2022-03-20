#!/usr/bin/env python

import InstrumentDriver
from VISA_Driver import VISA_Driver
import visa
from InstrumentConfig import InstrumentQuantity
import numpy as np
import string
import pyvisa
from BaseDriver import LabberDriver
import time

__version__ = "0.0.2"

class Error(Exception):
    pass

class Driver(LabberDriver):
    """ This class implements the Oxford Mercury iPS driver"""
    def performOpen(self, options={}):
    #    """Perform the operation of opening the instrument connection"""
        self.visa_handle = visa.ResourceManager().open_resource(self.getAddress())
        self.visa_handle.parity=self.visa_handle.parity.none
        self.visa_handle.baud_rate=9600
        self.visa_handle.write_termination='\r\n'
        self.visa_handle.read_termination=None
        self.visa_handle.query('T 1')
        self.visa_handle.query('H 1')
        self.tpa = 0.080697 #self.visa_handle.query('GET RATE')[29:29+6]

    def performGetValue(self, quant, options={}):
        """Perform the Get Value instrument operation"""
        if quant.name == 'Bz':
            sign = self.getSign()[0]
            answStr = self.visa_handle.query('GET OUTPUT')
            if sign >=0:
                value = float(answStr[17:17+7])
            else:
                value = float(answStr[17:17+8])
        elif quant.name == 'BzRate':
            answStr = self.visa_handle.query('GET RATE')
            value = float(answStr[29:29+5])*self.tpa
        elif quant.name == 'BzSwitchHeater':
            answStr = self.visa_handle.query('GET H')
            value = float(answStr[33:36]) > 2.0
        return value

    def performSetValue(self, quant, value, sweepRate, options={}):
        self.visa_handle.query('T 1')
        if quant.name == 'Bz':
            isSweeping = True
            sign = self.visa_handle.query('GET SIGN')[28:31]
            if not (sign == 'NEG' or sign == 'POS'):
                self.visa_handle.write('RAMP ZERO')
                value = 0
            elif (sign == 'NEG' and value > 0):
                self.visa_handle.write('RAMP ZERO')
                while (isSweeping == True):
                    isSweeping = self.visa_handle.query('RAMP STATUS')[22:26] == 'RAMP'
                time.sleep(5)
                self.visa_handle.write('DIRECTION +')
            elif (sign == 'POS' and value < 0):
                self.visa_handle.write('RAMP ZERO')
                while (isSweeping == True):
                    isSweeping = self.visa_handle.query('RAMP STATUS')[22:26] == 'RAMP'
                time.sleep(5)
                self.visa_handle.write('DIRECTION -')
            self.visa_handle.query('SET MID {0:.7f}'.format(abs(value)))
            self.visa_handle.write('RAMP MID')
            while (isSweeping == True):
                isSweeping = self.visa_handle.query('RAMP STATUS')[22:26] == 'RAMP'
        elif quant.name == 'BzRate':
            if value > 20e-3 or value < -20e-3:
                pass
            else:
                valueT = value/self.tpa
                answStr = self.visa_handle.query('SET RAMP {0:.7}'.format(valueT))
        elif quant.name == 'BzSwitchHeater':
            if value:
                self.visa_handle.query('SET H 2.5')
            else:
                self.visa_handle.query('SET H 0')
        return value

    def checkIfSweeping(self, quant, options={}):
        if quant.name == 'Bz':
            answStr = self.visa_handle.query('RAMP STATUS')[22:26]
            if answStr == 'RAMP' or 'EXTE' or 'QUEN':
                status = True
            elif answStr == 'HOLD':
                status = False
        else:
            pass
        return status

    def getSign(self):  #check!
        answStr = self.visa_handle.query('GET SIGN')[28:31]
        if answStr == '' or 'POS':
            sign = 1
            oppoSignStr = '-'
        elif answStr == 'NEG':
            sign = -1
            oppoSignStr = '+'
        return sign, oppoSignStr
#    def performStopSweep(self, quant, options={}):
#        pass

#    def performClose(self, bError=False , options={}):
#       pass
#        """Perform the set value operation"""
#        if quant.name in ('Bx', 'By', 'Bz'):
#            resetSwhtr = False
#            if quant.name + " switch heater" in self.detectedOptions:
#                swhtrFunc = self.instrCfg.getQuantity(quant.name + "SwitchHeater")
#                swhtr = self.performGetValue(swhtrFunc)
#                if not swhtr:
#                    self.performSetValue(swhtrFunc, True)
#                    resetSwhtr = True
#            dev = quant.set_cmd.split(":", 4)[2]
#            self.askAndLog(quant.set_cmd + ":" + str(value))
#            self.askAndLog('SET:DEV:' + dev + ':PSU:ACTN:RTOS')
#            self.waitForIdle(dev)
#            if resetSwhtr:
#                self.performSetValue(swhtrFunc, False)
#        elif quant.name in ('BxRate', 'ByRate', 'BzRate'):
#            self.askAndLog(quant.set_cmd + ":" + str(value))
#        elif quant.name in ('BxSwitchHeater', 'BySwitchHeater', 'BzSwitchHeater'):
#            vstring = "OFF"
#            if value:
#                vstring = "ON"
#            delay = self.instrCfg.getQuantity('SwitchHeaterDelay').getValue()
#            if not delay > 1:
#                self.Log("Switch Heater delay unreasonably short. Will not continue as this seems to be an error.")
#                return value
#            self.askAndLog(quant.set_cmd + ":" + vstring)
#            self.wait(delay)
#
#        return value

#    def waitForIdle(self, dev):
#        idle = (self.askAndLog('READ:DEV:' + dev + ':PSU:ACTN').strip().rsplit(':',1)[1] == "HOLD")
#        while not idle and not self.isStopped():
#            self.wait(0.1)
#            idle = (self.askAndLog('READ:DEV:' + dev + ':PSU:ACTN').strip().rsplit(':',1)[1] == "HOLD")
#        if self.isStopped():
#            self.askAndLog('SET:DEV:' + dev + ':PSU:ACTN:HOLD')
