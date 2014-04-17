# findOW.py
# 2014 04 17

# Look for an openWind executable in the usual places

import sys, os

def findOW(debug=False):
    ow_paths = ['C:/rassess/Openwind',  # GNS
                'C:/Models/Openwind',   # KLD
               ]
    
    for owp in ow_paths:
        owname = '/'.join([owp,'openWind64.exe'])
        if os.path.isfile(owname):
            if debug:
                sys.stderr.write('findOW: found {:}\n'.format(owname))
            return owname
            
    sys.stderr.write('findOW: OpenWind executable file not found in ow_paths\n')
    return None
