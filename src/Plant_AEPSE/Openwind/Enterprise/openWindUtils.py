# openWindUtils.py
# 2013 06 25
'''
  Utilities to help run OpenWind from openMDAO
<<<<<<< HEAD
    rdReport(rptpath, debug=False):
    class owWindTurbine()
    rdOWTG(fname)
    
  For reading/writing OpenWind scripts, see wrtScriptXML.py
    rdScript(fname, debug=False):
  
   G. Scott, NREL 2013 06 25
   
   Move wrtTurbXML.py into this file?
=======
    rdScript(fname, debug=False):
    rdReport(rptpath, debug=False):
 
   G. Scott, NREL 2013 06 25
>>>>>>> 24199616d6558da868dd109518be1732fad705cd
  
'''

import sys, os
<<<<<<< HEAD
import numpy as np
from lxml import etree

# ---------------------

class owWindTurbine():
    ''' represents a single wind turbine in a layout and its location, energy production, wind speed, etc.
        (This does NOT represent a particular model of turbine and its physical properties -
          see ???.py for that)
    '''
    
    def __init__(self):
        # create an empty owWindTurbine object with default (invalid) values
        self.x = -9999.9
        self.y = -9999.9
        self.tIndex = -1
        self.gross = -9999.9
        self.net = -9999.9
        self.aeff = -9999.9
        self.freeWS = -9999.9
        self.meanWS = -9999.9
    
    def parseLine(self, line, hdrs):
        # parse line from an OpenWind energy capture report and set variables
        # hdrs[] must be  list of the variable names from the report line immediately
        #   preceding the turbine data lines. E.g.,
        #     Site	Index	X[m]	Y[m]	Gross [kWh]	Net [kWh]	Array Efficiency [%%]	Free Speed [m/s]	Mean Speed [m/s]	Turbulence Intensity [%%]	TI@15 [%%]	
        
        f = line.strip().split('\t')
        for i in range(len(hdrs)):
            if hdrs[i] == 'X[m]':
                self.x = float(f[i])
            if hdrs[i] == 'Y[m]':
                self.y = float(f[i])
            if hdrs[i] == 'Index':
                self.tIndex = int(f[i])
            if hdrs[i] == 'Gross [kWh]':
                self.gross = float(f[i])
            if hdrs[i] == 'Net [kWh]':
                self.net = float(f[i])
            if hdrs[i] == 'Array Efficiency [%%]':
                self.aeff = float(f[i])
            if hdrs[i] == 'Free Speed [m/s]':
                self.freeWS = float(f[i])
            if hdrs[i] == 'Mean Speed [m/s]':
                self.meanWS = float(f[i])
                

    def __str__(self):
        # default print method
        # if any class members are None, this will bomb
        
        return '{:3d} {:9.1f} {:9.1f} {:9.3f} {:9.3f} {:6.2f} {:5.2f} {:5.2f}'.format(self.tIndex, 
          self.x, self.y, 
          self.gross * 0.001, # kWh to mWh
          self.net * 0.001, 
          self.aeff, 
          self.freeWS, self.meanWS)
          
=======
import xml.etree.ElementTree as ET
import numpy as np

>>>>>>> 24199616d6558da868dd109518be1732fad705cd
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
<<<<<<< HEAD
          
        X and Y positions can be read from file IF they have been specified in 'Output Fields' in scripter menu
          'X [m]' and 'Y [m]'
          <TurbineXField value="true"/>
          <TurbineYField value="true"/>
=======
>>>>>>> 24199616d6558da868dd109518be1732fad705cd
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
<<<<<<< HEAD
    hdrs = []
    nErrors = 0
=======
>>>>>>> 24199616d6558da868dd109518be1732fad705cd
    eCaps = []
    aGross = []
    aNet = []
    aArray = []
    genparams = {}
<<<<<<< HEAD
    xTurb = []
    yTurb = []
    owTrbs = [] # list of owWindTurbine objects
    ival = []
    ivDict = {}
=======
>>>>>>> 24199616d6558da868dd109518be1732fad705cd
        
    for line in fh.readlines():
        line = line.rstrip()
        
        # general parameters
<<<<<<< HEAD
        # 2014 02 17 - when do these appear? where are they used? (not used at the moment)
=======
>>>>>>> 24199616d6558da868dd109518be1732fad705cd
        
        if line.startswith('\t\t\t\t'):
            gpline = line.strip()
            gp = gpline.split('=')
            if debug:
<<<<<<< HEAD
                sys.stderr.write('{:25s} {:}\n'.format(gp[0], gp[1]))
=======
                print '{:25s} {:}'.format(gp[0], gp[1])
>>>>>>> 24199616d6558da868dd109518be1732fad705cd
            try:
                genparams[gp[0]] = float(gp[1])
            except:
                try:
                   genparams[gp[0]] = int(gp[1])
                except: 
                   genparams[gp[0]] = gp[1]
        
<<<<<<< HEAD
        # Error reported by OpenWind
        
        foundError = False
        if line.startswith('Failed to find and replace turbine type'):
            foundError = True
        if line.find('not have access to an appropriate WRG') > -1:
            foundError = True
        if foundError:
            sys.stderr.write('\n{:}\n'.format(line))
            nErrors += 1
            
        # table of turbine values
        #   There is no sure way of recognizing the header line, since its contents can vary.
        #   Here, we look for 'Gross' and 'Net' columns.
        
        #if line.startswith('Site Name'):
        if line.find('Gross') > -1 and line.find('Net') > -1:
            hdrs = line.split('\t')
            if len(hdrs) > 2: # skip line that has actual site name
                # get headers and indices
                ival = [None for i in range(len(hdrs))]
                ivDict = {}
                for i in range(len(hdrs)):
                    hval = hdrs[i].strip()
                    ivDict[hval] = i
                    ival[i] = hval
                    if debug:
                        sys.stderr.write('{:2d} "{:}" "{:}"\n'.format(i,hdrs[i], hval))
                foundHdrs = True
                continue
            
                
        # individual turbine lines immediately follow the header line
=======
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
>>>>>>> 24199616d6558da868dd109518be1732fad705cd
                
        if foundHdrs:
            if len(line) < 1:
                break
            f = line.split('\t')
            if len(f) < len(ival):
<<<<<<< HEAD
                break # end of turbine lines
                
            try:
                grossKWh = float(f[ivDict['Gross [kWh]']])
            except:
                sys.stderr.write("Couldn't find gross in line:\n  {:}\n".format(line))
            try:
                netKWh = float(f[ivDict['Net [kWh]']])
            except:
                sys.stderr.write("Couldn't find net   in line:\n  {:}\n".format(line))
            try:
                aEff = float(f[ivDict['Array Efficiency [%%]']])
            except:
                sys.stderr.write("Couldn't find array in line:\n  {:}\n".format(line))
                
            arrayKWh = 0.01*aEff*grossKWh
            aGross.append(grossKWh)
            aNet.append(netKWh)
            aArray.append(arrayKWh)
            #print '{:.2f} {:.2f} {:.2f} {:.2f} '.format(grossKWh, netKWh, arrayKWh, aEff)
            
            if ('X[m]' in ivDict and 'Y[m]' in ivDict):
                xTurb.append(float(f[ivDict['X[m]']]))
                yTurb.append(float(f[ivDict['Y[m]']]))
                
            newTurb = owWindTurbine()
            newTurb.parseLine(line,hdrs)
            owTrbs.append(newTurb)
            
    fh.close()
    
    # Summarize
    
    gross_aep = np.sum(np.array(aGross))/1000000.  # kWh to gWh
    array_aep = np.sum(np.array(aArray))/1000000.
    net_aep   = np.sum(np.array(aNet))/1000000.  
    nTurb = len(aGross)
    
    if debug:
        sys.stderr.write( 'N(turbines) {:}\n'.format(nTurb))
=======
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
>>>>>>> 24199616d6558da868dd109518be1732fad705cd
        sys.stderr.write( 'Gross {:.4f} GWh\n'.format(gross_aep) )
        sys.stderr.write( 'Array {:.4f} GWh\n'.format(array_aep) )
        sys.stderr.write( 'Net   {:.4f} GWh\n'.format(net_aep  ) )
        
<<<<<<< HEAD
        if (len(xTurb) > 0):
            sys.stderr.write('X range {:9.1f} to {:9.1f} m\n'.format(np.min(xTurb), np.max(xTurb)))
            sys.stderr.write('Y range {:9.1f} to {:9.1f} m\n'.format(np.min(yTurb), np.max(yTurb)))
    
        sys.stderr.write('\nEnd OpenWind::rdReport({:})\n\n'.format(rptpath))
    
    if nErrors > 0:
        sys.stderr.write('Found {:} errors while reading {:}\n'.format(nErrors, rptpath))
            
    return gross_aep, array_aep, net_aep, owTrbs   
           
# -------------------

# function rdOWTG replaced with getTurbParams in rwTurbXML.py : 2014 03 31
=======
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
        
>>>>>>> 24199616d6558da868dd109518be1732fad705cd
