import os,sys,time

class LfcpixLog(): ### TODO separate file
    def __init__(self,logfile='lfcpix.log'):
        self.logfile=logfile
    def info(self,s):
        print s
        s.replace("\n","")
        with open(self.logfile,"a") as f:
            f.write("%s %s\n"%(time.strftime("%Y/%m/%d-%H:%M:%S"),s))
    def archive(self):
        with open('archive_%s'%self.logfile, 'a') as fo:
            try:
                with open(self.logfile) as f:
                    for line in f:
                        fo.write(line)
                with open(self.logfile,"w") as f:
                    f.write("")
            except:
                pass
    def show(self,r,show="all"):
        s=""
        if show=="all" or "power" in show:
          s="%s--------Power--------\n"%s
          s="%sVdda:%f,%f Vddd:%f,%f Vddp:%f,%f VCasc2:%f,%f\n"%(s,
            r["Vdda"],r["Vdda_curr"],r["Vddd"],r["Vddd_curr"],r["Vddp"],r["Vddp_curr"],r["VCasc2"],r["VCasc2_curr"])
          s="%sVCascN:%f,%f VCascP:%f,%f TH:%f,%f"%(s,
            r["VCascN"],r["VCascN_curr"],r["VCascP"],r["VCascP_curr"],r["TH"],r["TH_curr"])
        if show=="all":
            s="%s--------Global DAC--------\n"%s
            s='%sBLRes:%d VAmp:%d VPFB:%d VPFoll:%d VPLoad:%d IComp:%d VSTRETCH:%d\n'%(s,
                r["BLRes"],r["VAmp"],r["VPFB"],r["VPFoll"],r["VPLoad"],r["IComp"],r["VSTRETCH"])
            s='%sIBOTA:%d IBCS:%d WGT:%d LSBdacL:%d LSBdacL2:%d IBCS2:%d\n'%(s,
                r["IBOTA"],r["IBCS"],r["WGT"],r["LSBdacL"],r["LSBdacL2"],r["IBCS2"])
            s="%s--------Pixels--------\n"%s
            s="%ssw_mon:%s sw_inj:%s\n"%(s,r['SW_MON'],r['SW_INJ'])
            s="%spreamp_en:%s\n"%(s,r["PREAMP_EN"])
            s="%sinj_en:%s\n"%(s,r["INJECT_EN"])
            s="%smon_en:%s\n"%(s,r["MON_EN"])
            s="%s--------Pulser--------\n"%s
            s="%sinj_width:%d inj_delay:%d inj_n:%d inj_en:%d\n"%(s,
                r['INJ_WIDTH'],r['INJ_DELAY'],r['INJ_REPEAT'],r['INJ_EN'])
            s="%sinj_high:%f inj_low:%f\n"%(s,r['inj_high'],r['inj_low'])
            s="%sgate_width:%d gate_delay:%d gate_n:%d inj_en:%d\n"%(s,
                r['GATE_WIDTH'],r['GATE_DELAY'],r['GATE_REPEAT'],r['GATE_EN'])
            s="%s--------Switch--------\n"%s ###TODO
            #s="%s,CCPD_SW:%d,(%s)\n"%(s,r["CCPD_SW"],str(self.dut["CCPD_SW"]).split(",",1)[1][:-1])
            #s="%s,rx_SW:%d,(%s)\n"%(s,r["rx_SW"],str(self.dut["rx"]).split(",",1)[1][:-1])
            s="%s--------SPI--------\n"%s
            s="%s sr_repeat:%d sr_wait:%d sr_en:\n"%(s,
                r["SR_REPEAT"],r["SR_WAIT"])
            s="%s--------FPGA--------\n"%s ###TODO
            #s="%stlu:%s\n"%(s,str(self.dut["tlu"]))
            #s="%stdc:%s\n"%(s,str(self.dut["CCPD_TDC"]))
        self.info(s)
