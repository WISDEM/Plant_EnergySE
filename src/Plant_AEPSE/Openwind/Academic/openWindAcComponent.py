# openWindAcComponent.py
# 2014 04 08
'''
  Execute OpenWindAcademic as an OpenMDAO Component
  
  NOTE: Script file must contain an Optimize/Optimise operation - otherwise,
    no results will be found.
  
'''

import os.path

import sys, time
import subprocess
from lxml import etree

import Plant_AEPSE.Openwind.openWindUtils as utils
import owAcademicUtils as acutils
import Plant_AEPSE.Openwind.rwScriptXML as rwScriptXML

from openmdao.lib.datatypes.api import Float, Int, VarTree
from openmdao.main.api import FileMetadata, Component, VariableTree

#from openmdao.util.filewrap import InputFileGenerator, FileParser

from fusedwind.plant_flow.fused_plant_vt import GenericWindTurbineVT, GenericWindTurbinePowerCurveVT, \
                           ExtendedWindTurbinePowerCurveVT, GenericWindFarmTurbineLayout

#-----------------------------------------------------------------

class OWACcomp(Component):
    """ A simple OpenMDAO component for OpenWind academic

        Args:
           owExe (str): full path to OpenWind executable
           scriptFile (str): path to XML script that OpenWind will run

     """

    # inputs
    
    rotor_diameter   = Float(126.0, iotype='in', units='m', desc='connecting rotor diameter to force run on change') # todo: hack for now
    availability     = Float(0.95,  iotype='in', desc='availability')
    other_losses     = Float(0.0,   iotype='in', desc='soiling losses')
    
    dummyVbl         = Float(0,   iotype='in',  desc='unused variable to make it easy to do DOE runs')
    
    wt_layout        = VarTree(GenericWindFarmTurbineLayout(), iotype='in', desc='properties for each wind turbine and layout')    

    # outputs
    
    gross_aep        = Float(0.0, iotype='out', desc='Gross Output')
    net_aep          = Float(0.0, iotype='out', desc='Net Output')
    nTurbs           = Int(0,     iotype='out', desc='Number of turbines')
    #array_aep        = Float(0.0, iotype='out', desc='Array output - NOT USED IN ACADEMIC VERSION')
    #array_efficiency = Float(0.0, iotype='out', desc='Array Efficiency')
    #array_losses     = Float(0.0, iotype='out', desc='Array losses')
    
    #------------------ 
    
    def __init__(self, owExe, scriptFile=None, debug=False, stopOW=True, start_once=False):
        """ Constructor for the OWACwrapped component """

        super(OWACcomp, self).__init__()

        # public variables
        
        self.input_file = 'myinput.txt'
        self.output_file = 'myoutput.txt'
        self.stderr = 'myerror.log'
        
        # external_files : member of Component class = list of FileMetadata objects
        self.external_files = [
            FileMetadata(path=self.output_file),
            FileMetadata(path=self.stderr),
        ]
        
        self.debug = debug
        self.stopOW = stopOW
        self.start_once = start_once
        
        self.script_file = 'script_file.xml' # replace with actual file name
        if scriptFile is not None:
            self.script_file = scriptFile

            # Check script file for validity and extract some path information
        
            scriptOK = self.parse_scriptFile()
        
        # Set the version of OpenWind that we want to use
        
        self.command = [owExe, self.script_file]
        
        # Try starting OpenWind here (if self.start_once is True)
        
        if self.start_once:
            self.proc = subprocess.Popen(self.command)
            self.pid = self.proc.pid
            if self.debug:
                sys.stderr.write('Started OpenWind with pid {:}\n'.format(self.pid))
                sys.stderr.write('  OWACComp: dummyVbl {:}\n'.format(self.dummyVbl))
        
    #------------------ 
    
    def parse_scriptFile(self):

        # OWac looks for the notify files and writes the 'results.txt' file to the 
        #   directory that contains the *blb workbook file
        # find where the results file will be found     
        
        try:
            e = etree.parse(self.script_file)
            self.rptpath = e.getroot().find('ReportPath').get('value')
        except:
            sys.stderr.write("Can't find ReportPath in {:}\n".format(self.script_file))
            self.rptpath = 'NotFound'
        
        # Make sure there's an optimize operation - otherwise OWAC won't find anything
        
        foundOpt = False
        ops = e.getroot().findall('.//Operation')
        for op in ops:
            optype = op.find('Type').get('value')
            if optype == 'Optimize' or optype == 'Optimise':
                foundOpt = True
                break
        if not foundOpt:
            sys.stderr.write('\n*** ERROR: no Optimize operation found in {:}\n\n'.format(self.script_file))
            return False
            
        # Find the workbook folder and save as dname
        
        self.dname = None
        for op in ops:
            if op.find('Type').get('value') == 'Change Workbook':
                wkbk = op.find('Path').get('value')
                self.dname = os.path.dirname(wkbk)
                if self.debug:
                    sys.stderr.write('Working directory: {:}\n'.format(self.dname))
                break
                
        #self.dname = os.path.dirname(self.script_file)
        #self.resname = os.path.join(self.dname,'results.txt')
        self.resname = '/'.join([self.dname,'results.txt'])
        
        return True
        
    #------------------ 
    
    def execute(self):
        """ Executes our component. """

        if self.debug:
            sys.stderr.write("  In {0}.execute() {1}...\n".format(self.__class__, self.script_file))

        # Prepare input file here
        #   - write a new script file?
        #   - write a new turbine file to overwrite the one referenced
        #       in the existing script_file?

        # Execute the component and save process ID
        
        #self.command[1] = self.script_file
        if not self.start_once:
            self.proc = subprocess.Popen(self.command)
            self.pid = self.proc.pid
            if self.debug:
                sys.stderr.write('Started OpenWind with pid {:}\n'.format(self.pid))
                sys.stderr.write('  OWACComp: dummyVbl {:}\n'.format(self.dummyVbl))
                #sys.stderr.write('Report Path: {:}\n'.format(self.rptpath))

            # Watch for 'results.txt', meaning that OW has run once with the default locations 
            
            if self.debug:
                sys.stderr.write('OWACComp waiting for {:} (first run -  positions unchanged\n'.format(self.resname))
            acutils.waitForNotify(watchFile=self.resname, path=self.dname, debug=False, callback=self.getCBvalue)

        # Now OWac is waiting for a new position file
        # Write new postions and notify file - this time it should use updated positions

        #if self.debug:
        #    sys.stderr.write('Writing position file\n')
        #acutils.writePositionFile(self.wt_positions, path=self.dname, debug=self.debug)
        #if self.debug:
        #    sys.stderr.write('wt_p: {:} shape {:}\n'.format(self.wt_layout.wt_positions.__class__, 
        #                  self.wt_layout.wt_positions.shape))
        acutils.writePositionFile(self.wt_layout.wt_positions, path=self.dname, debug=self.debug)
        
        # see if results.txt is there already
        
        if os.path.exists(self.resname):
            resmtime = os.path.getmtime(self.resname)
            if self.debug:
                sys.stderr.write('ModTime({:}): {:}\n'.format(self.resname, time.asctime(time.localtime(resmtime))))
        else:
            if self.debug:
                sys.stderr.write('{:} does not exist yet\n'.format(self.resname))
            
        acutils.writeNotify(path=self.dname, debug=self.debug) # tell OW that we're ready for the next (only) iteration
        
        # 'results.txt' is in the same directory as the *blb file
        
        if os.path.exists(self.resname):
            resNewmtime = os.path.getmtime(self.resname)
            if resNewmtime > resmtime: # file has changed
                if self.debug:
                    sys.stderr.write('results.txt already updated')
            else:
                acutils.waitForNotify(watchFile=self.resname, path=self.dname, callback=self.getCBvalue, debug=self.debug)
        else:
            if self.debug:
                sys.stderr.write('OWACComp waiting for {:} (modified positions)\n'.format(self.resname))
            acutils.waitForNotify(watchFile=self.resname, path=self.dname, callback=self.getCBvalue, debug=self.debug)

        # Parse output file 
        #    Enterprise OW writes the report file specified in the script BUT
        #    Academic OW writes 'results.txt' (which doesn't have as much information)
        
        netEnergy, netNRGturb, grossNRGturb = acutils.parseACresults(fname=self.resname)
        if netEnergy is None:
            sys.stderr.write("Error reading results file\n")
            if self.debug:
                sys.stderr.write('Stopping OpenWind with pid {:}\n'.format(self.pid))
            self.proc.terminate()
            return
            
        # Set the output variables
        #   - array_aep is not available from Academic 'results.txt' file
        
        self.nTurbs = len(netNRGturb)
        self.net_aep = netEnergy
        self.gross_aep = sum(grossNRGturb)
        if self.debug:
            sys.stderr.write('{:}\n'.format(self.dump()))
        
        if not self.start_once and self.stopOW:
            if self.debug:
                sys.stderr.write('Stopping OpenWind with pid {:}\n'.format(self.pid))
            self.proc.terminate()
    
    #------------------ 
    
    def dump(self):
        # returns a string with a summary of object parameters
        dumpstr = ''
        dumpstr += 'Gross {:10.4f} GWh Net {:10.4f} GWh from {:4d} turbines'.format(
            self.gross_aep*0.000001,self.net_aep*0.000001, self.nTurbs)
        #print dumpstr
        return dumpstr
        
    #------------------ 
    
    def getCBvalue(self,val):
        ''' Callback invoked when waitForNotify detects change in results file
            Sets self.net_aep to its argument
            waitForNotify has handler which reads results.txt and calls this 
              function with netEnergy 
            Is this redundant with other parser for results.txt?
        '''
        self.net_aep = val

#------------------------------------------------------------------

if __name__ == "__main__":

    debug = False
    start_once = False
    for arg in sys.argv[1:]:
        if arg == '-debug':
            debug = True
        if arg == '-once':
            start_once = True
            
    #owexe = 'C:/rassess/Openwind/OpenWind64_ac.exe'
    from Plant_AEPSE.Openwind.findOW import findOW
    owexe = findOW(debug=debug, academic=True)
    if not os.path.isfile(owexe):
        sys.stderr.write('OpenWind executable file "{:}" not found\n'.format(owexe))
        exit()

    #owXMLname = 'C:/Python27/openmdao-0.7.0/twister/models/AEP/testOWScript1.xml'
    #owXMLname = 'C:/Python27/openmdao-0.7.0/twister/models/AEP/VA_ECap.xml'
    #owXMLname = 'C:/SystemsEngr/Plant_AEPSE_GNS/src/Plant_AEPSE/Openwind/Academic/testOWScript.xml'
    #owXMLname = 'C:/SystemsEngr/Plant_AEPSE_GNS/src/Plant_AEPSE/Openwind/Academic/testOWACScript.xml'
    
    owXMLname = '../../test/rtecScript.xml' # replace turb, energy capture
    owXMLname = '../../test/owacScript.xml' # optimize operation
    
    if not os.path.isfile(owXMLname):
        sys.stderr.write('OpenWind script file "{:}" not found\n'.format(owXMLname))
        exit()
    
    rwScriptXML.rdScript(owXMLname,debug=debug) # Show our operations
    
    #ow = OWACcomp(owExe=owexe, debug=debug) #, stopOW=False)
    #ow.script_file = owXMLname
    ow = OWACcomp(owExe=owexe, debug=debug, scriptFile=owXMLname, start_once=start_once)
    
    wt_positions = [[456000.00,4085000.00],
                    [456500.00,4085000.00]]
    
    # move turbines farther offshore with each iteration
    
    for irun in range(1,4):
        for i in range(len(wt_positions)):
            wt_positions[i][0] += 3000.
            wt_positions[i][1] -= 2000.
        ow.wt_layout.wt_positions = wt_positions
        
        ow.execute() # run the openWind process
        
        print '\nFinal values'
        owd = ow.dump()
        print '  {:}'.format(owd)
        print '-' * 40, '\n'
                    