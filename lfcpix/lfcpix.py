import time, string, os ,sys

import numpy as np
np.set_printoptions(linewidth="nan", threshold="nan")
import matplotlib.pyplot as plt
import bitarray

import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

from basil.dut import Dut

import lfcpix_log
        
class lfcpix():
    def __init__(self,conf="lfcpix.yaml"):
        self.logger=lfcpix_log.LfcpixLog()
        self.dut=Dut(conf)
        
        # init member variables
        self.debug=0
        self._build_img=np.vectorize(self._build_img_one)
        self.plot=False
        
        # init basil
        self.dut.init()
        
        #### init memory
        self.mon_en=self.dut["CCPD_SR"]["Pixels"].copy()
        self.inj_en=self.dut["CCPD_SR"]["Pixels"].copy()
        self.preamp_en=self.dut["CCPD_SR"]["Pixels"].copy()
        self.preamp_en_ana=self.dut["CCPD_SR"]["PREAMP_EN_ANA"].copy()
        self.monitor_en_ana=self.dut["CCPD_SR"]["MONITOR_EN_ANA"].copy()
        self.sw_mon=self.dut["CCPD_SR"]["SW_MON"].copy()
        self.sw_inj=self.dut["CCPD_SR"]["SW_INJ"].copy()
        self.tdac=np.ones([26,106],int)*0
        
       # init chip
        self.power()
        self.set_global()
        self.set_mon_en([14,25])
        self.set_preamp_en()
        self.set_inj_en([14,25])
        self.set_tdac(0)
        self.set_inj_all()
        self.show()
        
    def _build_img_one(self,spix):
            frame=spix/2768
            spix=2755-spix%2768
            col=spix/106
            row=spix%106
            if col%2==0:
                pass
            elif col%2==1:
                row=106-row
            return frame,col,row
            
    def _build_img2(self,dat):
        img=np.empty([26,106],dtype=int)  ##### TODO can be more efficient
        for i in range(0,26,2):
            img[i+0,:]=np.copy(dat[(i+0)*106:(i+1)*106])
            img[i+1,:]=np.copy(dat[(i+1)*106:(i+2)*106][::-1])
        return img
        
    def _cal_Pixels(self,pix):
        if isinstance(pix,str):
            if pix=="all":
                en_pix=bitarray.bitarray('1'*2756)
                en_col=bitarray.bitarray('1'*10)
            else:
                en_pix=bitarray.bitarray('0'*2756)
                en_col=bitarray.bitarray('0'*10)
        elif isinstance(pix,int):
            if pix==0:
                en_pix=bitarray.bitarray('0'*2756)
                en_col=bitarray.bitarray('0'*10)
            else:
                en_pix=bitarray.bitarray('1'*2756)
                en_col=bitarray.bitarray('1'*10)
        elif isinstance(pix,type(bitarray.bitarray())):
            en_pix=bitarray.bitarray('0'*2756)
            en_col=bitarray.bitarray('0'*10)
            for i in range(0,26,2):
                a0=pix[106*(i):106*(i+1)].copy()
                a1=pix[106*(i+1):106*(i+2)].copy()
                a1.reverse()
                en_pix[106*(i):106*(i+2)]=a0+a1
        else:
            en_pix=bitarray.bitarray('0'*2756)
            en_col=bitarray.bitarray('0'*10)
            if isinstance(pix[0],int):
                pix=[pix]
            for p in pix:
                if p[0]>25:
                    en_col[p[0]-26]=1
                else:
                    r=p[0]%2
                    if r==0:
                        en_pix[p[0]*106+p[1]]=1
                    elif r==1:
                        en_pix[(p[0]+1)*106-p[1]-1]=1
        return en_pix,en_col

#############
### Power, injection, threshold
    def power(self,pwr_en=True,
              Vdda=1.8,Vddp=1.5,Vddd=1.8,VCasc2=0.7,TH=1.5,VCascP=1.,VCascN=0.52):    
        self.dut['CCPD_vdda'].set_current_limit(204, unit='mA')
        
        self.dut['CCPD_vdda'].set_voltage(Vdda, unit='V')
        self.dut['CCPD_vdda'].set_enable(pwr_en)
        
        self.dut['CCPD_vddaPRE'].set_voltage(Vddp, unit='V')
        self.dut['CCPD_vddaPRE'].set_enable(pwr_en)
        
        self.dut['CCPD_vddd'].set_voltage(Vddd, unit='V')
        self.dut['CCPD_vddd'].set_enable(pwr_en)

        self.dut['CCPD_VCasc2'].set_voltage(VCasc2, unit='V')
        self.dut['CCPD_VCascP'].set_voltage(VCascP, unit='V')
        self.dut['CCPD_TH'].set_voltage(TH, unit='V')
        self.dut['CCPD_VCascN'].set_voltage(VCascN, unit='V')
        
        self.logger.info("Vdda:%f Vddp:%f Vddd:%f VCasc2:%f VCascN:%f VCascP:%f TH:%f"%(
                        Vdda,Vddp,Vddd,VCasc2,VCascN,VCascP))
                        
    def set_inj_all(self,inj_high=1.0,inj_low=0.0,inj_width=500,inj_n=1,delay=700,ext=True):
        self.dut["CCPD_Injection_high"].set_voltage(inj_high,unit="V")
        self.inj_high=inj_high
        self.dut["CCPD_Injection_low"].set_voltage(inj_low,unit="V")
        self.inj_low=inj_low

        self.dut["CCPD_PULSE_INJ"].reset()
        self.dut["CCPD_PULSE_INJ"]["REPEAT"]=inj_n
        self.dut["CCPD_PULSE_INJ"]["DELAY"]=inj_width
        self.dut["CCPD_PULSE_INJ"]["WIDTH"]=inj_width
        self.dut["CCPD_PULSE_INJ"]["EN"]=1
        
        self.dut["CCPD_PULSE_GATE"].reset()
        self.dut["CCPD_PULSE_GATE"]["REPEAT"]=1
        self.dut["CCPD_PULSE_GATE"]["DELAY"]=delay
        self.dut["CCPD_PULSE_GATE"]["WIDTH"]=inj_n*inj_width*2+10
        self.dut["CCPD_PULSE_GATE"]["EN"]=ext
        self.logger.info("inj:%.4f,%.4f inj_width:%d inj_n:%d delay:%d ext:%d"%(
            inj_high,inj_low,inj_width,inj_n,delay,int(ext)))

    def set_inj(self,inj_high,inj_low=0.0):
        self.dut["CCPD_Injection_high"].set_voltage(inj_high,unit="V")
        self.inj_high=inj_high
        self.dut["CCPD_Injection_low"].set_voltage(inj_low,unit="V")
        self.inj_low=inj_low
        self.logger.info("set_inj inj_high:%f inj_low:%f"%(inj_high, inj_low))

    def inject(self):
        self.dut["CCPD_PULSE_INJ"].start()

    def set_th(self,TH,thmod=False):
        self.dut['CCPD_TH'].set_voltage(TH, unit='V')
        THvol=self.dut['CCPD_TH'].get_voltage(unit='V')
        self.dut['CCPD_SW']['THON_NEG']= (not thmod)
        self.dut['CCPD_SW'].write()
        self.logger.info("th_set:%f th:%f th_mod:%d"%(TH,THvol,thmod))

    def get_th(self):
        thmod=not self.dut['CCPD_SW']['THON_NEG']
        THvol=self.dut['CCPD_TH'].get_voltage(unit='V')
        self.logger.info("get_th:%f th_mod:%d"%(THvol,thmod))
##############
####  status
    def get_status(self):
        stat={"Vdda": self.dut['CCPD_vdda'].get_voltage(unit='V'),
            "Vdda_curr": self.dut['CCPD_vdda'].get_current(unit="mA"),
            "Vddp": self.dut['CCPD_vddaPRE'].get_voltage(unit='V'),
            "Vddp_curr": self.dut['CCPD_vddaPRE'].get_current(unit="mA"),
            "Vddd": self.dut['CCPD_vddd'].get_voltage(unit='V'),
            "Vddd_curr": self.dut['CCPD_vddd'].get_current(unit="mA"),
            "VCasc2": self.dut['CCPD_VCasc2'].get_voltage(unit='V'),
            "VCasc2_curr": self.dut['CCPD_VCasc2'].get_current(unit="mA"),
            "VCascN": self.dut['CCPD_VCascN'].get_voltage(unit='V'),
            'VCascN_curr': self.dut['CCPD_VCascN'].get_current(unit="mA"),
            'VCascP': self.dut['CCPD_VCascP'].get_voltage(unit='V'),
            'VCascP_curr': self.dut['CCPD_VCascP'].get_current(unit="mA"),
            'TH': self.dut['CCPD_TH'].get_voltage(unit='V'),
            'TH_curr': self.dut['CCPD_TH'].get_current(unit="mA"),
            ##### TODO make data from get_data
            'BLRes':self.dut['CCPD_SR']['BLRes'].tovalue(),
            'VAmp':self.dut['CCPD_SR']['VAmp'].tovalue(),
            'VPFB':self.dut['CCPD_SR']['VPFB'].tovalue(),
            'VPFoll':self.dut['CCPD_SR']['VPFoll'].tovalue(),
            'VPLoad':self.dut['CCPD_SR']['VPLoad'].tovalue(),
            'IComp':self.dut['CCPD_SR']['IComp'].tovalue(),
            'VSTRETCH':self.dut['CCPD_SR']['VSTRETCH'].tovalue(),
            'IBOTA':self.dut['CCPD_SR']['IBOTA'].tovalue(),
            'IBCS':self.dut['CCPD_SR']['IBCS'].tovalue(),
            'WGT':self.dut['CCPD_SR']['WGT'].tovalue(),
            'LSBdacL':self.dut['CCPD_SR']['LSBdacL'].tovalue(),
            'LSBdacL2':self.dut['CCPD_SR']['LSBdacL2'].tovalue(),
            'IBCS2':self.dut['CCPD_SR']['IBCS2'].tovalue(),
            'INJ_EN_AnaPassive':self.dut['CCPD_SR']['INJ_EN_AnaPassive'].tovalue(),
            #"PREAMP_EN_ANA": self.preamp_en_ana.tovalue(),
            "SW_MON":" ".join(hex(ord(n)) for n in self.sw_mon.tobytes()),
            "SW_INJ":" ".join(hex(ord(n)) for n in self.sw_inj.tobytes()),
            "MON_EN":" ".join(hex(ord(n)) for n in self.mon_en.tobytes()),
            "PREAMP_EN":" ".join(hex(ord(n)) for n in self.preamp_en.tobytes()),
            "INJECT_EN":" ".join(hex(ord(n)) for n in self.inj_en.tobytes()),
            "Pixels":" ".join(hex(ord(n)) for n in self.dut["CCPD_SR"]["Pixels"].tobytes()),
            #"SR_EN":self.dut["CCPD_SR"].get_enable(), ##TODO find this function
            "SR_REPEAT":self.dut["CCPD_SR"].get_repeat(),
            "SR_WAIT":self.dut["CCPD_SR"].get_wait(),
            'CCPD_SW':self.dut["CCPD_SW"].get_data()[0],
            'rx_SW':self.dut["rx"].get_data()[0],
            'inj_high':self.inj_high,
            'inj_low':self.inj_low,
            'INJ_DELAY':self.dut["CCPD_PULSE_INJ"]["DELAY"],
            'INJ_WIDTH':self.dut["CCPD_PULSE_INJ"]["WIDTH"],
            'INJ_REPEAT':self.dut["CCPD_PULSE_INJ"]["REPEAT"],
            'INJ_EN':self.dut["CCPD_PULSE_INJ"]["EN"],
            'GATE_DELAY':self.dut["CCPD_PULSE_GATE"]["DELAY"],
            'GATE_WIDTH':self.dut["CCPD_PULSE_GATE"]["WIDTH"],
            'GATE_REPEAT':self.dut["CCPD_PULSE_GATE"]["REPEAT"],
            'GATE_EN':self.dut["CCPD_PULSE_GATE"]["EN"],
            }         
        return stat

    def show(self,show="all"):
        r=self.get_status()
        self.logger.show(r)
##########
### set registers
    def _write_SR(self,sw="SW_LDDAC"):
        if sw=="SW_LDDAC":
            self.dut['CCPD_SW']['SW_LDPIX']=0
            self.dut['CCPD_SW']['SW_LDDAC']=1
            self.dut['CCPD_SW']['SW_HIT']=0
        elif sw=="SW_LDPIX":
            self.dut['CCPD_SW']['SW_LDPIX']=1
            self.dut['CCPD_SW']['SW_LDDAC']=0
            self.dut['CCPD_SW']['SW_HIT']=0
        elif sw=="SW_HIT":
            self.dut['CCPD_SW']['SW_LDPIX']=0
            self.dut['CCPD_SW']['SW_LDDAC']=0
            self.dut['CCPD_SW']['SW_HIT']=1
        else:
            self.dut['CCPD_SW']['SW_LDPIX']=0
            self.dut['CCPD_SW']['SW_LDDAC']=0
            self.dut['CCPD_SW']['SW_HIT']=0
        self.dut['CCPD_SW'].write()

        self.dut['CCPD_SR'].set_size(2953)
        self.dut['CCPD_SR'].set_repeat(1)
        self.dut['CCPD_SR'].set_wait(0)
        self.dut['CCPD_SR'].write()
        self.dut['CCPD_SR'].start()
        i=0
        while i<10000:
            if self.dut['CCPD_SR'].is_done():
                break
            elif i> 100:
                time.sleep(0.001)
            i=i+1
        if i==10000:
            self.logger.info("ERROR timeout")

    def set_global(self,BLRes=28,VAmp=26,VPFB=47,VPFoll=12,VPLoad=11,IComp=24,VSTRETCH=5,
               IBOTA=20,IBCS=23,WGT=32,LSBdacL=32,LSBdacL2=32,IBCS2=23):
        self.dut['CCPD_SPI_RX'].reset()
        self.dut['CCPD_SPI_RX'].set_en(False)
        
        self.dut["CCPD_PULSE_GATE"].reset()
        self.dut['CCPD_PULSE_GATE'].set_en(False)
        self.dut["CCPD_PULSE_INJ"].reset()
        self.dut['CCPD_PULSE_INJ'].set_en(False)

        self.dut['CCPD_SR']['BLRes']=BLRes
        self.dut['CCPD_SR']['VAmp']=VAmp
        self.dut['CCPD_SR']['VPFB']=VPFB
        self.dut['CCPD_SR']['VPFoll']=VPFoll
        self.dut['CCPD_SR']['VPLoad']=VPLoad
        self.dut['CCPD_SR']['IComp']=IComp
        self.dut['CCPD_SR']['VSTRETCH']=VSTRETCH
        self.dut['CCPD_SR']['IBOTA']=IBOTA
        self.dut['CCPD_SR']['IBCS']=IBCS
        self.dut['CCPD_SR']['WGT']=WGT
        self.dut['CCPD_SR']['LSBdacL']=LSBdacL
        self.dut['CCPD_SR']['LSBdacL2']=LSBdacL2
        self.dut['CCPD_SR']['IBCS2']=IBCS2
        self._write_SR(sw="SW_LDDAC")

        self.logger.info('BLRes:%d VAmp:%d VPFB=:%d VPFoll:%d VPLoad:%d IComp:%d VSTRETCH:%dIBOTA:%d IBCS:%d WGT:%d LSBdacL:%d LSBdacL2:%d IBCS2:%d'%(
               BLRes,VAmp,VPFB,VPFoll,VPLoad,IComp,VSTRETCH,IBOTA,IBCS,WGT,LSBdacL,LSBdacL2,IBCS2)) 

    def set_mon_en(self,pix="none"):
        tmp_spi_en=self.dut['CCPD_SPI_RX'].get_en()
        self.dut['CCPD_SPI_RX'].set_en(False)
        tmp_gate_en=self.dut['CCPD_SPI_RX'].get_en()
        self.dut['CCPD_PULSE_GATE'].set_en(False)
        
        self.dut['CCPD_SR']['TRIM_EN']=0
        self.dut['CCPD_SR']['INJECT_EN']=0
        self.dut['CCPD_SR']['MONITOR_EN']=1
        self.dut['CCPD_SR']['PREAMP_EN']=0
        
        self.dut['CCPD_SR']['PREAMP_EN_ANA']=self.preamp_en_ana
        self.dut['CCPD_SR']['SW_INJ']=self.sw_inj
        
        en_pix,en_col=self._cal_Pixels(pix)
        self.dut['CCPD_SR']['Pixels']=en_pix
        self.mon_en=en_pix.copy()
        self.dut['CCPD_SR']['MONITOR_EN_ANA']=en_col
        self.monitor_en_ana=en_col.copy()

        for i in range(0,2756,106):
            self.dut['CCPD_SR']['SW_MON'][i/106]=self.mon_en[i:i+106].any()
        for i in range(10):
            self.dut['CCPD_SR']['SW_MON'][26+i]=en_col[i]
        self.sw_mon=self.dut['CCPD_SR']['SW_MON'].copy()
        
        self.dut['CCPD_SR']['BUFFER_EN']=self.sw_mon.any()
        self.dut['CCPD_SR']['REGULATOR_EN']=(self.preamp_en_ana.any() or self.preamp_en[106*18:].any())

        self._write_SR(sw="SW_LDPIX")

        self.dut['CCPD_SPI_RX'].set_en(tmp_spi_en)
        self.dut['CCPD_PULSE_GATE'].set_en(tmp_gate_en)
        
        s="set_mon_en pix:%s lds:%d,%d,%d,%d pixels:%s "%(pix,
                self.dut['CCPD_SR']['TRIM_EN'].tovalue(),self.dut['CCPD_SR']['INJECT_EN'].tovalue(),
                self.dut['CCPD_SR']['MONITOR_EN'].tovalue(),self.dut['CCPD_SR']['PREAMP_EN'].tovalue(),
                "")
        s="%spreamp_en_ana:0x%x monitor_en_ana:0x%x sw_mon:0x%x sw_inj:0x%x regulator:%d buffer:%d "%(s,
                self.dut['CCPD_SR']['PREAMP_EN_ANA'].tovalue(),self.dut['CCPD_SR']['MONITOR_EN_ANA'].tovalue(),
                self.dut['CCPD_SR']['SW_MON'].tovalue(),self.dut['CCPD_SR']['SW_INJ'].tovalue(),
                self.dut['CCPD_SR']['REGULATOR_EN'].tovalue(),self.dut['CCPD_SR']['BUFFER_EN'].tovalue())
        self.logger.info(s)

    def set_preamp_en(self,pix="all"):
        tmp_spi_en=self.dut['CCPD_SPI_RX'].get_en()
        self.dut['CCPD_SPI_RX'].set_en(False)
        tmp_gate_en=self.dut['CCPD_SPI_RX'].get_en()
        self.dut['CCPD_PULSE_GATE'].set_en(False)

        self.dut['CCPD_SR']['TRIM_EN']=0
        self.dut['CCPD_SR']['INJECT_EN']=0
        self.dut['CCPD_SR']['MONITOR_EN']=0
        self.dut['CCPD_SR']['PREAMP_EN']=1
        
        self.dut['CCPD_SR']['MONITOR_EN_ANA']=self.monitor_en_ana
        self.dut['CCPD_SR']['SW_MON']=self.sw_mon
        self.dut['CCPD_SR']['SW_INJ']=self.sw_inj

        en_pix,en_col=self._cal_Pixels(pix)
        self.dut['CCPD_SR']['Pixels']=en_pix
        self.preamp_en=en_pix.copy()
        self.dut['CCPD_SR']['PREAMP_EN_ANA']=en_col
        self.preamp_en_ana=en_col.copy()
        
        self.dut['CCPD_SR']['BUFFER_EN']=self.sw_mon.any()
        self.dut['CCPD_SR']['REGULATOR_EN']=(en_col.any() or en_pix[106*18:].any())
        
        self._write_SR(sw="SW_LDPIX")

        self.dut['CCPD_SPI_RX'].set_en(tmp_spi_en)
        self.dut['CCPD_PULSE_GATE'].set_en(tmp_gate_en)
        
        s="set_preamp_en pix:%s lds:%d,%d,%d,%d pixels:%s "%(pix,
                self.dut['CCPD_SR']['TRIM_EN'].tovalue(),self.dut['CCPD_SR']['INJECT_EN'].tovalue(),
                self.dut['CCPD_SR']['MONITOR_EN'].tovalue(),self.dut['CCPD_SR']['PREAMP_EN'].tovalue(),
                "")
        s="%spreamp_en_ana:0x%x monitor_en_ana:0x%x sw_mon:0x%x sw_inj:0x%x regulator:%d buffer:%d"%(s,
                self.dut['CCPD_SR']['PREAMP_EN_ANA'].tovalue(),self.dut['CCPD_SR']['MONITOR_EN_ANA'].tovalue(),
                self.dut['CCPD_SR']['SW_MON'].tovalue(),self.dut['CCPD_SR']['SW_INJ'].tovalue(),
                self.dut['CCPD_SR']['REGULATOR_EN'].tovalue(),self.dut['CCPD_SR']['BUFFER_EN'].tovalue())
        self.logger.info(s)
        
    def set_inj_en(self,pix="none"):
        tmp_spi_en=self.dut['CCPD_SPI_RX'].get_en()
        self.dut['CCPD_SPI_RX'].set_en(False)
        tmp_gate_en=self.dut['CCPD_SPI_RX'].get_en()
        self.dut['CCPD_PULSE_GATE'].set_en(False)
    
        self.dut['CCPD_SR']['TRIM_EN']=0
        self.dut['CCPD_SR']['INJECT_EN']=1
        self.dut['CCPD_SR']['MONITOR_EN']=0
        self.dut['CCPD_SR']['PREAMP_EN']=0
        
        self.dut['CCPD_SR']['PREAMP_EN_ANA']=self.preamp_en_ana
        self.dut['CCPD_SR']['MONITOR_EN_ANA']=self.monitor_en_ana
        self.dut['CCPD_SR']['SW_MON']=self.sw_mon
        

        en_pix,en_col=self._cal_Pixels(pix)
        self.dut['CCPD_SR']['Pixels']=en_pix
        self.inj_en=en_pix.copy()
        for i in range(0,2756,106*2):
            self.dut['CCPD_SR']['SW_INJ'][i/(106*2)]=self.inj_en[i:i+(106*2)].any()
        for i in range(5):
            self.dut['CCPD_SR']['SW_INJ'][13+i]=en_col[2*i:2*(i+1)].any()
        self.sw_inj=self.dut['CCPD_SR']['SW_INJ'].copy()
        
        self.dut['CCPD_SR']['BUFFER_EN']=self.sw_mon.any()
        self.dut['CCPD_SR']['REGULATOR_EN']=(self.preamp_en_ana.any() or self.preamp_en[106*18:].any())
        
        self._write_SR(sw="SW_LDPIX")
        
        self.dut['CCPD_SPI_RX'].set_en(tmp_spi_en)
        self.dut['CCPD_PULSE_GATE'].set_en(tmp_gate_en)

        s="set_inj_en pix:%s lds:%d,%d,%d,%d pixels:%s "%(pix,
                self.dut['CCPD_SR']['TRIM_EN'].tovalue(),self.dut['CCPD_SR']['INJECT_EN'].tovalue(),
                self.dut['CCPD_SR']['MONITOR_EN'].tovalue(),self.dut['CCPD_SR']['PREAMP_EN'].tovalue(),
                "")
        s="%spreamp_en_ana:0x%x monitor_en_ana:0x%x sw_mon:0x%x sw_inj:0x%x regulator:%d buffer:%d"%(s,
                self.dut['CCPD_SR']['PREAMP_EN_ANA'].tovalue(),self.dut['CCPD_SR']['MONITOR_EN_ANA'].tovalue(),
                self.dut['CCPD_SR']['SW_MON'].tovalue(),self.dut['CCPD_SR']['SW_INJ'].tovalue(),
                self.dut['CCPD_SR']['REGULATOR_EN'].tovalue(),self.dut['CCPD_SR']['BUFFER_EN'].tovalue())
        self.logger.info(s)

    def set_tdac(self,tdac):
        tmp_spi_en=self.dut['CCPD_SPI_RX'].get_en()
        self.dut['CCPD_SPI_RX'].set_en(False)
        tmp_gate_en=self.dut['CCPD_SPI_RX'].get_en()
        self.dut['CCPD_PULSE_GATE'].set_en(False)
    
        self.dut['CCPD_SR']['INJECT_EN']=0
        self.dut['CCPD_SR']['MONITOR_EN']=0
        self.dut['CCPD_SR']['PREAMP_EN']=0
        self.dut['CCPD_SR']['SW_MON']=self.sw_mon
        
        self.dut['CCPD_SR']['PREAMP_EN_ANA']=self.preamp_en_ana
        self.dut['CCPD_SR']['MONITOR_EN_ANA']=self.monitor_en_ana
        
        self.dut['CCPD_SR']['SW_INJ']=self.sw_inj
        self.dut['CCPD_SR']['SW_MON']=self.sw_mon
        
        self.dut['CCPD_SR']['BUFFER_EN']=self.sw_mon.any()
        self.dut['CCPD_SR']['REGULATOR_EN']=(self.preamp_en_ana.any() or self.preamp_en[106*18:].any())
        
        if isinstance(tdac, int):
            tdac=np.ones([26,106],int)*tdac
       
        for i_trim in [1,2,4,8]:
            pix=bitarray.bitarray(((np.reshape(tdac, 106*26) & i_trim) !=0).tolist())
            en_pix,en_col=self._cal_Pixels(pix)
            self.dut['CCPD_SR']['Pixels']=en_pix
            self.dut['CCPD_SR']['TRIM_EN']=i_trim
            self._write_SR(sw="SW_LDPIX")
        
        self.dut['CCPD_SPI_RX'].set_en(tmp_spi_en)
        self.dut['CCPD_PULSE_GATE'].set_en(tmp_gate_en)
        
        np.argwhere(self.tdac!=tdac)
        s="tdac:"
        for p in np.argwhere(self.tdac!=tdac):
            s="%s,[%d,%d]=%d"%(s,p[0],p[1],tdac[p[0],p[1]])
        self.logger.info(s)
        self.tdac=np.copy(tdac)

################
## HIT register
    def set_hit(self,mode="inj",repeat=100,gate_delay=50,gate_width=None):
        ### TODO should be better than this
        if mode=="inj":
            inj=True
            inj_delay=100
            inj_width=200
            if gate_width==None:
                gate_width=inj_delay+inj_width/2
            thmod=False
            thon_width=0
            thon_delay=0
        elif mode=="inj_ext": 
            inj=False
            inj_delay=0
            inj_width=0
            if gate_width==None:
                gate_width=1000
            thmod=False
            thon_width=0
            thon_delay=0
        elif mode=="inj_thmod":
            if gate_width==None:
                gate_width=9900
            inj=True
            inj_width=200
            inj_delay=gate_width-inj_width/2
            thmod=True
            thon_width=gate_width-10
            thon_delay=gate_delay+10
        elif mode=="src":
            inj=False
            inj_delay=0
            inj_width=0
            if gate_width==None:
                gate_width=9900
            thmod=False
            thon_width=0
            thon_delay=0
        elif mode=="src_thmod":
            inj=False
            inj_delay=0
            inj_width=0
            if gate_width==None:
                gate_width=9900
            thmod=True
            thon_width=gate_width-10
            thon_delay=gate_delay+10
        sr_wait=gate_width+gate_delay+5

        self.dut['rx']['CCPD_ADC'] = 0
        self.dut['rx']['TLU'] = 0
        self.dut['rx']['CCPD_TDC'] = 0
        self.dut['rx']['CCPD_RX'] = 1
        self.dut['rx'].write()
        
        self.dut["CCPD_PULSE_THON"].reset()
        if thmod==False:
            self.dut["CCPD_PULSE_THON"].set_en(0)
        else:
            self.dut["CCPD_PULSE_THON"].set_delay(thon_delay)
            self.dut["CCPD_PULSE_THON"].set_repeat(1)
            self.dut["CCPD_PULSE_THON"].set_width(thon_width)
            self.dut["CCPD_PULSE_THON"].set_en(1)

        self.dut["CCPD_PULSE_GATE"].reset()
        self.dut["CCPD_PULSE_GATE"]["EN"]=0
        self.dut["CCPD_SR"].reset()
        self.dut["CCPD_SR"]=bitarray.bitarray('1'*2953)
        self._write_SR(sw="NONE")
        self.dut["CCPD_SR"].set_size(2768)
        self.dut["CCPD_SR"].set_repeat(repeat+1)
        self.dut["CCPD_SR"].set_wait(sr_wait)

        self.dut['CCPD_SW']['SW_LDPIX']=0
        self.dut['CCPD_SW']['SW_LDDAC']=0
        if thmod==False:
            self.dut['CCPD_SW']['THON_NEG']=1
        else:
            self.dut['CCPD_SW']['THON_NEG']=0
        self.dut["CCPD_SW"]["SW_HIT"]=1
        self.dut["CCPD_SW"]["EXT_START_TLU"]=0
        self.dut["CCPD_SW"]["GATE_NEG"]=0
        self.dut['CCPD_SW'].write()

        if inj==False:
            self.dut["CCPD_PULSE_INJ"]["EN"]=0
        else:
            self.dut["CCPD_PULSE_INJ"].reset()
            self.dut["CCPD_PULSE_INJ"]["REPEAT"]=1
            self.dut["CCPD_PULSE_INJ"]["DELAY"]=inj_delay
            self.dut["CCPD_PULSE_INJ"]["WIDTH"]=inj_width
            self.dut["CCPD_PULSE_INJ"]["EN"]=1

        self.dut["CCPD_PULSE_GATE"].reset()
        self.dut["CCPD_PULSE_GATE"]["REPEAT"]=1
        self.dut["CCPD_PULSE_GATE"]["DELAY"]=gate_delay
        self.dut["CCPD_PULSE_GATE"]["WIDTH"]=gate_width
        self.dut["CCPD_PULSE_GATE"]["EN"]=1
        
        # set TDC
        self.dut["CCPD_TDC"].reset()
        self.dut['CCPD_TDC']['ENABLE_EXTERN']=False
        self.dut['CCPD_TDC']['ENABLE']=False

        # reset fifo
        self.dut['sram'].reset()
        
        # reset rx
        self.dut['CCPD_SPI_RX'].reset()
        self.dut['CCPD_SPI_RX'].set_en(True)

        s="repeat:%d inj_delay:%d inj_width:%d gate_delay:%d gate_width:%d\n"%(
            repeat,inj_delay,inj_width,gate_delay,gate_width)
        s="%sthod:%d thon_width:%d thon_delay:%d sr_wait:%d"%(
            s,thmod,thon_width,thon_delay,sr_wait)
        self.logger.info(s)

    def get_hit(self):
        self.dut['sram'].reset()
        while self.dut["sram"].get_fifo_size()!=0:
           self.dut['sram'].get_data()
           self.dut['sram'].reset()
        self.dut['sram'].reset()
        self.dut["CCPD_SR"].start()
        wait=self.dut["CCPD_SR"].get_wait()
        repeat=self.dut["CCPD_SR"].get_repeat()
        i=0
        while self.dut["sram"].get_fifo_size()<692*repeat:
        #while not self.dut['CCPD_SR'].is_done():  ## this dose not work any more
            if i>10000+wait*repeat/1000:
                self.logger.info("get_hit ERROR timeout")
                break
            elif i> 100:
                time.sleep(0.001) 
            i=i+1
        return self.dut['sram'].get_data()[173:]
##########################
########### TDC
    def set_tdc_inj(self,repeat=100,inj_width=500,gate_delay=5,
                inj_delay=None, gate_width=None, tdc_trig_dist=False):
        if inj_delay==None:
            inj_delay=inj_width
        if gate_width==None:
            gate_width=inj_width*2*repeat+2*gate_delay

        self.dut['rx']['NC'] = 0
        self.dut['rx']['TLU'] = 0
        self.dut['rx']['CCPD_TDC'] = 1
        self.dut['rx']['CCPD_RX'] = 0
        self.dut['rx'].write()
        
        self.dut['CCPD_SW']['SW_LDPIX']=0
        self.dut['CCPD_SW']['SW_LDDAC']=0
        self.dut['CCPD_SW']['SW_HIT']=0
        self.dut["CCPD_SW"]['THON_NEG']=1
        self.dut['CCPD_SW'].write()
        
        self.dut['CCPD_SPI_RX'].reset()
        self.dut['CCPD_SPI_RX'].set_en(False)

        self.dut["CCPD_PULSE_INJ"].reset()
        self.dut["CCPD_PULSE_INJ"]["REPEAT"]=repeat
        self.dut["CCPD_PULSE_INJ"]["DELAY"]=inj_delay
        self.dut["CCPD_PULSE_INJ"]["WIDTH"]=inj_width
        self.dut["CCPD_PULSE_INJ"]["EN"]=1

        self.dut["CCPD_PULSE_GATE"].reset()
        self.dut["CCPD_PULSE_GATE"]["REPEAT"]=1
        self.dut["CCPD_PULSE_GATE"]["DELAY"]=gate_delay
        self.dut["CCPD_PULSE_GATE"]["WIDTH"]=gate_width
        self.dut["CCPD_PULSE_GATE"]["EN"]=1

        self.dut["CCPD_TDC"].reset()
        self.dut['CCPD_TDC']['EN_INVERT_TDC']=True
        self.dut['CCPD_TDC']['EN_TRIGGER_DIST']=tdc_trig_dist
        self.dut['CCPD_TDC']['EN_WRITE_TIMESTAMP']=True
        self.dut['CCPD_TDC']['ENABLE_EXTERN']=True
        self.dut['CCPD_TDC']['ENABLE']=False
        
        self.dut['sram'].reset()

        s="set_tdc_inj: repeat=%d inj_width=%d inj_delay=%d gate_width=%d gate_delay=%d tdc_trig_dist=%d"%(
            repeat,inj_width,inj_delay,gate_delay,gate_width,tdc_trig_dist)
        self.logger.info(s)
    
    def set_tdc_src(self,mode="src",gate_width=None):
        if mode=="tlu": 
            inj_width=100
            inj_delay=inj_width
            if gate_width==None:
                gate_width=1
            gate_delay=1
            tlu=True
        else: # mode=="src"
            inj_width=0
            inj_delay=0
            if gate_width==None:
                gate_width=10000000 
            gate_delay=5
            tlu=False

        self.dut['rx']['NC'] = 0
        self.dut['rx']['TLU'] = 0
        self.dut['rx']['CCPD_TDC'] = 1
        self.dut['rx']['CCPD_RX'] = 0
        self.dut['rx']['TLU'] = tlu
        self.dut['rx'].write()
        
        self.dut['CCPD_SW']['SW_LDPIX']=0
        self.dut['CCPD_SW']['SW_LDDAC']=0
        self.dut['CCPD_SW']['SW_HIT']=0
        self.dut['CCPD_SW']['GATE_NEG']=0 
        self.dut["CCPD_SW"]['THON_NEG']=1
        self.dut['CCPD_SW']['EXT_START_TLU']=tlu
        self.dut['CCPD_SW'].write()
        
        self.dut["CCPD_PULSE_THON"].reset()
        self.dut["CCPD_PULSE_THON"]["EN"]=False

        self.dut['CCPD_SPI_RX'].reset()
        self.dut['CCPD_SPI_RX'].set_en(False)
        self.dut["CCPD_SR"].reset()
        self.dut["CCPD_SR"].set_en(0)

        self.dut["tlu"]["RESET"]=0
        if tlu==True:
            self.dut["tlu"]["TRIGGER_MODE"]=3
            self.dut["tlu"]["TRIGGER_LOW_TIMEOUT"]=0
            self.dut["tlu"]["TRIGGER_VETO_SELECT"]=255

        self.dut["CCPD_PULSE_INJ"].reset()
        
        self.dut["CCPD_PULSE_GATE"].reset()
        self.dut["CCPD_PULSE_GATE"]["REPEAT"]=1
        self.dut["CCPD_PULSE_GATE"]["DELAY"]=gate_delay
        self.dut["CCPD_PULSE_GATE"]["WIDTH"]=gate_width
        self.dut["CCPD_PULSE_GATE"]["EN"]=1 

        self.dut["CCPD_TDC"].reset()
        self.dut['CCPD_TDC']['EN_INVERT_TDC']=True
        self.dut['CCPD_TDC']['ENABLE_EXTERN']=True
        self.dut['CCPD_TDC']['ENABLE']=False

        self.dut['sram'].reset()

        s="set_tdc gate_width:%d gate_delay:%d tlu:%d"%(gate_width,gate_delay,tlu)
        self.logger.info(s)
    
    def get_tdc(self):
        self.dut['sram'].reset()
        self.dut["CCPD_PULSE_GATE"].start()
        i=0
        while i<10000:
            if self.dut['CCPD_PULSE_GATE'].is_done():
                break
            elif i> 100:
                time.sleep(0.001) # avoid CPU 100%
            i=i+1
        if i==10000:
            self.logger.info("ERROR timeout")
        return self.dut['sram'].get_data()
    
    def get_data_now(self):
       return self.dut["sram"].get_data()
    
    def save_data_continuous(self,timeout=-1):
       fname=time.strftime("data_%y%m%d-%H%M%S")
       self.logger.info("fname:%s.npy"%fname) 
       t0=time.time() 
       while True:
         with open("%s_%d.npy"%(fname,i/10000),"ab") as f:
               d=self.dut['sram'].get_data()
               if len(d)==0:
                   time.sleep(0.1)
               else:
                   np.save(f,d)
                   f.flush()
               if (time.time()-t0> timeout) and timeout>0:
                   break

###################
### tune and  scan
    def scan_th(self,b=0.78,e=0.7,s=-0.01,mode="src",save=True,pix=[14,25]):
        self.dut['CCPD_TH'].set_voltage(b, unit='V')
        thlist=np.arange(b,e,s)
        if save==True:
            fname=time.strftime("hit_%y%m%d-%H%M%S.npy")
            self.logger.info("scan_th fname:%s"%fname)
            with open(fname,"ab+") as f:
                np.save(f,thlist)
        for th in thlist[1:]:
            d=self.get_hit()
            th_meas=self.dut['CCPD_TH'].get_voltage(unit='V')
            self.dut['CCPD_TH'].set_voltage(th, unit='V')
            d=self.analyse_hit(d,"img")
            if self.plot==True:
                self.ax[0,0].pcolor(d,vmin=0)
                plt.pause(0.001)
            self.logger.info("scan_th %f %d %s"%(th_meas,np.sum(d),str(d[pix[0],pix[1]])))
            if save==True:
                with open(fname,"ab+") as f:
                    np.save(f,d)
        if save==True:
            return fname
    
    def scan_th_tdc(self,b=1.1,e=0.7,s=-0.01):
            self.dut['CCPD_TH'].set_voltage(b, unit='V')       
            self.logger.info("scan_th_tdc_simple th cnt ave std")
            for th in np.arange(b+s,e+s,s):
                d=self.get_tdc()
                th_meas=self.dut['CCPD_TH'].get_voltage(unit='V')
                self.dut['CCPD_TH'].set_voltage(th, unit='V')
                width,timestamp=self.analyse_tdc(d)
                cnt=len(width)
                ave=np.average(width[width>0])
                std=np.std(width[width>0])
                self.logger.info("scan_th_tdc_simple %f %d %f %f"%(th_meas,cnt,ave,std))
    
    def source_tdc(self,n=1000,gate_width=10000000,save=False):
        fname=None
        if save==True:
            fname=time.strftime("srctdc_%y%m%d-%H%M%S.npy")
        i=0
        self.set_tdc_src(mode='src',gate_width=gate_width)
        while i<n:
            d=self.get_tdc()
            if save==True:
                with open(fname,"ab+") as f:
                    np.save(f,d)
            width,timestamp=self.analyse_tdc(d)
            cnt=len(width)
            ave=np.average(width[width>0])
            std=np.std(width[width>0])
            self.logger.info("scan_th_tdc_simple %d %d %f %f"%(i,cnt,ave,std))
            i=i+1
        return fname
    
    def scan_inj_tdc(self,b=1.81,e=0.0,s=-0.05,inj_low=0,save=False):
        self.dut["CCPD_Injection_high"].set_voltage(b,unit="V")
        self.inj_high=b
        self.dut["CCPD_Injection_low"].set_voltage(inj_low,unit="V")
        self.inj_low=inj_low
        self.logger.info("scan inj_low inj_high cnt ave std")
        fname=None
        if save==True:
            fname=time.strftime("injtdc_%y%m%d-%H%M%S.npy")
            with open(fname,"wb") as f:
                np.save(f,np.arange(b,e,s))
        for inj in np.arange(b+s,e,s):
            d=self.get_tdc()
            if save==True:
                with open(fname,"ab+") as f:
                   np.save(f,d) 
            self.dut["CCPD_Injection_high"].set_voltage(inj,unit="V")
            self.inj_high=inj
            width,delay=self.analyse_tdc(d)
            cnt=len(width)
            ave=np.average(width)
            std=np.std(width)
            self.logger.info("scan_inj_tdc %f %f %d %f %f"%(self.inj_low,self.inj_high,cnt,ave,std))
        d=self.get_tdc()
        if save==True:
            with open(fname,"ab+") as f:
                np.save(f,d) 
        width,delay=self.analyse_tdc(d)
        cnt=len(width)
        ave=np.average(width)
        std=np.std(width)
        self.logger.info("scan_inj_tdc %f %f %d %f %f"%(self.inj_low,self.inj_high,cnt,ave,std))
        return fname
#################
### analyse data ###TODO separate file
    def analyse_hit(self,dat,fmt="zs"):
        dat=dat[(dat & 0xF0000000)==0x60000000]
        ret=np.empty([16,len(dat)],dtype=bool)
        for i in range(16):
            ret[15-i,:]= (dat & 2**i ==0)  ### the first bit goes to ret[15,0]
        ret=np.reshape(ret,len(dat)*16,order="F")
        if fmt=="zs":
            ret=np.argwhere(ret==True)[:,0] 
            if len(ret)!=0:
                frame,col,row=self._build_img(ret)
                ret=np.transpose(np.array([frame,col,row]))
                return ret
            else:
                return np.array([])
        elif fmt=="zs_frame":
            ret=np.argwhere(ret==True)[:,0]
            if len(ret)!=0:
                frame,col,row=self._build_img(ret)
                frame=(dat[ret/16] & 0x0FFF0000)>>16
                ret=np.transpose(np.array([frame,col,row]))
                return ret
            else:
                return np.array([])
        elif fmt=="img":
            img=np.zeros([26,106])
            for i in range(0,len(ret),2768):
                img=np.add(img,self._build_img2(ret[i:i+2756][::-1]))
            return img
        else:
            return "ERROR!! fmt=img,zs,zs_frame" ### TODO to be an exception?
    
    def analyse_tdc(self,dat,tdc_trig_dist=False):
        dat=dat[dat & 0xF0000000==0x50000000]
        ret0=dat & 0x00000FFF
        if tdc_trig_dist:
            ret1=np.right_shift(dat & 0x000FF000,12)
            ret2=np.right_shift(dat & 0x0FF00000,20)
            return ret0,ret1,ret2
        else:
            ret1=np.right_shift(dat & 0x0FFFF000,12)
            return ret0,ret1
    
    def analyse_adc(self,dat):
        dat=dat[dat & 0xe0000000==0xe0000000]
        if dat[0]& 0xf0000000!=0xf0000000:
            self.logger.info("analyse_adc: first adc data was not the first data 0x%x"%dat[0])
        return dat & 0x00003FFF

    def init_plot(self):
        self.plot=True
        plt.ion()
        fig,self.ax=plt.subplots(2,2)
        plt.pause(0.001)
        self.ax[0,0].autoscale(False)
        self.ax[1,0].autoscale(False)
        self.ax[0,0].set_xbound(0,106)
        self.ax[0,0].set_ybound(0,24)
        self.ax[1,0].set_xbound(0,106)
        self.ax[1,0].set_ybound(0,24)
        
if __name__=="__main__":
    l=lfcpix.lfcpix()




 



 
