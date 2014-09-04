# findOW.py
# 2014 04 17

# Look for an openWind executable in the usual places
# TODO: eliminate this from the release version? or have user input added?

import sys, os

def findOW(academic=False, debug=False):
    ow_paths = ['C:/rassess/Openwind',  # GNS
                'C:/Models/Openwind',   # KLD
               ]
    ow = 'openWind64.exe'
    if academic:
        ow = 'openWind64_ac.exe'
        
    for owp in ow_paths:
        owname = '/'.join([owp,ow])
        if os.path.isfile(owname):
            if debug:
                sys.stderr.write('findOW: found {:}\n'.format(owname))
            return owname
            
    sys.stderr.write('findOW: OpenWind executable file not found in ow_paths\n')
    return None
