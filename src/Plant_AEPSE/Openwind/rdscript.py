# rdscript.py
# 2014 04 17

import sys, os
from Plant_AEPSE.Openwind.rwScriptXML import rdScript

for fname in sys.argv[1:]:
    sys.stderr.write('Reading {:}\n'.format(fname))
    rdScript(fname, debug=True)
