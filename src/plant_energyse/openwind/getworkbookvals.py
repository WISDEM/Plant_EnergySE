# getworkbookvals.py
# 2014 04 10
# get values from an OpenWind workbook by running OW and parsing results

# getTurbPos(workbook, owexe, delFiles=True):
#   Get turbine positions from a *blb workbook file
#     by running an energy capture and parsing report

# getEC(workbook, owexe, delFiles=True):
#   Get base energy caputure from a *blb workbook file
#     by running an energy capture and parsing report

# Writes: gtpReport.txt, gtpScript.xml
# (should have option to delete after running)
# (should have more error checking)

import sys, os
import openWindUtils
import rwScriptXML
import subprocess

#-----------------------------------------

def getTurbPos(workbook, owexe, delFiles=True):
    '''
      Run openWind executable 'owexe' 
        - do an energy capture on 'workbook'
        - return xy[nturb][2] with coordinates of turbines
    '''
    
    rpath = 'gtpReport.txt'
    scriptname = 'gtpScript.xml'
    
    # Write script with: load workbook, energy capture, exit
    
    scripttree, ops = rwScriptXML.newScriptTree(rpath)
    scripttree.find('TurbineXField').set('value','true')
    scripttree.find('TurbineYField').set('value','true')
    
    scripttree.find('TurbineTypeField').set('value','true') # added 2014 09 29
    
    rwScriptXML.makeChWkbkOp(ops,workbook)       # change workbook
    rwScriptXML.makeEnCapOp(ops, wm = "DAWM Eddy-Viscosity" ) # energy capture
    rwScriptXML.makeExitOp(ops)                 # exit
    rwScriptXML.wrtScript(scripttree, scriptname, addCols=True)
    
    # Run openwind script
    
    retcode = subprocess.call([owexe, scriptname])
    
    # Parse output and return
    
    gross_aep, array_aep, net_aep, owTrbs = openWindUtils.rdReport(rpath)
    nturb = len(owTrbs)
    xy = [[0,0] for i in range(nturb)]
    for i in range(nturb):
        xy[i][0] = owTrbs[i].x
        xy[i][1] = owTrbs[i].y

    if delFiles:
        try:
            os.remove(scriptname)
            os.remove(rpath)
        except:
            sys.stderr.write('\nERROR *** could not delete {:} or {:}\n\n'.format(scriptname, rpath))
        
    return xy
#-----------------------------------------

def getEC(workbook, owexe, delFiles=True):
    # get default energy capture for a workbook
    
    rpath = 'gtpReport.txt'
    scriptname = 'gtpScript.xml'
    
    # Write script with: load workbook, energy capture, exit
    
    scripttree, ops = rwScriptXML.newScriptTree(rpath)
    rwScriptXML.makeChWkbkOp(ops,workbook)       # change workbook
    rwScriptXML.makeEnCapOp(ops, wm = "DAWM Eddy-Viscosity" ) # energy capture
    rwScriptXML.makeExitOp(ops)                 # exit
    rwScriptXML.wrtScript(scripttree, scriptname, addCols=True)
    
    # Run openwind script
    
    retcode = subprocess.call([owexe, scriptname])
    
    # Parse output and return
    
    gross_aep, array_aep, net_aep, owTrbs = openWindUtils.rdReport(rpath)
    
    if delFiles:
        try:
            os.remove(scriptname)
            os.remove(rpath)
        except:
            sys.stderr.write('\nERROR *** could not delete {:} or {:}\n\n'.format(scriptname, rpath))
        
    return gross_aep, array_aep, net_aep
          
if __name__ == "__main__":

    workbook = 'C:/SystemsEngr/Test/VA_test.blb'
    owexe = 'C:/rassess/OpenWind/Openwind64.exe'
    xy = getTurbPos(workbook, owexe)
    for i in range(len(xy)):
        print '{:2d} {:.1f} {:.1f}'.format(i, xy[i][0], xy[i][1])
        
    gross_aep, array_aep, net_aep = getEC(workbook, owexe)
    print 'Gross {:.4f} Net {:.4f}'.format(gross_aep, net_aep)
