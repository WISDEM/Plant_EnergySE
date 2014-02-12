# openWindUtils.py
# 2013 06 25
'''
  Utilities to help run OpenWind from openMDAO
    rdScript(fname, debug=False):
    rdReport(rptpath, debug=False):
 
   G. Scott, NREL 2013 06 25
  
'''

import sys, os
import xml.etree.ElementTree as ET
import numpy as np

# -------------------

def rdReport(rptpath, debug=False):
    ''' read the output of an OpenWind script and extract useful info 
        OpenMDAO also has capabilities for parsing output files (the FileParser object)
        
        USAGE:
        import openWindUtils
        # get rptpath from script with wrtTurbXML.rdScript()
        gross_aep, array_aep, net_aep = openWindUtils.rdReport(rptpath)
        
        Returns:
          Gross = no wakes, no losses applied
          Array = wakes applied, but no losses
          Net = Array * Product_of_losses
          
        Array efficiency can be computed as:  
          Aeff = mean(Array[i]/Gross[i])
    '''
    
    if not os.path.isfile(rptpath):
        sys.stderr.write('OpenWind::rdReport: file "{:}" does not exist\n'.format(rptpath))
        return None
    
    try:
        fh = open(rptpath, 'r')
    except:
        sys.stderr.write('OpenWind::rdReport: error reading file "{:}"\n'.format(rptpath))
        return None
    
    if debug:
        sys.stderr.write('\nOutput of OpenWind::rdReport({:}):\n'.format(rptpath))
    
    foundHdrs = False
    eCaps = []
    aGross = []
    aNet = []
    aArray = []
    genparams = {}
        
    for line in fh.readlines():
        line = line.rstrip()
        
        # general parameters
        
        if line.startswith('\t\t\t\t'):
            gpline = line.strip()
            gp = gpline.split('=')
            if debug:
                print '{:25s} {:}'.format(gp[0], gp[1])
            try:
                genparams[gp[0]] = float(gp[1])
            except:
                try:
                   genparams[gp[0]] = int(gp[1])
                except: 
                   genparams[gp[0]] = gp[1]
        
        # table of turbine values
        
        #if line.startswith('Site Name'):
        if line.find('Gross') > -1 and line.find('Net') > -1:
            f = line.split('\t')
            if len(f) > 2: # skip line that has actual site name
                # get headers and indices
                ival = [None for i in range(len(f))]
                ivDict = {}
                for i in range(len(f)):
                    ivDict[f[i].strip()] = i
                    ival[i] = f[i].strip()
                    if debug:
                        print '{:2d} "{:}"'.format(i,f[i])
                foundHdrs = True
                #print ivDict
                continue
                
        if foundHdrs:
            if len(line) < 1:
                break
            f = line.split('\t')
            if len(f) < len(ival):
                break
            try:
                grossKWh = float(f[ivDict['Gross [kWh]']])
                aGross.append(grossKWh)

                netKWh = float(f[ivDict['Net [kWh]']])
                aNet.append(netKWh)
                
                aEff = float(f[ivDict['Array Efficiency [%%]']])

                arrayKWh = 0.01*aEff*grossKWh
                aArray.append(arrayKWh)
            except:
                sys.stderr.write("Couldn't find turbine output values in line:\n  {:}\n".format(line))
                
            
    fh.close()
    
    gross_aep = np.sum(np.array(aGross))/1000000.
    array_aep = np.sum(np.array(aArray))/1000000.
    net_aep   = np.sum(np.array(aNet))/1000000.  
    
    if debug:
        sys.stderr.write( 'Gross {:.4f} GWh\n'.format(gross_aep) )
        sys.stderr.write( 'Array {:.4f} GWh\n'.format(array_aep) )
        sys.stderr.write( 'Net   {:.4f} GWh\n'.format(net_aep  ) )
        
        sys.stderr.write('\nEnd OpenWind::rdReport({:})\n\n'.format(rptpath))
    
    return gross_aep, array_aep, net_aep    
           
# -------------------

# -------------------

#def rdScript(fname, debug=False):
#    ''' read an OpenWind XML script file and extract useful info 
#        Also lists all operations found in script
#        
#        SEE ALSO: wrtScriptXML.rdScript() - uses lxml
#    '''
#    
#    e = ET.parse(fname)
#    if debug:
#        sys.stderr.write('\nrdScript: {:}\n'.format(fname))
#    
#    # Get ReportPath so we know where to look for results
#    
#    for atype in e.findall('ReportPath'):
#        rptpath = atype.get('value').replace('\\','/')
#        if debug:
#            sys.stderr.write('  ReportPath: {:}\n'.format(rptpath))        
#
#    nop = 0
#    if debug:
#        sys.stderr.write('  Operations:\n')
#    for aotype in e.findall('AllOperations'):
#        for atype in aotype.findall('Operation'):
#            nop += 1
#            optype = atype.find('Type').get('value') 
#            if debug:
#                sys.stderr.write('    Operation {:}: {:}\n'.format(nop, optype))        
#    if debug:
#        sys.stderr.write('\n')
#       
#    return rptpath
        
