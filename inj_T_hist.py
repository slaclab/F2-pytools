# script to grab injector temperature histories and "normalize" them

import numpy as np
import os,sys
import meme.archive as arch
from urllib.request import urlopen
import json
from datetime import datetime, timedelta
from matplotlib import pyplot as plt

ARC_LINK = 'http://facet-archapp.slac.stanford.edu/retrieval/data/getData.csv?pv={}&from={}&to={}'

INJ_TEMP_PVS = [
    'LASR:LR10:1:OSC_OUTLET',
    'LASR:LR10:1:TABLETEMP1',
    'LASR:LR10:1:OSCILATOR',
    'LASR:LR10:1:REGEN',
    'GUN:IN10:111:WGBDYTEMP1',
    'CATH:IN10:111:TEMP1',
    ]
INJ_TEMP_LABELS = [
    'Chiller',
    'Laser Table',
    'Vitara',
    'Regen',
    'MPA',
    'Gun waveguide',
    'Cathode',
    ]

def main():
    for PV, label in zip(INJ_TEMP_PVS, INJ_TEMP_LABELS):
        dTemp, dt = normed_T_history(PV, ndays=2)
        plt.plot(dt, dTemp, label=label)
    plt.legend()
    plt.xlabel('time')
    plt.ylabel('dT (degF, normalized)')
    plt.show()
    return

def inj_dT_history():
    temps, times = {}, {}
    for PV, label in zip(INJ_TEMP_PVS, INJ_TEMP_LABELS):
        dTemp, dt = normed_T_history(PV, ndays=2)
        temps[label] = dTemp
        times[label] = dt
    return temps, times

def normed_T_history(temp_PV, ndays=2):
    T_to = datetime.utcnow()
    T_from = T_to - timedelta(days=ndays)
    dTemp = {}
    dt = {}
    req = ARC_LINK.format(
        encode_sepr(temp_PV),
        encode_sepr(encode_datestr(T_from)),
        encode_sepr(encode_datestr(T_to))
        )
    result = urlopen(req).read().decode('utf-8')
    dt = get_data(result, irow=0)
    dTemp = time_norm(get_data(result, irow=1))

    return dTemp, dt

def encode_sepr(pv): return pv.replace(':', '%3A')

def encode_datestr(dt): return dt.strftime('%Y-%m-%dT%H:%M:%S.000Z')

def get_data(result, irow):
    signal = []
    for r in result.split('\n'):
        try: signal.append(float(r.split(',')[irow]))
        except: pass
    return signal

def time_norm(signal): return [x-signal[0] for x in signal]

if __name__ == '__main__':
    main()