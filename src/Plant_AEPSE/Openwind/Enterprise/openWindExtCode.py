# openWindExtCode.py
# 2013 06 25
'''
  Execute OpenWind as a component using OpenMDAO's ExternalCode
  Based on example from http://openmdao.org/docs/plugin-guide/filewrapper_plugin.html
  
  2014 03 26: GNS revisions
  
'''

import os.path

import sys
#sys.path.append('C:/Python27/openmdao-0.7.0/twister/models/AEP/')
import openWindUtils as utils
import rwScriptXML

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

    rotor_diameter = Float(126.0, iotype='in', units='m', desc='connecting rotor diameter to force run on change') # todo: hack for now
    availability = Float(0.95, iotype='in', desc='availability')
    other_losses = Float(0.0, iotype='in', desc='soiling losses')
    
    dummyVbl       = Float(0, iotype='in', desc='unused variable to make it easy to do DOE runs')

    array_efficiency    = Float(0.0, iotype='out', desc='Array Efficiency')
    gross_aep = Float(0.0, iotype='out', desc='Gross Output')
    net_aep   = Float(0.0, iotype='out', desc='Net Output')
    array_aep = Float(0.0, iotype='out', desc='Array Output')
    array_losses = Float(0.0, iotype='out', desc='Array losses')
    nTurbs = Int(0, iotype='out', desc='Number of turbines')
    
    #------------------ 
    
    def __init__(self, owExe, scriptFile=None):
        """ Constructor for the OWwrapped component """

        super(OWwrapped, self).__init__()

        # External Code public variables
        
        self.input_file = 'myinput.txt'
        self.output_file = 'myoutput.txt'
        self.stderr = 'myerror.log'
        
        self.script_file = 'script_file.xml' # replace with actual file name
        if scriptFile is not None:
            self.script_file = scriptFile

        # external_files : member of Component class = list of FileMetadata objects
        self.external_files = [
            #FileMetadata(path=self.input_file, input=True),
            FileMetadata(path=self.output_file),
            FileMetadata(path=self.stderr),
        ]
        
        # Set the version of OpenWind that we want to use
        
        #self.command = [owExeUnofficial, self.script_file]
        self.command = [owExe, self.script_file]

    #------------------ 
    
    def execute(self):
        """ Executes our file-wrapped component. """

        sys.stderr.write("  In {0}.execute()...\n".format(self.__class__))

        # Prepare input file here
        #   - write a new script file?
        #   - write a new turbine file to overwrite the one referenced
        #       in the existing script_file?

        # Execute the component
        
        self.command[1] = self.script_file
        super(OWwrapped, self).execute()
        
        sys.stderr.write('Ran openWindExtCode: dummyVbl {:} returnCode {:}\n'.format(self.dummyVbl,self.return_code))

        # Parse output file 
        
        rptpath = rwScriptXML.rdScript(self.command[1], debug=True) #False) # get output file name from script
        
        self.gross_aep, self.array_aep, self.net_aep, owTurbs = utils.rdReport(rptpath, debug=False) 
        self.nTurbs = len(owTurbs)
        
        #print 'Gross {:.4f} GWh'.format(self.gross_aep)
        #print 'Array {:.4f} GWh'.format(self.array_aep)
        #print 'Net   {:.4f} GWh'.format(self.net_aep  )
        #print 'AEff  {:.2f} %'.format(self.aeff*100.0)
        
        # Set the output variables
        self.array_efficiency = self.array_aep / self.gross_aep        
        self.gross_aep = self.gross_aep * 1000000.0 # gWh to kWh
        self.array_aep = self.array_aep * 1000000.0
        self.net_aep   = self.net_aep   * 1000000.0

        # find net aep
        #   2014 03 28 - commented out
        #     We're reading net_aep from OpenWind output, and OW has already applied the losses
        #self.net_aep = self.net_aep * self.availability * (1-self.other_losses)

        # find array efficiency
        self.array_losses = 1 - (self.array_aep/self.gross_aep)
    
    def dump(self):
        # returns a string with a summary of object parameters
        dumpstr = ''
        dumpstr += 'Gross {:10.4f} GWh Net {:10.4f} GWh from {:4d} turbines'.format(
        self.gross_aep*0.000001,self.net_aep*0.000001, self.nTurbs)
        return dumpstr
        
#------------------------------------------------------------------

if __name__ == "__main__":

    owname = 'C:/rassess/Openwind/OpenWind64.exe'
    if not os.path.isfile(owname):
        sys.stderr.write('OpenWind executable file "{:}" not found\n'.format(owname))
        exit()

    #owXMLname = 'C:/Python27/openmdao-0.7.0/twister/models/AEP/testOWScript1.xml'
    #owXMLname = 'C:/Python27/openmdao-0.7.0/twister/models/AEP/VA_ECap.xml'
    #owXMLname = 'C:/SystemsEngr/Plant_AEPSE-master/src/Plant_AEPSE/Openwind/Enterprise/testOWScript.xml'
    owXMLname = 'C:/SystemsEngr/Plant_AEPSE_GNS/src/Plant_AEPSE/Openwind/Enterprise/testOWScript.xml'
    
    if not os.path.isfile(owXMLname):
        sys.stderr.write('OpenWind script file "{:}" not found\n'.format(owXMLname))
        exit()
    
    ow = OWwrapped(owExe = owname)
    ow.script_file = owXMLname
    
    ow.execute() # run the openWind process
    
    print ow.dump()
