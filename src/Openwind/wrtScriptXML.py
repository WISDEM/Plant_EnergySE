# wrtScriptXML.py
# 2013 06 21
'''
   Write/read XML tree that conforms to the OpenWind OpenWindScript XML format
   G. Scott, NREL 2013 06 21
   
   2013 06 26: added rdScript(), converted it to lxml
   
   USAGE:
    import wrtScriptXML
    scripttree, ops = wrtScriptXML.getScriptTree(rpath)
    wrtScriptXML.makeChWkbkOp(ops,blbpath)       # change workbook
    ... (other operations)
    wrtScriptXML.makeExitOp(ops)                 # exit
    
    scriptXML = etree.tostring(scripttree, 
                               xml_declaration=True, 
                               doctype='<!DOCTYPE OpenWindScript>',
                               pretty_print=True)
    
    ofh = open('myScriptFile.xml', 'w')
    ofh.write(scriptXML)
    ofh.close()
   
'''

import sys, os
from lxml import etree
from datetime import datetime
    
#---------------------------------------------------

def getScriptTree(rpath):
    '''
    Creates a basic OpenWind script - operations are added later
      rpath   : string containing full path to report file
      
    Returns 
      scripttree : elementTree for script - call etree.tostring(scripttree,...) to get XML string
      ops : operations tree - call make???Op(ops,...) to add operations
    '''
        
    global pmult
    scripttree = etree.Element("OpenWindScript")

    scripttree.append(etree.Comment(' Written by wrtScriptXML.py on {:} '.format(str(datetime.now()))))
    
    # Need to set these to actual values
    
    rpath = etree.SubElement(scripttree, "ReportPath", value=rpath)
    
    se = etree.SubElement(scripttree, 'AppendOperations',     value="Sideways")
    se = etree.SubElement(scripttree, 'SiteNameField',        value="true")
    se = etree.SubElement(scripttree, 'TurbineTypeField',     value="false")
    se = etree.SubElement(scripttree, 'TurbineLabelField',    value="false")
    se = etree.SubElement(scripttree, 'TurbineIndexField',    value="true")
    se = etree.SubElement(scripttree, 'TurbineXField',        value="false")
    se = etree.SubElement(scripttree, 'TurbineYField',        value="false")
    se = etree.SubElement(scripttree, 'GrossEnergyField',     value="true")
    se = etree.SubElement(scripttree, 'NetEnergyField',       value="true")
    se = etree.SubElement(scripttree, 'ArrayEfficiencyField', value="true")
    se = etree.SubElement(scripttree, 'FreeWindspeedField',   value="true")
    se = etree.SubElement(scripttree, 'MeanWindspeedField',   value="true")
    se = etree.SubElement(scripttree, 'TurbulenceTotalField', value="true")
    se = etree.SubElement(scripttree, 'TI15',                 value="true")
    
    ops = etree.SubElement(scripttree, "AllOperations")

    return scripttree, ops
    
#---------------------------------------------------

def makeChWkbkOp(parent,blbpath):
    ''' adds 'Change Workbook' operation to parent '''
    
    op = etree.SubElement(parent, 'Operation')
    opv = etree.SubElement(op, 'Type', value='Change Workbook')
    opv = etree.SubElement(op, 'Path',  value=blbpath)

#---------------------------------------------------

def makeRepTurbOp(parent,tname,tpath):
    ''' adds 'Replace Turbine Type' operation to parent '''
    
    op = etree.SubElement(parent, 'Operation')
    opv = etree.SubElement(op, 'Type', value='Replace Turbine Type')
    opv = etree.SubElement(op, 'TurbineName',  value=tname)
    opv = etree.SubElement(op, 'TurbinePath',  value=tpath)

#---------------------------------------------------

def makeEnCapOp(parent, wm = "DAWM Eddy-Viscosity" ):
    ''' adds 'Energy Capture' operation to parent '''
    
    op = etree.SubElement(parent, 'Operation')
    opv = etree.SubElement(op, 'Type', value='Energy Capture')

    umin,umax,ustep = 0.0, 70.0, 1.0
    tdir,fdir,ldir = 72.0, 0.0, 71.0
    doff = 0.0
    pxx = 50.0
    
    opv = etree.SubElement(op, 'WakeModel', value=wm)
    opv = etree.SubElement(op, 'Umin',      value='{:.1f}'.format(umin))
    opv = etree.SubElement(op, 'Umax',      value='{:.1f}'.format(umax))
    opv = etree.SubElement(op, 'Ustep',     value='{:.1f}'.format(ustep))
    opv = etree.SubElement(op, 'TotalDirections', value='{:.1f}'.format(tdir))
    opv = etree.SubElement(op, 'FirstDirection',  value='{:.1f}'.format(fdir))
    opv = etree.SubElement(op, 'LastDirection',   value='{:.1f}'.format(ldir))
    opv = etree.SubElement(op, 'DirectionOffset', value='{:.1f}'.format(doff))
    opv = etree.SubElement(op, 'Pxx',             value='{:.1f}'.format(pxx))

#---------------------------------------------------

def makeExitOp(parent):
    ''' adds Exit operation to parent '''
    
    op = etree.SubElement(parent, 'Operation')
    opv = etree.SubElement(op, 'Type', value='Exit')

#---------------------------------------------------
#---------------------------------------------------

def rdScript(fname, debug=False):
    ''' read an OpenWind XML script file and extract useful info 
        Also lists all operations found in script
    '''
    
    #e = ET.parse(fname)
    e = etree.parse(fname)
    if debug:
        sys.stderr.write('\nrdScript: {:}\n'.format(fname))
    root = e.getroot()
    for child in root:
        print child.tag
    
    # Get ReportPath so we know where to look for results
    
    for atype in e.findall('ReportPath'):
        rptpath = atype.get('value').replace('\\','/')
        if debug:
            sys.stderr.write('  ReportPath: {:}\n'.format(rptpath))        

    nop = 0
    if debug:
        sys.stderr.write('  Operations:\n')
    for aotype in e.findall('AllOperations'):
        for atype in aotype.findall('Operation'):
            nop += 1
            optype = atype.find('Type').get('value') 
            if debug:
                sys.stderr.write('    Operation {:}: {:}\n'.format(nop, optype))        
    if debug:
        sys.stderr.write('\n')
       
    return rptpath
        
#---------------------------------------------------

def main():
    '''
      blbpath : string containing full path to workbook file 
      tname   : string containing name of turbine to replace
      tpath   : string containing full path to new turbine *OWTG file
    '''
    
    rpath = 'D:/Path/File'
    blbpath = 'D:/Path/Workbook.blb'
    tname = 'Enercon 44'
    tpath = 'D:/Path/To/newturbine.owtg'
    
    scripttree, ops = getScriptTree(rpath)
    
    # add operations to 'ops' (the 'AllOperations' tree in scripttree)
    
    makeChWkbkOp(ops,blbpath)       # change workbook
    makeRepTurbOp(ops,tname,tpath)  # replace turbine
    makeEnCapOp(ops)                # run energy capture
    makeExitOp(ops)                 # exit
    
    # export script as text string
    
    scriptXML = etree.tostring(scripttree, 
                               xml_declaration=True, 
                               doctype='<!DOCTYPE OpenWindScript>',
                               pretty_print=True)
    
    #print scriptXML
    
    # Save script to file
    
    scriptFile = 'testOWScript.xml'
    ofh = open(scriptFile, 'w')
    ofh.write(scriptXML)
    ofh.close()
    
    # Read it back
    
    rptpath = rdScript(scriptFile, debug=True)
    #print 'Report path: {:}'.format(rptpath)
    
#---------------------------------------------------

if __name__ == "__main__":

    main()
