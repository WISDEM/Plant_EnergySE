# rwScriptXML.py
# 2013 06 21
'''
   Write/read XML tree that conforms to the OpenWind OpenWindScript XML format
   G. Scott, NREL 2013 06 21
   
   2013 06 26: added rdScript(), converted it to lxml
   2014 03 28: getScriptTree() renamed to newScriptTree()
   2014 03 30: name changed from 'wrtScriptXML.py' to 'rwScriptXML.py'
   2014 07 16: added 'Iterations' to Optimize operation
   2014 09 23: added some error checking
   2014 10 01: rdScript return dictionary now includes operations
   2014 11 03: added makeRepTurbPos() for replace turbine positions operation
   
   USAGE:
    import rwScriptXML
    scripttree, ops = rwScriptXML.newScriptTree(rpath)
    rwScriptXML.makeChWkbkOp(ops,blbpath)       # change workbook
    rwScriptXML.makeRepTurbOp(ops,tname,tpath) # replace turbine
    rwScriptXML.makeRepTurbPos(ops,sname,tppath) # replace turbine positions
    rwScriptXML.makeEnCapOp(ops, wm = "DAWM Eddy-Viscosity" ) # energy capture
    rwScriptXML.makeOptimiseOp(ops [,nIter=NN]) # optimize for energy
    rwScriptXML.makeOptimizeOp(ops [,nIter=NN]) # alternate spelling
    rwScriptXML.makeOptCostEnergyOp(ops) # optimize for cost
    
    ... (other operations when they are added)
    rwScriptXML.makeExitOp(ops)                 # exit
    
    scriptXML = etree.tostring(scripttree, 
                               xml_declaration=True, 
                               doctype='<!DOCTYPE OpenWindScript>',
                               pretty_print=True)
    
    ofh = open('myScriptFile.xml', 'w')
    ofh.write(scriptXML)
    ofh.close()
   
   TO CHANGE A VALUE:
   
    aop = scripttree.find("AppendOperations")
    if aop is not None:
        aop.set('value','Sideways')
        
    allops = scripttree.find("AllOperations")
    for aop in allops: # should all be operations
        atype = aop.find('Type')
        if atype.get('value') == 'Change Workbook':
            apath = aop.find('Path')
            apath.set('value',newWorkbookName)
'''

import sys, os
from lxml import etree
from datetime import datetime
    
#---------------------------------------------------
#-------------- READING OPERATIONS --------------

def parseScript(fname, debug=False):
    ''' parse an OpenWind XML script file and return etree '''
    if debug:
        sys.stderr.write('\nparseScript(): reading {:}\n'.format(fname))
    if not os.path.exists(fname):
        sys.stderr.write('\n*** ERROR in parseScript(): file {:} not found\n'.format(fname))
        raise IOError
            
    e = etree.parse(fname)
    return e    
     
#---------------------------------------------------

def rdScript(fname, debug=False):
    ''' read an OpenWind XML script file and extract useful info 
        if debug, lists all operations found in script
        returns a dictionary that may include the following keys:
          rptpath
          workbook
          turbname
          replturbname
          replturbpath
          repltpsite
          repltpospath
          operations
    '''
    
    dscript = {} # dictionary to return
    
    e = parseScript(fname)
    
    if debug:
        sys.stderr.write('\nrdScript: {:}\n'.format(fname))
    dscript = {} # dictionary to return
    
    e = parseScript(fname)
    root = e.getroot()
    
    # Get ReportPath so we know where to look for results
    
    for atype in e.findall('ReportPath'):
        rptpath = atype.get('value').replace('\\','/')
        dscript['rptpath'] = rptpath
        if debug:
            sys.stderr.write('  ReportPath: {:}\n'.format(rptpath))        

    nop = 0
    if debug:
        sys.stderr.write('  Operations:\n')
    dscript['operations'] = []
    for aotype in e.findall('AllOperations'):
        for atype in aotype.findall('Operation'):
            nop += 1
            arg = ''
            optype = atype.find('Type').get('value')
            dscript['operations'].append(optype)
            if optype == "Change Workbook":
                wkbk = atype.find('Path').get('value')
                dscript['workbook'] = wkbk
                arg = wkbk
            if optype == "Replace Turbine Type":
                tname = atype.find('TurbineName').get('value')
                tpath = atype.find('TurbinePath').get('value')
                dscript['replturbname'] = tname
                dscript['replturbpath'] = tpath
                arg = tname + ' --> ' + tpath
            if optype == "Replace Turbine Positions":
                sname = atype.find('SiteName').get('value')
                tppath = atype.find('TurbinePosPath').get('value')
                dscript['repltpsite'] = sname
                dscript['repltpospath'] = tppath
                arg = sname + ' --> ' + tppath
            if optype == "Optimise":
                nopt = atype.find('Iterations').get('value')
                if nopt is not None:
                    arg = nopt
            if optype == "Optimize":
                sys.stderr.write("\n*** WARNING: OpenWind prefers 'Optimise' to 'Optimize\n")
                sys.stderr.write('  Please rename your operation\n\n')
            if debug:
                sys.stderr.write('    Operation {:}: {:} {:}\n'.format(nop, optype, arg))        
    if debug:
        sys.stderr.write('\n')
       
    return dscript
        
#-------------- WRITING OPERATIONS --------------

def newScriptTree(rpath):
    '''
    Creates a basic OpenWind script - operations are added later
      rpath   : string containing full path to report file
      
    Returns 
      scripttree : elementTree for script - call etree.tostring(scripttree,...) to get XML string
      ops : operations tree - an element within scripttree with ID "AllOperations"
        call make???Op(ops,...) to add operations
    '''
        
    writeXY = 'false'
    
    scripttree = etree.Element("OpenWindScript")

    scripttree.append(etree.Comment(' Written by rwScriptXML.py on {:} '.format(str(datetime.now()))))
    
    # Need to set these to actual values
    
    rpath = etree.SubElement(scripttree, "ReportPath", value=rpath)
    
    #se = etree.SubElement(scripttree, 'AppendOperations',     value="Sideways")
    se = etree.SubElement(scripttree, 'AppendOperations',     value="After")
    se = etree.SubElement(scripttree, 'SiteNameField',        value="true")
    se = etree.SubElement(scripttree, 'TurbineTypeField',     value="false")
    se = etree.SubElement(scripttree, 'TurbineLabelField',    value="false")
    se = etree.SubElement(scripttree, 'TurbineIndexField',    value="true")
    se = etree.SubElement(scripttree, 'TurbineXField',        value=writeXY)
    se = etree.SubElement(scripttree, 'TurbineYField',        value=writeXY)
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

def makeRepTurbPos(parent,sname,tppath):
    ''' adds 'Replace Turbine Position' operation to parent '''

    op = etree.SubElement(parent, 'Operation')
    opv = etree.SubElement(op, 'Type', value='Replace Turbine Positions')
    opv = etree.SubElement(op, 'SiteName',  value=sname)
    opv = etree.SubElement(op, 'TurbinePosPath',  value=tppath)

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

def makeOptimiseOp(parent, nIter=None):
    ''' adds 'Optimise' operation to parent '''
    
    op = etree.SubElement(parent, 'Operation')
    opv = etree.SubElement(op, 'Type', value='Optimise')
    
    if nIter is not None:
        opv = etree.SubElement(op, 'Iterations', value='{:}'.format(nIter))

def makeOptimizeOp(parent, nIter=None):
    ''' adds 'Optimise' operation to parent - convenience function with American spelling '''
    
    makeOptimiseOp(parent, nIter=nIter)
    #op = etree.SubElement(parent, 'Operation')
    #opv = etree.SubElement(op, 'Type', value='Optimise')
    
#---------------------------------------------------

def makeOptCostEnergyOp(parent):
    ''' adds 'Optimise Energy' operation to parent '''
    
    op = etree.SubElement(parent, 'Operation')
    opv = etree.SubElement(op, 'Type', value='OCOE')

#---------------------------------------------------

def makeExitOp(parent):
    ''' adds Exit operation to parent '''
    
    op = etree.SubElement(parent, 'Operation')
    opv = etree.SubElement(op, 'Type', value='Exit')

#---------------------------------------------------

def makeEnableOp(parent, siteName, enable=True):
    ''' adds Site Properties operation to parent 
          siteName should be the name of an existing site layer
          default is to enable site and add to optimizer
    '''
    
    enVal = '1'
    if not enable:
        enVal = '0'
        
    op = etree.SubElement(parent, 'Operation')
    opv = etree.SubElement(op, 'Type', value='Site Properties')
    opv = etree.SubElement(op, 'SiteName', value=siteName)
    opv = etree.SubElement(op, 'Enable', value=enVal)
    opv = etree.SubElement(op, 'Fixed', value="1")
    opv = etree.SubElement(op, 'Grow', value="0")
    opv = etree.SubElement(op, 'IncludeInOptimiser', value=enVal)
    opv = etree.SubElement(op, 'SetTurbineType', value="0")
    #opv = etree.SubElement(op, 'TurbineType', value="&lt;none&gt;")
    opv = etree.SubElement(op, 'TurbineType', value="&amp;lt;none&amp;gt;")

#---------------------------------------------------

def wrtScript(scripttree, ofname, addCols=False):
    # Save scripttree to file in XML format
    
    scriptXML = etree.tostring(scripttree, 
                               xml_declaration=True, 
                               doctype='<!DOCTYPE OpenWindScript>',
                               pretty_print=True)
    
    if addCols:
        # OpenWind seems to have a problem with indentation
        # This option adds a couple of blank columns to lines that already
        #   start with a blank. This seems to help.
        
        newXML = scriptXML.replace('\n ', '\n   ')
        scriptXML = newXML
        
    ofh = open(ofname, 'w')
    ofh.write(scriptXML)
    ofh.close()

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
    
    scripttree, ops = newScriptTree(rpath)
    
    # add operations to 'ops' (the 'AllOperations' tree in scripttree)
    
    makeChWkbkOp(ops,blbpath)       # change workbook
    makeRepTurbOp(ops,tname,tpath)  # replace turbine
    makeEnCapOp(ops)                # run energy capture
    
    makeOptimizeOp(ops, nIter=40)   # optimize operation with 40 iterations
    
    makeExitOp(ops)                 # exit
    
    # Save script to file
    
    scriptFile = 'testOWScript.xml'
    wrtScript(scripttree, scriptFile, addCols=True)
    
    
    # Read it back
    
    dscript = rdScript(scriptFile, debug=True)
    for k in (dscript.keys()):
        print k, dscript[k]
        
    #rptpath = ['rptpath']
    #print 'Report path: {:}'.format(rptpath)
    
#---------------------------------------------------

if __name__ == "__main__":

    main()
