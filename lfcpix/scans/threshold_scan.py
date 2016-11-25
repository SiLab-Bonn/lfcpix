
from lfcpix.scan_base import ScanBase
import time

import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - [%(levelname)-8s] (%(threadName)-10s) %(message)s")

import numpy as np
import bitarray
import tables as tb

from progressbar import ProgressBar
from basil.dut import Dut
import os

local_configuration = {
    "mask_steps": 4,
    "repeat_command": 100,
    "scan_range": [0.0, 0.4, 0.1],
    "vthin1Dac": 60,
    "PrmpVbpDac": 36,
    "preCompVbnDac" : 110,
    "columns" : [True] * 2 + [True] * 14,
    "mask_filename": ''
}

class ThresholdScan(ScanBase):
    scan_id = "threshold_scan"


    def scan(self, mask_steps=4, repeat_command=100, PrmpVbpDac=80, vthin2Dac=0, columns = [True] * 16, scan_range = [0, 0.2, 0.05], vthin1Dac = 80, preCompVbnDac = 50, mask_filename='', **kwargs):

        '''Scan loop
        Parameters
        ----------
        mask : int
            Number of mask steps.
        repeat : int
            Number of injections.
        '''
        
        
        #
        # settings
        #
        
        mask_en = np.full([64,64], False, dtype = np.bool)
        mask_tdac = np.full([64,64], 16, dtype = np.uint8)
        
        for inx, col in enumerate(columns):
           if col:
                mask_en[inx*4:(inx+1)*4,:]  = True
        
        if mask_filename:
            logging.info('Using pixel mask from file: %s', mask_filename)
        
            with tb.open_file(mask_filename, 'r') as in_file_h5:
                mask_tdac = in_file_h5.root.scan_results.tdac_mask[:]
                mask_en = in_file_h5.root.scan_results.en_mask[:]

        #self.dut.write_en_mask(mask_en)
        #self.dut.write_tune_mask(mask_tdac)
        
        scan_range = np.arange(scan_range[0], scan_range[1], scan_range[2])
        
        for idx, k in enumerate(scan_range):
            
            #dut['Pulser'].set_voltage(INJ_LO, float(INJ_LO + k), unit='V')
            #self.dut['INJ_HI'].set_voltage( float(INJ_LO + k), unit='V')
            
            time.sleep(0.5)
            
            #bv_mask = bitarray.bitarray(lmask)
        
            with self.readout(scan_param_id = idx):
                logging.info('Scan Parameter: %f (%d of %d)', k, idx+1, len(scan_range))
                pbar = ProgressBar(maxval=mask_steps).start()
                for i in range(mask_steps):

                   
                    time.sleep(0.1)
                    
                   
                    pbar.update(i)
                     
                    #while not self.dut['inj'].is_done():
                    #    pass
                    
        scan_results = self.h5_file.create_group("/", 'scan_results', 'Scan Masks')
        self.h5_file.create_carray(scan_results, 'tdac_mask', obj=mask_tdac)
        self.h5_file.create_carray(scan_results, 'en_mask', obj=mask_en)
        
    def analyze(self):
        pass
                
if __name__ == "__main__":

    scan = ThresholdScan()
    scan.start(**local_configuration)
    scan.analyze()
