# owcDOEAssy.py
# 2014 05 26
'''
  Test DOE FullFactorial with OpenWindAcademic component
  Analysis(Assembly) contains 3 components in workflow:
    WTPupdate - changes turbine positions
    WTLupdate - changes turbine types
    OWACcomp - runs OpenWind and reports net_aep
    
  Initial turbine positions are passed to wtpupdate::__init__()
    - read from (global) wt_positions
    - copied to wt_layout.wt_positions and NOT CHANGED
    - modified and copied to wt_layout_out.wt_positions
    
  Initial turbine types are read from Alstom 6MW OWTG file (hardcoded in wtpmodComponent.py)
    - copied (repeated) into wtpupdate.wt_layout.wt_list[]
    - could specify the OWTG file in __init__ call
     
'''

import sys, os

from openmdao.main.api import Assembly
from openmdao.lib.drivers.api import DOEdriver
from openmdao.lib.doegenerators.api import FullFactorial
from openmdao.lib.doegenerators.api import CSVFile
from openmdao.lib.casehandlers.api import ListCaseRecorder

from openWindAcComponent import OWACcomp  # OpenWind inside an OpenMDAO Component
#from wtpmodComponent import WTPMcomp, WTPupdate, WTLupdate
from wtlayoutComponents import WTPupdate, WTLupdate
from Plant_AEPSE.Openwind.findOW import findOW

from Plant_AEPSE.Openwind.rwScriptXML import rdScript

wt_positions = [[456000.00,4085000.00],
                [456500.00,4085000.00]]

owXMLname = '../../test/rtopScript.xml' # replace turbine and optimize
#owXMLname = '../../test/opScript.xml' # optimize only

global drvType
drvType = 'ff' # default is FullFactorial
        
#-------------------------------------------------------------------

class Analysis(Assembly):
    def configure(self):

        debug = True
        owexe = findOW(debug=debug, academic=True)

        # Create component instances
        
        wtp = WTPupdate(debug=debug, wt_positions=wt_positions)
        wtl = WTLupdate(debug=debug)
        owc = OWACcomp(owexe, scriptFile=owXMLname, debug=debug)
        
        self.add('wtpupdate', wtp) # update turbine positions
        
        self.add('wtlupdate', wtl) # update turbine types
        
        self.add('owc', owc) # run OpenWind Academic
        
        # Connect wt_layouts
        
        self.connect('wtpupdate.wt_layout_out', 'wtlupdate.wt_layout')
        self.connect('wtlupdate.wt_layout_out', 'owc.wt_layout')
        
        # Add driver and workflow
        
        self.add('driver', DOEdriver())
        
        if drvType == 'ff':
            self.driver.DOEgenerator = FullFactorial(num_levels=2)
            
            self.driver.add_parameter('wtpupdate.deltaX', low=0., high=20000.)
            self.driver.add_parameter('wtpupdate.deltaY', low=-10000., high=0.)
            self.driver.add_parameter('wtlupdate.pwrFactor', low=1.0, high=1.2)
        elif drvType == 'csv':
            # still being tested
            doefile = '../../test/citInput.csv'
            self.driver.DOEgenerator = CSVFile(doe_filename=doefile) #, num_parameters=3)
            self.driver.DOEgenerator.num_parameters = 3
            print self.driver.DOEgenerator
            print self.driver.DOEgenerator.num_parameters
            
        self.driver.case_outputs = ['owc.net_aep',]

        self.driver.recorders = [ListCaseRecorder(),]

        self.driver.workflow.add(['wtpupdate', 'wtlupdate', 'owc'])

    def execute(self):
        sys.stderr.write("  In {0}.execute()...\n".format(self.__class__))
        super(self.__class__, self).execute()

if __name__ == "__main__": # pragma: no cover         

    import time
    
    for i in range(1,len(sys.argv)):
        if sys.argv[i].startswith('-csv'):
            drvType = 'csv'
            
    scrdict = rdScript(owXMLname) #, debug=True)
    replturbpath = None
    if 'replturbpath' in scrdict:
        replturbpath = scrdict['replturbpath']
        print 'ReplTurbFile: {:}'.format(replturbpath)
    else:
        print 'No replaceTurb operation found'
    
    analysis = Analysis()

    if replturbpath is not None:
        analysis.wtlupdate.replturbpath = replturbpath

    tt = time.time()
    analysis.run() 
    
    print "Elapsed time: ", time.time()-tt, "seconds"
    
    # write the case output to the screen
    #  and to file
    
    ofname = 'caseOutput.txt'
    ofh = open(ofname,'w')
    ofh.write('   X        Y     EkWh\n')
    for c in analysis.driver.recorders[0].get_iterator():
        print "x: {:8.1f} y: {:8.1f} f: {:4.2f} z: {:8.1f}".format(c['wtpupdate.deltaX'],c['wtpupdate.deltaY'],c['wtlupdate.pwrFactor'],c['owc.net_aep'])
        ofh.write( "{:8.1f} {:8.1f} {:4.2f} {:8.4f}\n".format(c['wtpupdate.deltaX'],c['wtpupdate.deltaY'],c['wtlupdate.pwrFactor'],c['owc.net_aep']*0.000001))
    ofh.close()
