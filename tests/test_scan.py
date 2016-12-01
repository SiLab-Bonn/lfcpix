#
# ------------------------------------------------------------
# Copyright (c) All rights reserved
# SiLab, Institute of Physics, University of Bonn
# ------------------------------------------------------------
#

import unittest
import os
from basil.utils.sim.utils import cocotb_compile_and_run, cocotb_compile_clean
import sys
import yaml
import time

from lfcpix.lfcpix import lfcpix
from lfcpix.scans.threshold_scan import ThresholdScan

class TestSim(unittest.TestCase):

    def setUp(self):
        
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) #../
        print root_dir
        cocotb_compile_and_run(
            sim_files = [root_dir + '/tests/lfcpix_tb.v'], 
            sim_bus = 'basil.utils.sim.SiLibUsbBusDriver',
            include_dirs = (root_dir, root_dir + "/firmware/src"),
        )
       
        with open(root_dir + '/lfcpix/lfcpix.yaml', 'r') as f:
            self.cnfg = yaml.load(f)

        self.cnfg['transfer_layer'][0]['type'] = 'SiSim'

        
    def test(self):
        self.scan = ThresholdScan(self.cnfg)
        self.scan.start()
        
    def tearDown(self):
        self.scan.dut.dut.close()
        time.sleep(5)
        cocotb_compile_clean()

if __name__ == '__main__':
    unittest.main()
