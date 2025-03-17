# control-system agnostic magnet setter

import os
import sys
from epics import get_pv
import slc_mags
from traceback import print_exc

SLC_QUADS = [
    'QUAD:LI11:401',
    'QUAD:LI11:501',
    'QUAD:LI11:601',
    'QUAD:LI11:701',
    'QUAD:LI11:801',
    'QUAD:LI11:901',
    'QUAD:LI12:201',
    'QUAD:LI12:301',
    'QUAD:LI12:401',
    'QUAD:LI12:501',
    'QUAD:LI12:601',
    'QUAD:LI12:701',
    'QUAD:LI12:801',
    'QUAD:LI12:901',
    'QUAD:LI13:201',
    'QUAD:LI13:301',
    'QUAD:LI13:401',
    'QUAD:LI13:501',
    'QUAD:LI13:601',
    'QUAD:LI13:701',
    'QUAD:LI13:801',
    'QUAD:LI13:901',
    'QUAD:LI14:201',
    'QUAD:LI14:301',
    'QUAD:LI14:401',
    'QUAD:LI14:501',
    'QUAD:LI14:601',
    'QUAD:LI15:201',
    'QUAD:LI15:301',
    'QUAD:LI15:401',
    'QUAD:LI15:501',
    'QUAD:LI15:601',
    'QUAD:LI15:701',
    'QUAD:LI15:801',
    'QUAD:LI15:901',
    'QUAD:LI16:201',
    'QUAD:LI16:301',
    'QUAD:LI16:401',
    'QUAD:LI16:501',
    'QUAD:LI16:601',
    'QUAD:LI16:701',
    'QUAD:LI16:801',
    'QUAD:LI16:901',
    'QUAD:LI17:201',
    'QUAD:LI17:301',
    'QUAD:LI17:401',
    'QUAD:LI17:501',
    'QUAD:LI17:601',
    'QUAD:LI17:701',
    'QUAD:LI17:801',
    'QUAD:LI17:901',
    'QUAD:LI18:201',
    'QUAD:LI18:301',
    'QUAD:LI18:401',
    'QUAD:LI18:501',
    'QUAD:LI18:601',
    'QUAD:LI18:701',
    'QUAD:LI18:801',
    'QUAD:LI18:901',
    'QUAD:LI19:201',
    'QUAD:LI19:301',
    'QUAD:LI19:401',
    'QUAD:LI19:501',
    'QUAD:LI19:601',
    'QUAD:LI19:701',
    'QUAD:LI19:801',
    'QUAD:LI20:2086',
    'LGPS:LI20:2130',
    'LGPS:LI20:2150',
    'LGPS:LI20:2150',
    'LGPS:LI20:2200',
    'LGPS:LI20:2200',
    'LGPS:LI20:2200',
    'LGPS:LI20:2230',
    'LGPS:LI20:2251',
    'LGPS:LI20:2230',
    'LGPS:LI20:2200',
    'LGPS:LI20:2200',
    'LGPS:LI20:2200',
    'LGPS:LI20:2150',
    'LGPS:LI20:2150',
    'LGPS:LI20:2130',
    'LGPS:LI20:2060',
    'LGPS:LI20:3011',
    'LGPS:LI20:3311',
    'LGPS:LI20:3151',
    'LGPS:LI20:3091',
    'LGPS:LI20:3141',
    'LGPS:LI20:3151',
    'LGPS:LI20:3204',
    'LGPS:LI20:3261',
    'LGPS:LI20:3311',
    ]

SLC_CORRECTORS = [
    'XCOR:LI11:402',
    'YCOR:LI11:403',
    'XCOR:LI11:502',
    'YCOR:LI11:503',
    'XCOR:LI11:602',
    'YCOR:LI11:603',
    'XCOR:LI11:702',
    'YCOR:LI11:703',
    'XCOR:LI11:802',
    'YCOR:LI11:803',
    'XCOR:LI11:900',
    'YCOR:LI11:900',
    'XCOR:LI12:202',
    'YCOR:LI12:203',
    'XCOR:LI12:302',
    'YCOR:LI12:303',
    'XCOR:LI12:402',
    'YCOR:LI12:403',
    'XCOR:LI12:502',
    'YCOR:LI12:503',
    'XCOR:LI12:602',
    'YCOR:LI12:603',
    'XCOR:LI12:702',
    'YCOR:LI12:703',
    'XCOR:LI12:802',
    'YCOR:LI12:803',
    'XCOR:LI12:900',
    'YCOR:LI12:900',
    'XCOR:LI13:202',
    'YCOR:LI13:203',
    'XCOR:LI13:302',
    'YCOR:LI13:303',
    'XCOR:LI13:402',
    'YCOR:LI13:403',
    'XCOR:LI13:502',
    'YCOR:LI13:503',
    'XCOR:LI13:602',
    'YCOR:LI13:603',
    'XCOR:LI13:702',
    'YCOR:LI13:703',
    'XCOR:LI13:802',
    'YCOR:LI13:803',
    'XCOR:LI13:900',
    'YCOR:LI13:900',
    'XCOR:LI14:202',
    'YCOR:LI14:203',
    'XCOR:LI14:302',
    'YCOR:LI14:303',
    'XCOR:LI14:402',
    'YCOR:LI14:403',
    'XCOR:LI14:502',
    'YCOR:LI14:503',
    'XCOR:LI14:602',
    'YCOR:LI14:603',
    'XCOR:LI14:702',
    'YCOR:LI14:703',
    'XCOR:LI14:900',
    'YCOR:LI14:900',
    'XCOR:LI15:202',
    'YCOR:LI15:203',
    'XCOR:LI15:302',
    'YCOR:LI15:303',
    'XCOR:LI15:402',
    'YCOR:LI15:403',
    'XCOR:LI15:502',
    'YCOR:LI15:503',
    'XCOR:LI15:602',
    'YCOR:LI15:603',
    'XCOR:LI15:702',
    'YCOR:LI15:703',
    'XCOR:LI15:802',
    'YCOR:LI15:803',
    'XCOR:LI15:900',
    'YCOR:LI15:900',
    'XCOR:LI16:202',
    'YCOR:LI16:203',
    'XCOR:LI16:302',
    'YCOR:LI16:303',
    'XCOR:LI16:402',
    'YCOR:LI16:403',
    'XCOR:LI16:502',
    'YCOR:LI16:503',
    'XCOR:LI16:602',
    'YCOR:LI16:603',
    'XCOR:LI16:702',
    'YCOR:LI16:703',
    'XCOR:LI16:802',
    'YCOR:LI16:803',
    'XCOR:LI16:900',
    'YCOR:LI16:900',
    'XCOR:LI17:202',
    'YCOR:LI17:203',
    'XCOR:LI17:302',
    'YCOR:LI17:303',
    'XCOR:LI17:402',
    'YCOR:LI17:403',
    'XCOR:LI17:502',
    'YCOR:LI17:503',
    'XCOR:LI17:602',
    'YCOR:LI17:603',
    'XCOR:LI17:702',
    'YCOR:LI17:703',
    'XCOR:LI17:802',
    'YCOR:LI17:803',
    'XCOR:LI17:900',
    'YCOR:LI17:900',
    'XCOR:LI18:202',
    'YCOR:LI18:203',
    'XCOR:LI18:302',
    'YCOR:LI18:303',
    'XCOR:LI18:402',
    'YCOR:LI18:403',
    'XCOR:LI18:502',
    'YCOR:LI18:503',
    'XCOR:LI18:602',
    'YCOR:LI18:603',
    'XCOR:LI18:702',
    'YCOR:LI18:703',
    'XCOR:LI18:802',
    'YCOR:LI18:803',
    'XCOR:LI18:900',
    'YCOR:LI18:900',
    'XCOR:LI19:202',
    'YCOR:LI19:203',
    'XCOR:LI19:302',
    'YCOR:LI19:303',
    'XCOR:LI19:402',
    'YCOR:LI19:403',
    'XCOR:LI19:502',
    'YCOR:LI19:503',
    'XCOR:LI19:602',
    'YCOR:LI19:603',
    'YCOR:LI19:700',
    'XCOR:LI19:700',
    'XCOR:LI19:802',
    'YCOR:LI19:803',
    'XCOR:LI19:900',
    'YCOR:LI19:900',
    'XCOR:LI20:1996',
    'YCOR:LI20:2087',
    'XCOR:LI20:2096',
    'XCOR:LI20:2176',
    'YCOR:LI20:2181',
    'YCOR:LI20:2230',
    'YCOR:LI20:2267',
    'YCOR:LI20:2321',
    'XCOR:LI20:2326',
    'XCOR:LI20:2396',
    'BTRM:LI20:2420',
    'XCOR:LI20:2460',
    'XCOR:LI20:3026',
    'YCOR:LI20:3017',
    'YCOR:LI20:3057',
    'XCOR:LI20:3086',
    'XCOR:LI20:3276',
    'XCOR:LI20:3116',
    'YCOR:LI20:3147',
    ]

SLC_BENDS = [
    'LGPS:LI20:1990',
    'LGPS:LI20:2110',
    'LGPS:LI20:2240',
    'LGPS:LI20:2240',
    'LGPS:LI20:2110',
    'LGPS:LI20:2420',
    'BTRM:LI20:2420',
    'LGPS:LI20:2420',
    'LGPS:LI20:1990',
    'BEND:LI20:3330',
    ]

ALL_SLC_MAGNETS = SLC_CORRECTORS + SLC_QUADS + SLC_BENDS

def _is_legacy_dev_name(device):
    return (device[:2] == 'LI')

def _is_SLC_device(device):
    """ returns true if the magnet is controlled via SCP """
    return _is_legacy_dev_name(device) or (device in ALL_SLC_MAGNETS)

def _switch_primary_micro(device):
    """ switch things like LI14:QUAD --> QUAD:LI14 and vice versa """
    ds = device.split(':')
    return f'{ds[1]}:{ds[0]}:{ds[2]}'

def set_magnets(devices, values, timeout=12):
    """
    set an arbitrary number of magnet BDESes, 'devices' may contain either
    SLC or EPICS magnets.

    NOTE: EPICS magnets and SLC magnets will be set in steps as separate groups
    so the order of magnet trims may not match the order of 'devices'/'values'
    """
    if len(devices) != len(values): raise ValueError('device/value list mismatch')

    # split device/value list into EPICS & SLC parts
    slc_devices, slc_values = [], []
    epics_devices, epics_values = [], []
    for dev,val in zip(devices, values):
        if _is_SLC_device(dev):
            if _is_legacy_dev_name(dev):
                dev = _switch_primary_micro(dev)
            slc_devices.append(dev)
            slc_values.append(val)
        else:
            epics_devices.append(dev)
            epics_values.append(val)
    
    # set EPICS magnets
    print('Setting EPICS magnets ...')
    for dev,val in zip(epics_devices, epics_values):
        try:
            get_pv(f'{dev}:BDES').put(val)
            get_pv(f'{dev}:CTRL').put(1)
        except Exception as e:
            print(f'failed to set device: {dev}')
            print_exc(e)

    # set SLC magnets
    print('Setting SLC magnets ...')
    slc_mags.set_magnets(slc_devices, slc_values)
    return

if __name__ == '__main__':
    # shutters UV laser ,test magnet trims
    from time import sleep
    uv_mps = get_pv('IOC:SYS1:MP01:MSHUTCTL')

    print('Stopping beam')
    uv_mps.put(0)
    sleep(1)

    test_magnets = [
        'XCOR:LI11:304',  # EPICS
        'XCOR:LI14:402',  # SLC
        'LI16:XCOR:402',  # SLC (legacy name format)
        ]
    init_bdes = [
        get_pv(f'{test_magnets[0]}:BDES').get(),
        get_pv(f'{_switch_primary_micro(test_magnets[1])}:BDES').get(),
        get_pv(f'{test_magnets[0]}:BDES').get(),
        ]
    mod_bdes = [0.9*b for b in init_bdes]

    print(f'BDES (initial):  {init_bdes}')
    print(f'BDES (modified): {mod_bdes}')
    print('Setting test magnets to 0.9*BDES ...')
    set_magnets(test_magnets, mod_bdes)

    print('Pausing ...')
    sleep(3)

    bacts = [
        get_pv(f'{test_magnets[0]}:BACT').get(),
        get_pv(f'{_switch_primary_micro(test_magnets[1])}:BACT').get(),
        get_pv(f'{test_magnets[0]}:BACT').get(),
        ]
    errs = [bdes-bact for bdes,bact in zip(mod_bdes, bacts)]
    print(f'BDES-BACT: {errs}')

    print('Pausing ...')
    sleep(3)

    print('Restoring test magnets ...')
    set_magnets(test_magnets, mod_bdes)

    print('Restoring beam ...')
    uv_mps.put(1)