# openWindUtils.py
# 2013 06 25
'''
  Utilities to help run OpenWind from openMDAO
    rdReport(rptpath, debug=False):
    class owWindTurbine()
    rdOWTG(fname)
    
  For reading/writing OpenWind scripts, see rwScriptXML.py
  
   G. Scott, NREL 2013 06 25
   
   2014 09 26 : rdReport() - skip turbines with zero output
   2014 09 29:  owWindTurbine() - added 'ttype' field
   
   2015 04 08: changed parsing of header line (added getValue())
     somewhere in the last few OpenWind updates, Nick changed the units
     on Array Efficiency and TI from '%%' to '%'
   
'''

import sys, os
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
        self.ttype = 'none'
    
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
            if hdrs[i] == 'Type':
                self.ttype = f[i]
                

    def __str__(self):
        # default print method
        # if any class members are None, this will bomb
        
        return '{:3d} {:9.1f} {:9.1f} {:9.3f} {:9.3f} {:6.2f} {:5.2f} {:5.2f} {:}'.format(self.tIndex, 
          self.x, self.y, 
          self.gross * 0.001, # kWh to mWh
          self.net * 0.001, 
          self.aeff, 
          self.freeWS, self.meanWS, self.ttype)
          
# -------------------

def rdReport(rptpath, debug=False):
    ''' read the output of an OpenWind script and extract useful info 
        OpenMDAO also has capabilities for parsing output files (the FileParser object)
        
        USAGE:
        import openWindUtils
        # get rptpath from script with rwTurbXML.rdScript()
        gross_aep, array_aep, net_aep = openWindUtils.rdReport(rptpath)
        
        Returns:
          Gross = no wakes, no losses applied
          Array = wakes applied, but no losses
          Net = Array * Product_of_losses
          owTrbs = list of owWindTurbine objects
          
        Array efficiency can be computed as:  
          Aeff = mean(Array[i]/Gross[i])
          
        X and Y positions can be read from file IF they have been specified in 'Output Fields' in scripter menu
          'X [m]' and 'Y [m]'
          <TurbineXField value="true"/>
          <TurbineYField value="true"/>
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
    hdrs = []
    nErrors = 0
    eCaps = []
    aGross = []
    aNet = []
    aArray = []
    genparams = {}
    xTurb = []
    yTurb = []
    owTrbs = [] # list of owWindTurbine objects
    ival = []
    ivDict = {}
        
    for line in fh.readlines():
        line = line.rstrip()
        
        # general parameters
        # 2014 02 17 - when do these appear? where are they used? (not used at the moment)
        
        if line.startswith('\t\t\t\t'):
            gpline = line.strip()
            gp = gpline.split('=')
            if debug:
                sys.stderr.write('{:25s} {:}\n'.format(gp[0], gp[1]))
            try:
                genparams[gp[0]] = float(gp[1])
            except:
                try:
                   genparams[gp[0]] = int(gp[1])
                except: 
                   genparams[gp[0]] = gp[1]
        
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
                
        if foundHdrs:
            if len(line) < 1:
                break
            f = line.split('\t')
            if len(f) < len(ival):
                break # end of turbine lines
                
            #try:
            #    grossKWh = float(f[ivDict['Gross [kWh]']])
            #except:
            #    sys.stderr.write("Couldn't find 'Gross [kWh]' (field {:}) in line:\n  {:}\n".format(ivDict['Gross [kWh]'], line))
            #try:
            #    netKWh = float(f[ivDict['Net [kWh]']])
            #except:
            #    sys.stderr.write("Couldn't find 'Net [kWh]' (field {:}) in line:\n  {:}\n".format('Net [kWh]', line))
            #try:
            #    aEff = float(f[ivDict['Array Efficiency [%%]']])
            #except:
            #    sys.stderr.write("Couldn't find 'Array Efficiency [%%]' (field {:}) in line:\n  {:}\n".format('Array Efficiency [%%]', line))
            
            grossKWh = getValue(f, ivDict, 'Gross [kWh]', line)
            netKWh = getValue(f, ivDict, 'Net [kWh]', line)
            aEff = getValue(f, ivDict, 'Array Efficiency [%]', line)
            
            if grossKWh is None or grossKWh <= 0.0: # skip inactive turbines or those in deactivated layouts
                continue
                    
            aGross.append(grossKWh)
            aNet.append(netKWh)
            arrayKWh = 0.01*aEff*grossKWh
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
        sys.stderr.write( 'Gross {:.4f} GWh\n'.format(gross_aep) )
        sys.stderr.write( 'Array {:.4f} GWh\n'.format(array_aep) )
        sys.stderr.write( 'Net   {:.4f} GWh\n'.format(net_aep  ) )
        
        if (len(xTurb) > 0):
            sys.stderr.write('X range {:9.1f} to {:9.1f} m\n'.format(np.min(xTurb), np.max(xTurb)))
            sys.stderr.write('Y range {:9.1f} to {:9.1f} m\n'.format(np.min(yTurb), np.max(yTurb)))
    
        sys.stderr.write('\nEnd OpenWind::rdReport({:})\n\n'.format(rptpath))
    
    if nErrors > 0:
        sys.stderr.write('Found {:} errors while reading {:}\n'.format(nErrors, rptpath))
            
    return gross_aep, array_aep, net_aep, owTrbs   
           
# -------------------

def getValue(f, ivDict, vname, line):
    '''
    Get the floating-point value associated with 'vname'
      f = line.split()
    2015 04 08
    '''
    if not vname in ivDict:
        sys.stderr.write('\n*** ERROR: variable "{:}" not found in ivDict\n'.format(vname))
        return None
        
    ivd = ivDict[vname]
    try:
        value = float(f[ivd])
        return value
    except:
        sys.stderr.write("Couldn't find '{:}' (field {:}) in line:\n  {:}\n".format(vname, ivd, line))
    return None
    
# function rdOWTG replaced with getTurbParams in rwTurbXML.py : 2014 03 31
