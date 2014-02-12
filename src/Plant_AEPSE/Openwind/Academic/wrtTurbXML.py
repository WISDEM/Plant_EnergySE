# wrtTurbXML.py
# 2013 06 03
'''
   Write XML tree that conforms to the OpenWind TurbineType XML format
   G. Scott, NREL 2013 06 03
   
   USAGE:
    import wrtTurbXML
    turbtree = wrtTurbXML.getTurbTree(trbname, desc, power, thrust, hubht, rdiam, ...)
    turbXML = etree.tostring(turbtree, 
                             xml_declaration=True,
                             doctype='<!DOCTYPE {:}>'.format(trbname), 
                             pretty_print=True)
    ofh = open('myTurbine.owtg', 'w')
    ofh.write(turbXML)
    ofh.close()
   
'''

import sys, os
from lxml import etree

sys.path.append('D:/SystemsEngr/CostModels')
#sys.path.append('Y:/Wind/Public/Projects/Projects G-S/Systems Engineering/3 - SE Software and Modeling/wese-scratch/twister/models/csm')
#from csmTurb_old import *

nvel = 26
rho = [1.225]
thrst = [0.000, 0.000, 0.000, 0.878, 0.880, 0.881, 0.881, 0.882, 0.882, 0.843,  
     0.764, 0.544, 0.390, 0.297, 0.235, 0.190, 0.156, 0.131, 
     0.111, 0.096, 0.083, 0.073, 0.064, 0.057, 0.051, 0.046 ]
pwr = [0,0,0,50,100,150,300,1000,1500,2000,2500,
       3000, 3000, 3000, 3000, 3000, 
       3000, 3000, 3000, 3000, 3000, 
       3000, 3000, 3000, 3000, 3000, 
       ]
rpm = [i for i in range(nvel)]
hh = 100
rdiam = 126.0
ttlCost = 2000000
fndCost =  100000

global pmult
pmult = 1.0

#---------------------------------------------------

def main():
    
    global pmult
    for i in range(1,len(sys.argv)):
        if (sys.argv[i].startswith('-pmult')):
            pmult = float(sys.argv[1][6:])
    
    percosts = []
    #percosts.append(PerCost(compname='Drive Train', cost=300000, pyrs=7))
    #percosts.append(PerCost(compname='Blades', cost=200000, pyrs=15))
    
    trbname = "OWTestTurb"
    desc = 'OpenWind Test Turbine'
    power = pwr
    thrust = thrst
    hubht = hh
    rdiam = rdiam
    
    # generate tree structure and convert to XML string
    
    turbtree = getTurbTree(trbname, desc, power, thrust, hubht, rdiam, percosts)
    turbXML = etree.tostring(turbtree, 
                             xml_declaration=True,
                             doctype='<!DOCTYPE {:}>'.format(trbname), 
                             pretty_print=True)

    
    # save to file
    
    owtgFile = 'testTurbine.owtg'
    ofh = open(owtgFile, 'w')
    ofh.write(turbXML)
    ofh.close()
    
#---------------------------------------------------

def getTurbTree(trbname, desc,
      power, thrust, hubht, rdiam, percosts=[],
      cutInWS=3.0, cutOutWS=25.0, nblades=3, machineRating=3000.0,
      ttlCost=2000000, fndCost=100000):
    '''
       trbname : short one-word turbine name
       desc : turbine description string
       power[] : turbine power output in kW at 1.0 mps intervals, starting with 0.0 mps
       thrust[] : turbine thrust coefficient at 1.0 mps intervals, starting with 0.0 mps
       hubht :
       rdiam :
       percosts : array of PerCost objects representing periodic costs
       
    '''
        
    turbtree = etree.Element(trbname)

    # Need to set these to actual values
    
    tname = etree.SubElement(turbtree, "Name")
    tname.text = desc
    #tname.text = 'OpenWind Test Turbine'
    
    hh = etree.SubElement(turbtree, "HubHeight",               value='{:.0f}'.format(hubht))
    rd = etree.SubElement(turbtree, "RotorDiameter",           value='{:.0f}'.format(rdiam))
    
    vv = etree.SubElement(turbtree, "VoltageV",                value='690')
    xx = etree.SubElement(turbtree, "CapacityKW",              value='{:.0f}'.format(machineRating))
    
    xx = etree.SubElement(turbtree, "IsPitchControlled",       value="1")
    xx = etree.SubElement(turbtree, "LowCutIn",                value='{:.0f}'.format(cutInWS)) # "3")
    xx = etree.SubElement(turbtree, "HighCutOut",              value='{:.0f}'.format(cutOutWS)) # "25")
    xx = etree.SubElement(turbtree, "IEC_adjustment",          value="0")
    xx = etree.SubElement(turbtree, "NumBlades",               value='{:d}'.format(nblades)) # "3")
    xx = etree.SubElement(turbtree, "LowTemperatureShutDown",  value="-30")
    xx = etree.SubElement(turbtree, "HighTemperatureShutDown", value="45")
    xx = etree.SubElement(turbtree, "LowTemperatureUnits",     value="0")
    xx = etree.SubElement(turbtree, "HighTemperatureUnits",    value="0")
    xx = etree.SubElement(turbtree, "LowTemperatureRestart",   value="-20")
    xx = etree.SubElement(turbtree, "HighTemperatureRestart",  value="30")
    xx = etree.SubElement(turbtree, "IsVariableSpeed",         value="1")
    xx = etree.SubElement(turbtree, "TiltAngleDegrees",        value="5")
    xx = etree.SubElement(turbtree, "PeakOutputKW",            value='{:.0f}'.format(machineRating) ) #"3000")
    xx = etree.SubElement(turbtree, "SpeedClass",              value="1")
    xx = etree.SubElement(turbtree, "TiClass",                 value="1")
    xx = etree.SubElement(turbtree, "SpeedMax",                value="10")
    xx = etree.SubElement(turbtree, "TiMax",                   value="14")
    
    xx = etree.SubElement(turbtree, "Comments")
    xx.text = 'This is not a warrantied power curve.'
   
    # Tables - Power, Thrust, RPM
    
    ptbls = etree.SubElement(turbtree, "Power_Tables")
    ptc = etree.SubElement(ptbls, "Count", value='1')
        
    ptbls.append( makeTable("Power_Table0", rho, power) )

    turbtree.append( makeTable("Thrust_Table", rho, thrust) )
    
    turbtree.append( makeTable("RPM_Table", rho, rpm) )
    
    # Costs
    
    tc = etree.SubElement(turbtree, "TotalCost", value='{:d}'.format(ttlCost))
    fc = etree.SubElement(turbtree, "FoundationCost", value='{:d}'.format(fndCost))

	# PeriodicCosts 

    if len(percosts) > 0:
        pcst = etree.SubElement(turbtree, "PeriodicCosts")
        pc = etree.SubElement(pcst, "Count", value='{:d}'.format(len(percosts))) 
        for ipc in range(len(percosts)):
            pcst.append( percosts[ipc].makeXML(ipc) )
    
    # noise

    hz = [31, 63,125,250,500,1000,2000,4000,8000, 16000]
    nhz = [0,0,0,0,0,0,0,0,0,0]
    addNoiseRows(turbtree, 100, 100, hz, nhz)

    return turbtree

#---------------------------------------------------

class PerCost:
    ''' class for OpenWind Periodic Costs '''
    
    def __init__(self, compname='None', cost=0, pyrs=0, cvbl=0, pvbl=0, isvp=0, isvc=0, cexp=1, pexp=1, cfct=1, pfct=1):
        self.compname = compname
        self.cost = cost
        self.pyrs = pyrs
        self.cvbl = cvbl
        self.pvbl = pvbl
        self.isvp = isvp
        self.isvc = isvc
        self.cexp = cexp
        self.pexp = pexp
        self.cfct = cfct
        self.pfct = pfct
        
    #---------------

    def makeXML(self,ipc):
        ''' returns an xml element '''
        pc = etree.Element('PeriodicCost{:d}'.format(ipc))
        pcv = etree.SubElement(pc, 'Type')
        pcv.text = 'PeriodicCost'
        pcv = etree.SubElement(pc, 'Component')
        pcv.text = self.compname
        
        pcv = etree.SubElement(pc, 'Cost',             value='{:d}'.format(self.cost))
        pcv = etree.SubElement(pc, 'PeriodYears',      value='{:d}'.format(self.pyrs))
        pcv = etree.SubElement(pc, 'CostVariable',     value='{:d}'.format(self.cvbl))
        pcv = etree.SubElement(pc, 'PeriodVariable',   value='{:d}'.format(self.pvbl))
        pcv = etree.SubElement(pc, 'IsVariablePeriod', value='{:d}'.format(self.isvp))
        pcv = etree.SubElement(pc, 'IsVariableCost',   value='{:d}'.format(self.isvc))
        pcv = etree.SubElement(pc, 'CostExponent',     value='{:d}'.format(self.cexp))
        pcv = etree.SubElement(pc, 'PeriodExponent',   value='{:d}'.format(self.pexp))
        pcv = etree.SubElement(pc, 'CostFactor',       value='{:d}'.format(self.cfct))
        pcv = etree.SubElement(pc, 'PeriodFactor',     value='{:d}'.format(self.pfct))

        return pc
            
#---------------------------------------------------

def makeTblRows(parent, x, xname, cr):
    ''' adds rows to parent '''
    
    vc = etree.SubElement(parent, cr, value='{:d}'.format(len(x)))
    for i in range(len(x)):
        vi = etree.SubElement(parent, '{:}{:}'.format(xname,i), value='{:.3f}'.format(x[i]))

#---------------------------------------------------

def addNoiseRows(parent, ttl, tnl, hz, nhz):
    ''' adds noise rows to parent '''

    nr = etree.SubElement(parent, 'TonalNoise', value='{:.0f}'.format(tnl))
    
    for i in range(len(hz)):
        vi = etree.SubElement(parent, 'Noise{:.0f}hz'.format(hz[i]), value='{:.0f}'.format(nhz[i]))

#---------------------------------------------------

def makeTable(tblName, rho, y):
    ''' 
      Make XML table 'tblName'
      
      rho is an array of air densities
        - tables with multiple densities NOT YET IMPLEMENTED
      y : table values - should have as many columns as rho has values
      
      returns tbl, which should be appended to the appropriate element 
    '''

    tbl = etree.Element(tblName)
    
    ttype = etree.SubElement(tbl, "Type")
    ttype.text = 'TurbineTable'
    timin = etree.SubElement(tbl, "TI_min", value='0')
    timax = etree.SubElement(tbl, "TI_max", value='60')
    
    # x - velocities
    
    vels = etree.SubElement(tbl, "Velocities")
    makeTblRows(vels, range(nvel), 'Velocity', 'Count')
    
    # air densities
    
    rhos = etree.SubElement(tbl, "AirDensities")
    rc = etree.SubElement(rhos, "Count", value='{:}'.format(len(rho)))
    for i in range(len(rho)):
        rc = etree.SubElement(rhos, 'Rho{:}'.format(i), value='{:.3f}'.format(rho[i]))
    
    if len(rho) > 1:
        sys.stderr.write("\n*** WARNING - found {:} values of rho (air-density)\n".format(len(rho)))
        sys.stderr.write("   Currently, only one value is allowed. y-vector will be duplicated for all rho values\n")
        sys.stderr.write("   writeTurbXML.py::makeTable({:},,)\n\n".format(tblName))
        
    # y - values
    
    vals = etree.SubElement(tbl, "Values")
    rc = etree.SubElement(vals, "Columns", value='{:}'.format(len(rho)))
    for i in range(len(rho)):
        #rc = etree.SubElement(vals, 'Rho{:}'.format(i), value='{:.6f}'.format(rho[i]))
        rv = etree.SubElement(vals, 'Rho{:.6f}'.format(rho[i]))
        makeTblRows(rv, y, 'v{:}-'.format(i), 'Rows')
        
    return tbl
    
#---------------------------------------------------

if __name__ == "__main__":

    main()

'''
OLD:
    Uses following variables from csmTurbine::turb:
      hub_height
      rotor.diam
      machineRating
      cutInWS
      cutOutWS
      rotor.nblades
#---------------------------------------------------

def makePerCost(parent, ipc, xname):
    # adds periodic cost to parent 
    #NOT USED - see class PerCost
    #
    
    pc = etree.SubElement(parent, 'PeriodicCost{:d}'.format(ipc))
    pcv = etree.SubElement(pc, 'Type')
    pcv.text = 'PeriodicCost'
    pcv = etree.SubElement(pc, 'Component')
    pcv.text = xname
    
    # Need to set these to actual values
    
    pcv = etree.SubElement(pc, 'Cost',             value="300000")
    pcv = etree.SubElement(pc, 'PeriodYears',      value="7")
    pcv = etree.SubElement(pc, 'CostVariable',     value="0")
    pcv = etree.SubElement(pc, 'PeriodVariable',   value="0")
    pcv = etree.SubElement(pc, 'IsVariablePeriod', value="0")
    pcv = etree.SubElement(pc, 'IsVariableCost',   value="0")
    pcv = etree.SubElement(pc, 'CostExponent',     value="1")
    pcv = etree.SubElement(pc, 'PeriodExponent',   value="1")
    pcv = etree.SubElement(pc, 'CostFactor',       value="1")
    pcv = etree.SubElement(pc, 'PeriodFactor',     value="1")
    
    # for scaling powers (testing only!)
    global pmult
    if (pmult > 0):
        for i in range(len(pwr)):
            pwr[i] *= pmult 
'''
