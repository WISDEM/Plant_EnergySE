# openWindExtCode.py
# 2013 06 25
'''
  Execute OpenWind as a component using OpenMDAO's ExternalCode
  Based on example from http://openmdao.org/docs/plugin-guide/filewrapper_plugin.html 
'''

import os.path
import sys

import plant_energyse.openwind.openWindUtils as utils
from plant_energyse.openwind.rwScriptXML import rdScript

from openmdao.lib.datatypes.api import Float, Int
from openmdao.lib.components.api import ExternalCode
from openmdao.main.api import FileMetadata

from openmdao.util.filewrap import InputFileGenerator, FileParser

#-----------------------------------------------------------------

class OWwrapped(ExternalCode):
    """ A simple OpenMDAO code wrapper for OpenWind

        Args:
           owExe (str): full path to OpenWind executable
           scriptFile (str): path to XML script that OpenWind will run
    """

    #rotor_diameter = Float(126.0, iotype='in', units='m', desc='connecting rotor diameter to force run on change') # todo: hack for now
    availability = Float(0.95, iotype='in', desc='availability')
    other_losses = Float(0.0, iotype='in', desc='soiling losses')
    
    dummyVbl       = Float(0, iotype='in', desc='unused variable to make it easy to do DOE runs')

    array_efficiency    = Float(0.0, iotype='out', desc='Array Efficiency')
    gross_aep = Float(0.0, iotype='out', desc='Gross Output')
    net_aep   = Float(0.0, iotype='out', desc='Net Output')
    array_aep = Float(0.0, iotype='out', desc='Array Output')
    array_losses = Float(0.0, iotype='out', desc='Array losses')
    turbine_number = Int(0, iotype='out', desc='Number of turbines')
    
    #------------------ 
    
    def __init__(self, owExe, scriptFile=None, debug=False):
        """ Constructor for the OWwrapped component """

        super(OWwrapped, self).__init__()

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
            #FileMetadata(path=self.input_file, input=True),
            FileMetadata(path=self.output_file),
            FileMetadata(path=self.stderr),
        ]

        self.command = [owExe, self.script_file]
    
    def execute(self):
        """ Executes our file-wrapped component. """

        if self.debug:
            sys.stderr.write("  In {0}.execute()...\n".format(self.__class__))

        # Prepare input file here
        #   - write a new script file?
        #   - write a new turbine file to overwrite the one referenced
        #       in the existing script_file?

        # Execute the component
        self.command[1] = self.script_file
        super(OWwrapped, self).execute()
        
        if self.debug:
            sys.stderr.write('Ran openWindExtCode: dummyVbl {:} returnCode {:}\n'.format(self.dummyVbl,self.return_code))

        # Parse output file
        dscr = rdScript(self.command[1], debug=self.debug) # get output file name from script
        rptpath = dscr['rptpath']
        
        self.gross_aep, self.array_aep, self.net_aep, owTurbs = utils.rdReport(rptpath, debug=self.debug) 
        self.turbine_number = len(owTurbs)
        
        # Set the output variables
        self.array_efficiency = self.array_aep / self.gross_aep        
        self.gross_aep = self.gross_aep * 1000000.0 # gWh to kWh
        self.array_aep = self.array_aep * 1000000.0
        self.net_aep   = self.net_aep   * 1000000.0

        # find net aep (not using openwind for these since they may be inputs from other models)
        self.net_aep = self.net_aep * self.availability * (1-self.other_losses)

        # find array efficiency
        self.array_losses = 1 - (self.array_aep/self.gross_aep)
    
    def dump(self):
        # returns a string with a summary of object parameters
        dumpstr = ''
        dumpstr += 'Gross {:10.4f} GWh Net {:10.4f} GWh from {:4d} turbines'.format(
            self.gross_aep*0.000001,self.net_aep*0.000001, self.turbine_number)
        return dumpstr

#------------------------------------------------------------------

def example(owExe):

    # only use when debugging
    debug = False
    for arg in sys.argv[1:]:
        if arg == '-debug':
            debug = True

    if not os.path.isfile(owExe):
        sys.stderr.write('OpenWind executable file "{:}" not found\n'.format(owExe))
        exit()

    owXMLname = '../templates/ecScript.xml'
    
    if not os.path.isfile(owXMLname):
        sys.stderr.write('OpenWind script file "{:}" not found\n'.format(owXMLname))
        exit()
    
    ow = OWwrapped(owExe, debug=debug)
    ow.script_file = owXMLname
    
    ow.run() # run the openWind process
    
    print ow.dump()

if __name__ == "__main__":

    # Substitue your own path to Openwind Enterprise
    owExe = 'C:/Models/Openwind/openWind64.exe'
    owExe = 'D:/rassess/Openwind/openWind64.exe'
    example(owExe)