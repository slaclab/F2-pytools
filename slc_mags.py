from p4p.client.thread import Context
from p4p.nt import NTURI

"""
Written by D. Cesar and modified by C. Zimmer
"""

magset_typedef = NTURI([('MAGFUNC', 's'), ('LIMITCHECK', 's'), ('VALUE', ('S', 'query', [('names', 'as'), ('values', 'ad')]))])
db_typedef = NTURI([('TYPE', 's'), ('TABLE_TYPE', 's')])
ctx = Context("pva")

def set_magnets(pvs, vals, control='BDES', magfunc='TRIM', limitcheck='SOME', timeout=12, tryagain=True):
    """
    aidapva_magnetset can be used to set SLC magnet properties through aida-pva interface.
    https://www.slac.stanford.edu/grp/cd/soft/aida/aida-pva/md_docs_1_06__users__guide__s_l_c__magnet__channel__provider.html
    Args:
    - pvs (list of strings or string): pv names for the magnets
    - vals (list of values or float): values to be set corresponding to the pvs.
    - control (str) ['BDES']: "BDES", "VDES", or "BCON". BDES is the desired B field.
      VDES is the desired current for strings in SLC. BCON is the "config" value for the B field.
      It doesn't change the magnet but does change some readbacks and system warnings that compare BACT to BCON.
    - magfunc (str) ['TRIM']: one of "TRIM", "PTRB", or "NOFUNC".
      Note that when TRIM is selected, BDES/VDES is also changed, then the magnet is trimmed.
      If BCON is selected then magfunc does not apply.
    - limitcheck (str) ['SOME']: one of "ALL" (the whole command will fail if any limits fail).
      If BCON is selected then limitcheck does not apply.
      or "SOME".
    - timeout (flost) [7]: timeout in seconds for the rpc call
    - tryagain (bool) [True]: if the command timesout, try again with 10 second longer timeout period. If false, do nothing.

    Returns:
    - res: the output of the rpc call.

    Examples:
    - set a magnet:
      set_magnets('YCOR:LI13:303', 0.001)
    - set BDES (without trimming) for many magnets:
      set_magnets(['YCOR:LI13:303', 'YCOR:LI13:403'], [0, 0], magfunc='NOFUNC')
    """
     # First cast to list if needed
    if not isinstance(pvs, list):
        pvs = [pvs]
    if not isinstance(vals, list):
        vals = [vals] * len(pvs)  # e.g. if user gives multiple devices but wants them all set to same value
    pvs = check_epics_format(pvs[:])
    # Now setup command based on desired user type
    if control == 'BDES':
        value = magset_typedef.wrap(scheme='pva', path='MAGNETSET:BDES', kws={'MAGFUNC': magfunc, 'LIMITCHECK': limitcheck, 'VALUE': {'names': pvs, 'values': vals}})
        name = 'MAGNETSET:BDES'
    elif control == 'VDES':
        value = magset_typedef.wrap(scheme='pva', path='MAGNETSET:VDES', kws={'MAGFUNC': magfunc, 'LIMITCHECK': limitcheck, 'VALUE': {'names': pvs, 'values': vals}})
        name = 'MAGNETSET:VDES'
    elif control == 'BCON':
        value = magset_typedef.wrap(scheme='pva', path='MAGNETSET:BCON', kws={'VALUE': {'names': pvs, 'values': vals}})
        name = 'MAGNETSET:BCON'
    else:
        print("Unknown control. Choose 'BDES', 'VDES', or 'BCON'.")
    # Finally try to submit the command
    try:
        res = ctx.rpc(name, value, timeout=timeout)
    except TimeoutError as e:
        try:
            print('Command timed out')
            if tryagain:
                print('Trying one more time')
                res = ctx.rpc(name, value, timeout=timeout+10)
            else:
                print(f"An error occurred: {e}")
                return None
        except Exception as e:
            print(f"An error occurred: {e}")
            return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
    print('Set SLC magnets! Result:')
    print(res)
    return res


def get_aidapva(pvs, return_types='DOUBLE', timeout=1, tryagain=True):
    """
     Used to access SLC "database" values. Like regular pvs. AFAIK the rpcs commands are one at a time, so the looping is for user convenience only.
      https://www.slac.stanford.edu/grp/cd/soft/aida/aida-pva/md_docs_1_02__users__guide__s_l_c__controls__database__channel__provider.html
        Args:
        - pvs (list of strings or string): pv names for the magnets
        - return_types (list of str or str): values to be set corresponding to the pvs.
        - timeout (flost) [1]: timeout in seconds for the rpc call
        - tryagain (bool) [True]: if the command timesout, try again with 5 second longer timeout period. If false, do nothing.

        Returns:
        - res: a list of values from the rpc calls

        Examples:
        - Read a bact:
          get_aidapva('YCOR:LI13:303:BACT')
        - Read some magnet lengths
          get_aidapva(['YCOR:LI13:303:LEFF','YCOR:LI13:203:LEFF'])
    """
     # First cast to list if needed
    returnscalar = False
    if not isinstance(pvs, list):
        pvs = [pvs]
        returnscalar = True
    if not isinstance(return_types, list):
        return_types = [return_types]*len(pvs)
    results = []
    pvs = check_epics_format(pvs[:])
    for pv, return_type in zip(pvs, return_types):
        value = db_typedef.wrap(scheme='pva', path=pv, kws={'TYPE': return_type})
        try:
            res = ctx.rpc(pv, value, timeout=timeout)
        except TimeoutError as e:
            try:
                print('Command timed out')
                if tryagain:
                    print('Trying one more time')
                    res = ctx.rpc(pv,value,timeout=timeout+5)
                else:
                    print(f"An error occurred: {e}")
                    return None
            except Exception as e:
                print(f"An error occurred: {e}")
                return None
        except Exception as e:
            print(f"An error occurred: {e}")
            return None
        results.append(res)
        if returnscalar:
            results = results[0] #match input format
    return results


def set_aidapva(pvs,vals,value_types='FLOAT_ARRAY',timeout=1,tryagain=True):
    """
     Used to set SLC scalar "database" values. Like regular pvs. AFAIK the rpcs commands are one at a time, so the looping is for user convience only.
      https://www.slac.stanford.edu/grp/cd/soft/aida/aida-pva/md_docs_1_02__users__guide__s_l_c__controls__database__channel__provider.html
        Args:
        - pvs (list of strings or string): pv names for the magnets
        - vals (val or list of vals): values to set the pvs. Each 'val' of the list may be int/float or array ofint/float and must correspond to one the data type below (which may be arrays themselves if the pv holds an array)
        - value_types (list of str or str): FLOAT_ARRAY or INTEGER_ARRAY
        - timeout (flost) [1]: timeout in seconds for the rpc call
        - tryagain (bool) [True]: if the command timesout, try again with 5 second longer timeout period. If false, do nothing.

        Returns:
        - none

        Examples:
        - set a bcon:
          set_aidapva('YCOR:LI13:303:BCON',0.001)

    """
    #setup typedef for pva
    if value_types == 'FLOAT_ARRAY':
        db_typedef=NTURI([('VALUE','af'),('VALUE_TYPE','s')])
    elif value_types == 'INTEGER_ARRAY':
        db_typedef=NTURI([('VALUE','ai'),('VALUE_TYPE','s')])
    else:
        print('Unknown value type, try FLOAT_ARRAY or INTEGER_ARRAY')
        return

     # Cast to list if needed
    if not isinstance(pvs, list):
        pvs = [pvs]
    if not isinstance(vals, list):
        vals = [vals]*len(pvs)
    if not isinstance(value_types, list):
        value_types = [value_types]*len(pvs)

    for pv, val, value_type in zip(pvs,vals,value_types):
        if not isinstance(val, list):
            val = [val] # again make a list, since our typedef is expecting a list (and though some pvs are scalars, some are natively lists, so this if loop won't execute)
        value = db_typedef.wrap(scheme='pva', path=pv, kws={'VALUE':val,'VALUE_TYPE': value_type})
        try:
            res = ctx.rpc(pv, value, timeout=timeout)
        except TimeoutError as e:
            try:
                print('Command timed out')
                if tryagain:
                    print('Trying one more time')
                    res = ctx.rpc(pv,value,timeout=timeout+5)
                else:
                    print(f"An error occurred: {e}")
                    return None
            except Exception as e:
                print(f"An error occurred: {e}")
                return None
        except Exception as e:
            print(f"An error occurred: {e}")
            return None
    return res


def check_epics_format(pvs):
    """Simple function to make sure magnets are in epics form, i.e. XCOR:LI14:402 and not LI14:XCOR:402"""
    for i, pv in enumerate(pvs):
        if pv[:2] in ["LI", "IN"]:
            spl_pv = pv.split(":")
            new_pv = f'{spl_pv[1]}:{spl_pv[0]}:{spl_pv[2]}'
            pvs[i] = new_pv
    return pvs