# openWindAcExtCode.py
# 2014 04 03
'''
  Execute OpenWindAcademic as a component using OpenMDAO's ExternalCode
  Based on example from http://openmdao.org/docs/plugin-guide/filewrapper_plugin.html
  
  2014 04 03: based on openWindExtCode.py
  
  NOTE: Script file must contain an Optimize/Optimise operation - otherwise,
    no results will be found.
  
  2014 04 10: openwindAC doesn't work well as an ExternalCode because of its
    notify files - we need to have OW running in background
    See openWindAcComponent.py for a solution
'''

import os.path

import sys
#sys.path.append('C:/Python27/openmdao-0.7.0/twister/models/AEP/')
import openWindUtils as utils
import owAcademicUtils as acutils
import rwScriptXML

from openmdao.lib.datatypes.api import Float, Int
from openmdao.lib.components.api import ExternalCode
from openmdao.main.api import FileMetadata

from openmdao.util.filewrap import InputFileGenerator, FileParser

#-----------------------------------------------------------------

class OWACwrapped(ExternalCode):
    """ A simple OpenMDAO code wrapper for OpenWind academic

        Args:
           owExe (str): full path to OpenWind executable
           scriptFile (str): path to XML script that OpenWind will run

     """

    rotor_diameter   = Float(126.0, iotype='in', units='m', desc='connecting rotor diameter to force run on change') # todo: hack for now
    availability     = Float(0.95,  iotype='in', desc='availability')
    other_losses     = Float(0.0,   iotype='in', desc='soiling losses')
    
    dummyVbl         = Float(0,   iotype='in',  desc='unused variable to make it easy to do DOE runs')

    array_efficiency = Float(0.0, iotype='out', desc='Array Efficiency')
    gross_aep        = Float(0.0, iotype='out', desc='Gross Output')
    net_aep          = Float(0.0, iotype='out', desc='Net Output')
    array_losses     = Float(0.0, iotype='out', desc='Array losses')
    nTurbs           = Int(0,     iotype='out', desc='Number of turbines')
    array_aep        = Float(0.0, iotype='out', desc='Array output - NOT USED IN ACADEMIC VERSION')
    
    #------------------ 
    
    def __init__(self, owExe, scriptFile=None, debug=False):
        """ Constructor for the OWACwrapped component """

        super(OWACwrapped, self).__init__()

        # External Code public variables
        
        self.input_file = 'myinput.txt'
        self.output_file = 'myoutput.txt'
        self.stderr = 'myerror.log'
        
        self.debug = debug
        
        self.script_file = 'script_file.xml' # replace with actual file name
        if scriptFile is not None:
            self.script_file = scriptFile

        # external_files : member of Component class = list of FileMetadata objects
        self.external_files = [
            FileMetadata(path=self.output_file),
            FileMetadata(path=self.stderr),
        ]
        
        # Set the version of OpenWind that we want to use
        
        #self.command = [owExeUnofficial, self.script_file]
        self.command = [owExe, self.script_file]
        self.command = [owExe, self.script_file, '&']  # run in background?

    #------------------ 
    
    def execute(self):
        """ Executes our file-wrapped component. """

        sys.stderr.write("  In {0}.execute() {1}...\n".format(self.__class__, self.script_file))

        # Prepare input file here
        #   - write a new script file?
        #   - write a new turbine file to overwrite the one referenced
        #       in the existing script_file?

        # Execute the component
        
        self.command[1] = self.script_file
        super(OWACwrapped, self).execute()
        if self.debug:
            sys.stderr.write('Started openWindAcExtCode: dummyVbl {:} returnCode {:}\n'.format(self.dummyVbl,self.return_code))

        # Watch for 'results.txt', meaning that OW has run once with the default locations 
    
        if self.debug:
            sys.stderr.write('OpenWind waiting for results.txt\n')
        acutils.waitForNotify(watchFile='results.txt', debug=False, callback=self.getCBvalue)

        # Now OWac is waiting for a new position file
        # Write new postions and notify file - this time it should use updated positions
        
        if self.debug:
            sys.stderr.write('Writing position file\n')
        acutils.writePositionFile(wt_positions)
        if self.debug:
            sys.stderr.write('Writing notify file\n')
        acutils.writeNotify() # tell OW that we're ready for the next (only) iteration
        
        acutils.waitForNotify(watchFile='results.txt', debug=False, callback=self.getCBvalue)

        # Parse output file 
        #    Enterprise OW writes the report file specified in the script BUT
        #    Academic OW writes 'results.txt' (which doesn't have as much information)
        
        netEnergy, netNRGturb, grossNRGturb = utils.parseACresults()
        self.nTurbs = len(netNRGturb)
        self.net_aep = netEnergy
        self.gross_aep = sum(grossNRGturb)
        if self.debug:
            sys.stderr.write('{:}\n'.format(self.dump))
        
        # Set the output variables
        self.array_efficiency = self.array_aep / self.gross_aep        
        self.array_losses = 1 - (self.array_aep/self.gross_aep)
    
    def dump(self):
        # returns a string with a summary of object parameters
        dumpstr = ''
        dumpstr += 'Gross {:10.4f} GWh Net {:10.4f} GWh from {:4d} turbines'.format(
        self.gross_aep*0.000001,self.net_aep*0.000001, self.nTurbs)
        return dumpstr
        
    def getCBvalue(self,val):
        ''' Callback invoked when waitForNotify detects change in results file
            Sets global vbl 'cbVal' to its argument
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
    
    ow = OWACwrapped(owExe = owname)
    ow.script_file = owXMLname
    
    ow.execute() # run the openWind process
    
    print ow.dump()
