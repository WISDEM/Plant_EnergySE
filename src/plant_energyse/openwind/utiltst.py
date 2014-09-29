# utiltst.py
# 2014 02 17
# TODO: should this be in release version?

import sys, os
import Plant_AEPSE.Openwind.openWindUtils as owu
import numpy as np

rptpath = 'C:/SystemsEngr/Temp/rpttest.txt'
def main():
    gross_aep, array_aep, net_aep, nTurb, owTrbs = owu.rdReport(rptpath, debug=True)

    gaep = []
    for owt in owTrbs:
        print owt
        gaep.append(owt.gross)
    print 'Gross(total) {:.6f} GWh'.format(np.sum(gaep)*0.000001) # should be same as gross_aep
    
    fname = 'C:/SystemsEngr/Temp/NREL5MW_100m.owtg'
    owu.rdOWTG(fname,debug=True)    
    
#---------------------------------------------------

if __name__ == "__main__":

    main()
