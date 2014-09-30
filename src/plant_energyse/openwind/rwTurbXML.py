# rwTurbXML.py
# 2014 03 28
# Read and write turbine XML (*.owtg) files
#   - created by merging rdTurbXML.py and wrtTurbXML.py

'''
   Read/write XML tree that conforms to the OpenWind TurbineType XML format
   G. Scott, NREL 2013 07 09
   2014 03 24: updated documentation
   
   USAGE (reading):
     import rwTurbXML
     fname = 'turbfile.owtg'
     tree = rwTurbXML.parseOWTG(fname)
     vels, pwrs = rwTurbXML.getPwrTbls(tree)
     vels, thrusts = rwTurbXML.getThrustTbls(tree)
     vels, rpms = rwTurbXML.getRPMTbls(tree)
    
   USAGE (writing):
     import rwTurbXML
     turbtree = rwTurbXML.newTurbTree(trbname, desc,
         vels, power, thrust, rpm, hubht, rdiam, rho=[1.225], percosts=[],
         cutInWS=3.0, cutOutWS=25.0, nblades=3, machineRating=3000.0,
         ttlCost=2000000, fndCost=100000):
     turbXML = etree.tostring(turbtree, 
                              xml_declaration=True,
                              doctype='<!DOCTYPE {:}>'.format(trbname), 
                              pretty_print=True)
     ofh = open('myTurbine.owtg', 'w')
     ofh.write(turbXML)
     ofh.close()
   
   USAGE (modifying):
     modTurbXML(oldTurbFile, newTurbFile, rotor_diameter=rdiam)
     
'''

#-------------------------------------------------------

import sys, os
from lxml import etree
import matplotlib.pyplot as plt

# ----------- READING -----------------

#---------------------------------------------------------

def parseOWTG(fname,debug=False):
    # parse an OpenWind XML turbine file and return the etree
    
    try:
        tree = etree.parse(fname)
        return tree
    except:
        sys.stderr.write('\n*** ERROR in parseOWTG() opening/reading/parsing file {:}\n\n'.format(fname))
        return None
    
#---------------------------------------------------------

def getTurbParams(tree,debug=False):
    
    name = ''
    capKW = 0
    hubHt = 0
    rtrDiam = 0
    
    root = tree.getroot()
    name = root.find('Name').text
    try:
        hubHt = float(root.find('HubHeight').get('value'))
    except:
        sys.stderr.write("getTurbParams: HubHeight not found\n")
        
    try:
        capKW = float(root.find('CapacityKW').get('value'))
    except:
        sys.stderr.write("getTurbParams: HubHeight not found\n")
        
    try:
        rtrDiam = float(root.find('RotorDiameter').get('value'))
    except:
        sys.stderr.write("getTurbParams: HubHeight not found\n")
    
    return name, capKW, hubHt, rtrDiam
     
#---------------------------------------------------------

def getTbls(tree,tblname,debug=False):
    ''' extract and return tables from turbine XML structure 
        Table must have <Type>TurbineTable</Type>
        getTbls is usually called from getPwrTbls(), getThrustTbls(), getRPMTbls()
    '''
    
    vels = []
    pwrs = []

    # parse Velocities section
    
    vel = tree.xpath('/'.join([tblname,'Velocities']))[0]
    vcnt = int(tree.xpath('/'.join([tblname,'Velocities/Count']))[0].attrib['value'])
    
    ivel = 0
    vels = []
    for child in vel:
        ctg = child.tag
        if ctg.startswith('Count'):
            nvel = int(child.attrib['value'])
            vels = [None for ii in range(nvel)]
        if ctg.startswith('Velocity'):
            vels[ivel] = float(child.attrib['value'])
            if debug:
                print '{:12s} {:5.1f}'.format(child.tag, vels[ivel] )
            ivel += 1
    
    # parse AirDensities section
    
    adens = tree.xpath('/'.join([tblname,'AirDensities']))[0]
    nrho = int(tree.xpath('/'.join([tblname,'AirDensities/Count']))[0].attrib['value'])
    if debug:
        print 'Found {:} air densities'.format(nrho)
    
    # parse Values section
    
    ipwr = 0
    pwrs = []
    vals = tree.xpath('/'.join([tblname,'Values']))[0]
    for child in vals:
        ctg = child.tag
        if ctg.startswith('Rho'):
            rho = float(ctg[3:])
            if debug:
                print 'Rho {:5.3f}'.format(rho)
            for rchld in child:
                rctg = rchld.tag
                if rctg.startswith('Rows'):
                    npwr = int(rchld.attrib['value'])
                    pwrs = [None for ii in range(npwr)]
                if rctg.startswith('v'):
                    pwrs[ipwr] = float(rchld.attrib['value'])
                    if debug:
                        print '{:12s} {:5.1f}'.format(rctg, pwrs[ipwr] )
                    ipwr += 1
    
    return vels, pwrs
    
#---------------------------------------------------------

def getPwrTbls(tree,debug=False):
    ''' extract and return power tables from turbine XML structure '''
    
    ptbls = '//Power_Tables' 
    for record in tree.xpath(ptbls):
        cnts = record.xpath('/'.join([ptbls,'Count']))
        ntbl = int(cnts[0].attrib['value'])
        if debug:
            sys.stderr.write('Found {:} {:} tables\n'.format(ntbl, ptbls))
        
        for itbl in range(ntbl):
            tname = 'Power_Table{:}'.format(itbl)
            vels, pwrs = getTbls(record,tname,debug=debug)
                   
    return vels, pwrs

#---------------------------------------------------------

def getThrustTbls(tree,debug=False):
    ''' extract and return thrust table from turbine XML structure '''
    
    ttbls = '//Thrust_Table' 
    vels, tsts = getTbls(tree,ttbls,debug=debug)           
    return vels, tsts
    
#---------------------------------------------------------

def getRPMTbls(tree,debug=False):
    ''' extract and return RPM table from turbine XML structure '''
    
    rtbls = '//RPM_Table' 
    vels, rpms = getTbls(tree,rtbls,debug=debug)           
    return vels, rpms
    
# ----------- WRITING -----------------

#---------------------------------------------------

def newTurbTree(trbname, desc,
      vels, power, thrust, rpm, hubht, rdiam, rho=[1.225], percosts=[],
      cutInWS=3.0, cutOutWS=25.0, nblades=3, machineRating=3000.0,
      ttlCost=2000000, fndCost=100000):
    '''
       trbname : short one-word turbine name
       desc : turbine description string
       vels[] : wind speeds in mps at 1.0 mps intervals, starting with 0.0 mps
       power[] : turbine power output in kW at 1.0 mps intervals, starting with 0.0 mps
       thrust[] : turbine thrust coefficient at 1.0 mps intervals, starting with 0.0 mps
       rpm[] : turbine rpm at 1.0 mps intervals, starting with 0.0 mps
       hubht : turbine hub height in m
       rdiam : turbine rotor diameter in m
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
        
    ptbls.append( makeTable("Power_Table0", vels, rho, power) )

    turbtree.append( makeTable("Thrust_Table", vels, rho, thrust) )
    
    turbtree.append( makeTable("RPM_Table", vels, rho, rpm) )
    
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
    
    hz = [63,125,250,500,1000,2000,4000,8000]
    nhz = [0,0,0,0,0,0,0,0]
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
        ''' returns a tree representing a PerCost (periodic cost) item '''
        
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
    ''' adds rows to parent
        parent : an element or tree
        x      : an array of values
        xname  : name of variable
        cr     : name of element?? 
    '''
    
    vc = etree.SubElement(parent, cr, value='{:d}'.format(len(x)))
    for i in range(len(x)):
        vi = etree.SubElement(parent, '{:}{:}'.format(xname,i), value='{:.3f}'.format(x[i]))

#---------------------------------------------------

def addNoiseRows(parent, ttl, tnl, hz, nhz):
    ''' adds noise rows to parent '''
    
    nr = etree.SubElement(parent, 'TotalNoise', value='{:.0f}'.format(ttl))
    #nr = etree.SubElement(parent, 'TonalNoise', value='{:.0f}'.format(tnl))
    #  2014 03 24 : tonal commented out - where/why is it needed?
    
    for i in range(len(hz)):
        vi = etree.SubElement(parent, 'Noise{:.0f}hz'.format(hz[i]), value='{:.0f}'.format(nhz[i]))

#---------------------------------------------------

def makeTable(tblName, vels, rho, y):
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
    
    velocities = etree.SubElement(tbl, "Velocities")
    makeTblRows(velocities, vels, 'Velocity', 'Count')
    
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
        rv = etree.SubElement(vals, 'Rho{:.6f}'.format(rho[i]))
        makeTblRows(rv, y, 'v{:}-'.format(i), 'Rows')
        
    return tbl

# ----------- MODIFYING -----------------

def modTurbXML(oldTurbFile, newTurbFile, rotor_diameter=None):
    ''' read contents of a turbine OWTG file,
        modify some parameters,
        write new OWTG file '''
    
    turbtree = parseOWTG(oldTurbFile)
    trbname = turbtree.getroot().tag
    
    if rotor_diameter is not None:
        turbtree.find('RotorDiameter').set('value', '{:.2f}'.format(rotor_diameter))
    
    # ... modify other params here
    
    # write new OWTG file
    
    turbXML = etree.tostring(turbtree, 
                             xml_declaration=True,
                             doctype='<!DOCTYPE {:}>'.format(trbname), 
                             pretty_print=True)
    ofh = open(newTurbFile, 'w')
    ofh.write(turbXML)
    ofh.close()
    
# ----------- TESTING -----------------

def main():
    # main() only for testing module
    
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
    vels = [float(i) for i in range(nvel)]
    
    hh = 100
    rdiam = 126.0
    ttlCost = 2000000
    fndCost =  100000

    percosts = []
    #percosts.append(PerCost(compname='Drive Train', cost=300000, pyrs=7))
    #percosts.append(PerCost(compname='Blades', cost=200000, pyrs=15))
    
    trbname = "OWTestTurb"
    desc = 'OpenWind Test Turbine'
    power = pwr
    thrust = thrst
    hubht = hh
    rtrdiam = rdiam
    
    # generate tree structure and convert to XML string
    
    turbtree = newTurbTree(trbname, desc, vels, power, thrust, rpm, hubht, rtrdiam, rho, percosts)
    turbXML = etree.tostring(turbtree, 
                             xml_declaration=True,
                             doctype='<!DOCTYPE {:}>'.format(trbname), 
                             pretty_print=True)

    
    # --- save to file
    
    owtgFile = 'testTurbine.owtg'
    ofh = open(owtgFile, 'w')
    ofh.write(turbXML)
    ofh.close()
    sys.stderr.write('Wrote turbine file {:}\n'.format(owtgFile))
    
    # --- read back file and check values
    
    tree = parseOWTG(owtgFile)
    root = tree.getroot()
    print tree
    rdiamOut = float(root.find('RotorDiameter').get('value'))
    print 'RotorDiam: IN {:.1f} OUT {:.1f}'.format(rdiam, rdiamOut)
    
    ptable = root.find('.//Power_Table0')
    vels = ptable.find('.//Velocities')
    ws = []
    for v in vels:
        #print v.tag, v.get('value')
        if v.tag.startswith('Velocity'):
            ws.append(float(v.get('value')))
            
    vels = ptable.find('.//Velocities')
    tpwr = []    
    #tree.xpath('/'.join([tblname,'Velocities']))[0]
    
    ws, tpwr = getPwrTbls(root)
    for i in range(len(ws)):
        print '{:4.1f} {:7.1f}'.format(ws[i], tpwr[i])
    
    name, capKW, hubHt, rtrDiam = getTurbParams(tree)
    print '{:} {:} {:} {:} '.format(name, capKW, hubHt, rtrDiam)
     
if __name__ == "__main__":

    main()
