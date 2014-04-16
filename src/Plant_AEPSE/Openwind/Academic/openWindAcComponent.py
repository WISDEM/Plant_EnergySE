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

import openWindUtils as utils
import owAcademicUtils as acutils
import rwScriptXML

from openmdao.lib.datatypes.api import Float, Int, VarTree
from openmdao.main.api import FileMetadata, Component, VariableTree

#from openmdao.util.filewrap import InputFileGenerator, FileParser

from fused_plant_vt import GenericWindTurbineVT, GenericWindTurbinePowerCurveVT, \
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
    
    array_efficiency = Float(0.0, iotype='out', desc='Array Efficiency')
    gross_aep        = Float(0.0, iotype='out', desc='Gross Output')
    net_aep          = Float(0.0, iotype='out', desc='Net Output')
    array_losses     = Float(0.0, iotype='out', desc='Array losses')
    nTurbs           = Int(0,     iotype='out', desc='Number of turbines')
    array_aep        = Float(0.0, iotype='out', desc='Array output - NOT USED IN ACADEMIC VERSION')
    
    #------------------ 
    
    def __init__(self, owExe, scriptFile=None, debug=False, stopOW=True):
        """ Constructor for the OWACwrapped component """

        super(OWACcomp, self).__init__()

        # public variables
        
        self.input_file = 'myinput.txt'
        self.output_file = 'myoutput.txt'
        self.stderr = 'myerror.log'
        
        self.debug = debug
        self.stopOW = stopOW
        
        self.script_file = 'script_file.xml' # replace with actual file name
        if scriptFile is not None:
            self.script_file = scriptFile

        # external_files : member of Component class = list of FileMetadata objects
        self.external_files = [
            FileMetadata(path=self.output_file),
            FileMetadata(path=self.stderr),
        ]
        
        # Set the version of OpenWind that we want to use
        
        self.command = [owExe, self.script_file]
        
        #self.wt_positions = []

    #------------------ 
    
    def execute(self):
        """ Executes our component. """

        sys.stderr.write("  In {0}.execute() {1}...\n".format(self.__class__, self.script_file))

        # Prepare input file here
        #   - write a new script file?
        #   - write a new turbine file to overwrite the one referenced
        #       in the existing script_file?

        # find where the results file will be found
        # (Will results.txt be in that folder, or in the script folder?)
        
        try:
            e = etree.parse(self.script_file)
            rptpath = e.getroot().find('ReportPath').get('value')
        except:
            sys.stderr.write("Can't find ReportPath in {:}\n".format(self.script_file))
            rptpath = 'NotFound'
        
        # OWac looks for the notify files and writes the 'results.txt' file to the directory that contains:
        #   the *blb workbook file
        
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
            return
            
        # Find the workbook folder and save as dname
        
        dname = None
        for op in ops:
            if op.find('Type').get('value') == 'Change Workbook':
                wkbk = op.find('Path').get('value')
                dname = os.path.dirname(wkbk)
                if self.debug:
                    sys.stderr.write('Working directory: {:}\n'.format(dname))
                break
                
        #dname = os.path.dirname(self.script_file)
        #resname = os.path.join(dname,'results.txt')
        resname = '/'.join([dname,'results.txt'])
        
        # Execute the component and save process ID
        
        self.command[1] = self.script_file
        proc = subprocess.Popen(self.command)
        pid = proc.pid
        if self.debug:
            sys.stderr.write('Started OpenWind with pid {:}\n'.format(pid))
            sys.stderr.write('  OWACComp: dummyVbl {:}\n'.format(self.dummyVbl))
            #sys.stderr.write('Report Path: {:}\n'.format(rptpath))

        # Watch for 'results.txt', meaning that OW has run once with the default locations 
    
        if self.debug:
            sys.stderr.write('OWACComp waiting for {:} (first run -  positions unchanged\n'.format(resname))
        acutils.waitForNotify(watchFile=resname, path=dname, debug=False, callback=self.getCBvalue)

        # Now OWac is waiting for a new position file
        # Write new postions and notify file - this time it should use updated positions

        #if self.debug:
        #    sys.stderr.write('Writing position file\n')
        #acutils.writePositionFile(self.wt_positions, path=dname, debug=self.debug)
        acutils.writePositionFile(self.wt_layout.wt_positions, path=dname, debug=self.debug)
        
        # see if results.txt is there already
        
        if os.path.exists(resname):
            resmtime = os.path.getmtime(resname)
            sys.stderr.write('ModTime({:}): {:}\n'.format(resname, time.asctime(time.localtime(resmtime))))
        else:
            sys.stderr.write('{:} does not exist yet\n'.format(resname))
            
        acutils.writeNotify(path=dname, debug=self.debug) # tell OW that we're ready for the next (only) iteration
        
        # 'results.txt' is in the same directory as the *blb file
        
        if os.path.exists(resname):
            resNewmtime = os.path.getmtime(resname)
            if resNewmtime > resmtime: # file has changed
                sys.stderr.write('results.txt already updated')
            else:
                acutils.waitForNotify(watchFile=resname, path=dname, callback=self.getCBvalue, debug=self.debug)
        else:
            if self.debug:
                sys.stderr.write('OWACComp waiting for {:} (modified positions)\n'.format(resname))
            acutils.waitForNotify(watchFile=resname, path=dname, callback=self.getCBvalue, debug=self.debug)

        # Parse output file 
        #    Enterprise OW writes the report file specified in the script BUT
        #    Academic OW writes 'results.txt' (which doesn't have as much information)
        
        netEnergy, netNRGturb, grossNRGturb = acutils.parseACresults(fname=resname)
        if netEnergy is None:
            sys.stderr.write("Error reading results file\n")
            if self.debug:
                sys.stderr.write('Stopping OpenWind with pid {:}\n'.format(pid))
            proc.terminate()
            return
            
        self.nTurbs = len(netNRGturb)
        self.net_aep = netEnergy
        self.gross_aep = sum(grossNRGturb)
        if self.debug:
            sys.stderr.write('{:}\n'.format(self.dump()))
        
        # Set the output variables
        self.array_efficiency = self.array_aep / self.gross_aep        
        self.array_losses = 1 - (self.array_aep/self.gross_aep)
        
        #if self.debug:
        #    sys.stderr.write('Gross {:.1f} Net {:.1f}\n'.format(self.gross_aep, self.net_aep))
        
        if self.stopOW:
            if self.debug:
                sys.stderr.write('Stopping OpenWind with pid {:}\n'.format(pid))
            proc.terminate()
    
    def dump(self):
        # returns a string with a summary of object parameters
        dumpstr = ''
        dumpstr += 'Gross {:10.4f} GWh Net {:10.4f} GWh from {:4d} turbines'.format(
            self.gross_aep*0.000001,self.net_aep*0.000001, self.nTurbs)
        #print dumpstr
        return dumpstr
        
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

    owname = 'C:/rassess/Openwind/OpenWind64_ac.exe'
    if not os.path.isfile(owname):
        sys.stderr.write('OpenWind executable file "{:}" not found\n'.format(owname))
        exit()

    #owXMLname = 'C:/Python27/openmdao-0.7.0/twister/models/AEP/testOWScript1.xml'
    #owXMLname = 'C:/Python27/openmdao-0.7.0/twister/models/AEP/VA_ECap.xml'
    owXMLname = 'C:/SystemsEngr/Plant_AEPSE_GNS/src/Plant_AEPSE/Openwind/Academic/testOWScript.xml'
    owXMLname = 'C:/SystemsEngr/Plant_AEPSE_GNS/src/Plant_AEPSE/Openwind/Academic/testOWACScript.xml'
    
    owXMLname = 'C:/SystemsEngr/test/rtecScript.xml' # replace turb, energy capture
    owXMLname = 'C:/SystemsEngr/test/owacScript.xml' # optimize operation
    
    if not os.path.isfile(owXMLname):
        sys.stderr.write('OpenWind script file "{:}" not found\n'.format(owXMLname))
        exit()
    
    rwScriptXML.rdScript(owXMLname,debug=True) # Show our operations
    
    ow = OWACcomp(owExe=owname, debug=True) #, stopOW=False)
    ow.script_file = owXMLname
    
    wt_positions = [[456000.00,4085000.00],
                    [456500.00,4085000.00]]
    
    # move turbines farther offshore with each iteration
    
    for irun in range(1,4):
        for i in range(len(wt_positions)):
            wt_positions[i][0] += 3000.
            wt_positions[i][1] -= 2000.
        #ow.wt_positions = wt_positions
        ow.wt_layout.wt_positions = wt_positions
        
        ow.execute() # run the openWind process
        
        print '\nFinal values'
        owd = ow.dump()
        print '  {:}'.format(owd)
        print '-' * 40, '\n'
                    