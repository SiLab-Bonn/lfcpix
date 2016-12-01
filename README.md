# LFCPIX

DAQ for LFCPIX prototype based on [Basil](https://github.com/SiLab-Bonn/basil) framwork.

## Instalation

See [.travis.yml](.travis.yml) for detail.

- Install [conda](http://conda.pydata.org) for python and needed packages :
```bash
curl https://repo.continuum.io/miniconda/Miniconda2-latest-Linux-x86_64.sh -o miniconda.sh
bash miniconda.sh -b -p $HOME/miniconda
export PATH=$HOME/miniconda/bin:$PATH
conda update --yes conda
conda install --yes numpy bitarray pytest pyyaml numba mock matplotlib scipy pytables progressbar
```

- Install [pySiLibUSB](https://github.com/SiLab-Bonn/pySiLibUSB) for USB support

- Clone lfcpix
```bash
git clone https://github.com/SiLab-Bonn/lfcpix.git
cd lfcpix
python setup.py develop
```

- (For firmware development) Download and install [Basil](https://github.com/SiLab-Bonn/basil):
```bash
git clone -b v2.4.3 https://github.com/SiLab-Bonn/basil
cd basil
python setup.py develop 
cd ..
```

- (For simulation) Download and setup [cocotb](https://github.com/potentialventures/cocotb):
```bash
git clone https://github.com/potentialventures/cocotb.git
export COCOTB=$(pwd)/cocotb
cd cocotb
git reset --hard 6ff0d3985a51c681ddd633ad453202c9020c08fe
cd ..
export COCOTB=$(pwd)/cocotb
```

###Detailed instruction for pyBAR (similar software)

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
