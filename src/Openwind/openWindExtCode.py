# openWindExtCode.py
# 2013 06 25
'''
  Execute OpenWind using OpenMDAO's ExternalCode
  Based on example from http://openmdao.org/docs/plugin-guide/filewrapper_plugin.html
  
  Replace value of 'owExeV1130' below with path to an OpenWind executable that supports all scripting options
  
'''

import sys
sys.path.append('C:/Python27/openmdao-0.7.0/twister/models/AEP/')
import openWindUtils as utils
import wrtScriptXML

from openmdao.lib.datatypes.api import Float
from openmdao.lib.components.api import ExternalCode
from openmdao.main.api import FileMetadata

from openmdao.util.filewrap import InputFileGenerator, FileParser

#-----------------------------------------------------------------

class OWwrapped(ExternalCode):
    """A simple file wrapper for OpenWind"""

    rotorDiameter = Float(126.0, iotype='in', units='m', desc='connecting rotor diameter to force run on change') # todo: hack for now
    availability = Float(0.95, iotype='in', desc='availability')
    soilingLosses = Float(0.0, iotype='in', desc='soiling losses')
    
    array_efficiency    = Float(0.0, iotype='out', desc='Array Efficiency')
    gross_aep = Float(0.0, iotype='out', desc='Gross Output')
    net_aep   = Float(0.0, iotype='out', desc='Net Output')
    array_aep = Float(0.0, iotype='out', desc='Array Output')
    array_losses = Float(0.0, iotype='out', desc='Array losses')
    #------------------ 
    
    def __init__(self, owExeV1130):
        """Constructor for the OWwrapped component"""

        super(OWwrapped, self).__init__()

        # External Code public variables
        
        self.input_file = 'myinput.txt'
        self.output_file = 'myoutput.txt'
        self.stderr = 'myerror.log'
        
        self.scriptfile = 'scriptfile.xml' # replace with actual file name

        self.external_files = [
            #FileMetadata(path=self.input_file, input=True),
            FileMetadata(path=self.output_file),
            FileMetadata(path=self.stderr),
        ]
        
        # Set the version of OpenWind that we want to use
        
        #self.command = [owExeUnofficial, self.scriptfile]
        self.command = [owExeV1130, self.scriptfile]

    #------------------ 
    
    def execute(self):
        """ Executes our file-wrapped component. """

        # Prepare input file here
        #   - write a new script file?
        #   - write a new turbine file to overwrite the one referenced
        #       in the existing scriptfile?

        # Execute the component
        
        self.command[1] = self.scriptfile
        super(OWwrapped, self).execute()

        # Parse output file 
        
        rptpath = wrtScriptXML.rdScript(self.command[1], debug=False) # get output file name from script
        
        self.ttlGross, self.ttlArray, self.ttlNet = utils.rdReport(rptpath, debug=False) 
        
        #print 'Gross {:.4f} GWh'.format(self.ttlGross)
        #print 'Array {:.4f} GWh'.format(self.ttlArray)
        #print 'Net   {:.4f} GWh'.format(self.ttlNet  )
        #print 'AEff  {:.2f} %'.format(self.aeff*100.0)
        
        # Set the output variables
        self.array_efficiency = self.ttlArray / self.ttlGross        
        self.gross_aep = self.ttlGross * 1000000.0
        self.array_aep = self.ttlArray * 1000000.0

        # find net aep
        self.net_aep = (self.ttlNet * 1000000.0) * self.availability * (1-self.soilingLosses)

        # find array efficiency
        self.array_losses = 1 - (self.array_aep/self.gross_aep)
    
#------------------------------------------------------------------

if __name__ == "__main__":

    ow = OWwrapped(owExeV1130 = 'C:/Openwind/OpenWind64.exe')
    
    #owXMLname = 'C:/Python27/openmdao-0.7.0/twister/models/AEP/testOWScript1.xml'
    owXMLname = 'C:/Python27/openmdao-0.7.0/twister/models/AEP/VA_ECap.xml'
    #ow.command[1] = owXMLname
    ow.scriptfile = owXMLname
    
    ow.execute() # run the openWind process
