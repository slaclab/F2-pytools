from p4p.client.thread import Context
from p4p.nt import NTURI, NTTable

CTX = Context('pva')
MKB_ADDR = 'MKB:VAL'
URI_MKB_SET = NTURI([('VALUE','s'), ('MKB','s')])

def set_mkb(name, delta):
    """ adjust an SLC multiknob by the value delta """
    ntval = URI_MKB_SET.wrap(
        scheme='pva', path=MKB_ADDR, kws={'VALUE':delta, 'MKB':name}
        )
    return CTX.rpc(MKB_ADDR, ntval)
