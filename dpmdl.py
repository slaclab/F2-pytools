# script to grab PMDL data from the archive and "normalize" it 

import numpy as np
import os,sys
import meme.archive as arch
from urllib.request import urlopen
import json
from datetime import datetime, timedelta
from matplotlib import pyplot as plt

SBST_PVS = [f'LI1{i}:SBST:1:PMDL' for i in range(1,10)]
ARC_LINK = 'http://facet-archapp.slac.stanford.edu/retrieval/data/getData.csv?pv={}&from={}&to={}'

def main():
    signals, _ = normed_pmdl_history(ndays=2)
    for sbst, dp in signals.items():
        plt.plot(dp, label=sbst[:4])
    plt.legend()
    plt.xlabel('time')
    plt.ylabel('dPMDL (normalized)')
    plt.show()
    return

def normed_pmdl_history(ndays=2):
    T_to = datetime.utcnow()
    T_from = T_to - timedelta(days=ndays)
    dPMDL = {}
    dT = {}
    for pv in SBST_PVS:
        req = ARC_LINK.format(
            encode_sepr(pv),
            encode_sepr(encode_datestr(T_from)),
            encode_sepr(encode_datestr(T_to))
            )
        result = urlopen(req).read().decode('utf-8')
        dt = get_data(result, irow=0)
        dT[pv[:4]] = get_data(result, irow=0)
        dPMDL[pv[:4]] = norm_pmdl(get_data(result, irow=1))
        
    return dPMDL, dT

def temp_prs_history(ndays=2):
    T_to = datetime.utcnow()
    T_from = T_to - timedelta(days=ndays)
    dT, Temp, Prs = [],[],[]
    req1 = ARC_LINK.format(
        encode_sepr('ROOM:BSY0:1:OUTSIDETEMP'),
        encode_sepr(encode_datestr(T_from)),
        encode_sepr(encode_datestr(T_to))
        )
    req2 = ARC_LINK.format(
        encode_sepr('ROOM:BSY0:1:OUTSIDEPRES'),
        encode_sepr(encode_datestr(T_from)),
        encode_sepr(encode_datestr(T_to))
        )
    r1 = urlopen(req1).read().decode('utf-8')
    r2 = urlopen(req2).read().decode('utf-8') 
    dTT = get_data(r1, irow=0)
    Temp = get_data(r1, irow=1)
    dTP = get_data(r2, irow=0)
    Prs = get_data(r2, irow=1)

    return dTT, Temp, dTP, Prs

def encode_sepr(pv): return pv.replace(':', '%3A')

def encode_datestr(dt): return dt.strftime('%Y-%m-%dT%H:%M:%S.000Z')

def get_data(result, irow):
    signal = []
    for r in result.split('\n'):
        try: signal.append(float(r.split(',')[irow]))
        except: pass
    return signal

def norm_pmdl(signal): return [x-signal[0] for x in signal]

if __name__ == '__main__':
    main()