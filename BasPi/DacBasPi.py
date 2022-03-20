from VISA_Driver import VISA_Driver
import struct

class Driver(VISA_Driver):

    def performOpen(self, options={}):
        VISA_Driver.performOpen(self, options)
        sAns = self.askAndLog('ALL 7FFF80')
        return sAns

    def performGetValue(self, quant, options={}):
        """Perform the Get Value instrument operation"""
        # perform special getValue for reading complex value
        name = str(quant.name)
        if name in ['Dac1','Dac2','Dac3','Dac4','Dac5','Dac6','Dac7','Dac8']:
            # get complex value in one instrument reading
            dacNr = quant.name[-1]
            sCmd = '{} V?'.format(dacNr)
            sAns = self.askAndLog(sCmd).strip()
            lData =  float.fromhex(sAns)
            lData = lData/838848-10
            return lData

    def performSetValue(self, quant, value, sweepRate, options={}):
        """Perform the Get Value instrument operation"""
        # perform special getValue for reading complex value
        name = str(quant.name)
        if name in ['Dac1','Dac2','Dac3','Dac4','Dac5','Dac6','Dac7','Dac8']:
            dacNr= quant.name[-1] 
            sVal = (value+10)*838848
            sCmd = '{} {}'.format(dacNr, hex(int(sVal))[2:])
            sAns = self.askAndLog(sCmd)
            if sAns != 0:
              print(sAns)
            return value