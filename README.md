# PrAnCER

Automated gait tracking of rodents, gait parameter extraction, and manual curation of rodent gait 
data.


## Getting Started

### Prerequisites
The system has been tested on windows and mac environments.

### Installing
First, install Anaconda (Python 3.6 version).

If desired, create a new environment for running PrAnCER

```
conda env create -n prancer
source activate prancer
```

Install additional required repositories from conda forge

```
conda-install -c conda-forge opencv 
conda install -c conda-forge pims
conda install -c conda-forge av
```

Clone the git repository (you'll need git installed)

```
git clone https://github.com/hayleybounds/PrAnCER.git
```
