from p4p.client.thread import Context
from p4p.nt import NTURI, NTTable

CTX = Context('pva')

F2_ALL_KLYS = []
for s in range(11,20):
    for k in range(1,9):
        F2_ALL_KLYS.append(f'KLYS:LI{s}:{k}1')


URI_KLYS_TACT = NTURI([('TYPE','s'), ('BEAM','s')])
URI_ALL_KLYS = NTURI([('DEVICES','as'), ('BEAM','s')])
NTT_ALL_KLYS = NTTable([
    ('name', 's'),
    ('opstat', '?'),
    ('status','b'),
    ('accel', '?'),
    ('standby', '?'),
    ('bad', '?'),
    ('sled', '?'),
    ('sleded', '?'),
    ('pampl', '?'),
    ('pphas', '?'),
    ])

def get_klys_stat(klys_channel):
    """ get status for a single klytron, returns an int """
    ntval = URI_KLYS_TACT.wrap(
        scheme='pva', path=klys_channel, kws={'TYPE':'SHORT', 'BEAM':'10'}
        )
    res = CTX.rpc(klys_channel, ntval)
    return res.raw.value


def get_all_klys_stat():
    """ get the current status of all SLC klystrons in L2 & L3 as a dict """
    ntval = URI_ALL_KLYS.wrap(
        scheme='pva', path='KLYSTRONGET:TACT', kws={'DEVICES':F2_ALL_KLYS, 'BEAM':'10'}
        )
    res = CTX.rpc('KLYSTRONGET:TACT', ntval)
    k_status = {}
    for r in NTT_ALL_KLYS.unwrap(res): k_status[r['name']] = r
    return k_status
