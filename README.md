# LFCPIX

DAQ for LFCPIX prototype based on [Basil](https://github.com/SiLab-Bonn/basil) framwork.

## Instalation

- install [conda](http://conda.pydata.org) for python. See [.travis.yml](https://github.com/SiLab-Bonn/lfcpix/blob/master/.travis.yml) for detail.
- for USB support see [pySiLibUSB](https://github.com/SiLab-Bonn/pySiLibUSB)
- install basil
- make a clone of lfcpix

###Detailed instruction

https://github.com/SiLab-Bonn/pyBAR/wiki/Step-by-step-Installation-Guide

## Usage

### Start
```
./ipython.sh
```

### Inject pulses and enable Monitors
```
In [1]: import lfcpix
   ...: l=lfcpix.lfcpix()
   ...: l.set_mon_en([0,0])
   ...: l.set_inj_en([0,0])   
   ...: l.set_inj_all(inj_n=0,inj_high=1.5)
   ...: l.set_th(0.8)
   ...: l.inject()
```
