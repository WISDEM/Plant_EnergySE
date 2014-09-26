# openwind_assembly.py
# 2013 03 15
''' Run openWind from openMDAO 
    2013 03 15: G. Scott
    2013 06 07: GNS - revisions
    2014 03 26: GNS - revisions to example: paths, etc.
    2014 05 01: GNS - nTurbs replaced with turbine_number
    
    Requires
    --------
    ElementTree (should be part of Python distribution)
    OWwrapped - OpenMDAO ExternalCode component wrapper for OpenWind
    
    Notes
    -----
    At its simplest, executing openwind_assembly should just run OpenWind
      with a predefined XML script.
      - This script may include 'replace turbine' operations, in which case
        the user must be sure that the turbine file is updated between runs
        to reflect the desired turbine configuration.
      - If the report file needs to be changed, call updateRptFile()
        This will create a new script file
'''

import sys, os
import subprocess
# import xml.etree.ElementTree as ET # 20140326 now using lxml
from lxml import etree
import numpy as np

from openmdao.main.api import Component, Assembly, VariableTree
from openmdao.lib.datatypes.api import Float, Array, Int, VarTree

from vt import GenericWindTurbineVT, GenericWindTurbinePowerCurveVT, \
     ExtendedWindTurbinePowerCurveVT, GenericWindFarmTurbineLayout, \
     ExtendedWindFarmTurbineLayout, GenericWindRoseVT
                           
from fusedwind.interface import implement_base
from fusedwind.plant_flow.asym import BaseAEPModel

from openWindExtCode import OWwrapped  # OpenWind inside an OpenMDAO ExternalCode wrapper

import openwind.rwTurbXML as rwTurbXML
import openwind.rwScriptXML as rwScriptXML

#------------------------------------------------------------------

#class openwind_assembly(GenericAEPModel): # todo: has to be assembly or manipulation and passthrough of aep in execute doesnt work
#class openwind_assembly(BaseAEPModel): # todo: has to be assembly or manipulation and passthrough of aep in execute doesnt work

@implement_base(BaseAEPModel)
class openwind_assembly(Assembly): # todo: has to be assembly or manipulation and passthrough of aep in execute doesnt work
    """ Runs OpenWind from OpenMDAO framework """

    # Inputs
    hub_height     = Float(90.0, iotype='in', desc='turbine hub height', unit='m')
    rotor_diameter = Float(126.0, iotype='in', desc='turbine rotor diameter', unit='m')
    power_curve    = Array([], iotype='in', desc='wind turbine power curve')
    rpm            = Array([], iotype='in', desc='wind turbine rpm curve')
    ct             = Array([], iotype='in', desc='wind turbine ct curve')
    machine_rating = Float(6000.0, iotype='in', desc='wind turbine rated power', unit='kW')
    availability   = Float(0.941, iotype='in', desc='wind plant availability')
    wt_layout      = VarTree(GenericWindFarmTurbineLayout(), iotype='in', desc='properties for each wind turbine and layout')    
    other_losses   = Float(0.0, iotype='in', desc='wind plant losses due to blade soiling, etc')
    dummyVbl       = Float(0, iotype='in', desc='unused variable to make it easy to do DOE runs')
    
    # TODO: loss inputs
    # TODO: wake model option selections

    # Outputs
      # inherits output vbls net_aep and gross_aep from GenericAEPModel - NOT when using fusedwind implement_base
      
    gross_aep        = Float(0.0, iotype='out', desc='Gross Output')
    net_aep          = Float(0.0, iotype='out', desc='Net Output')
    #ideal_aep = Float(0.0, iotype='out', desc='Ideal Annual Energy Production before topographic, availability and loss impacts', unit='kWh')
    array_aep       = Float(0.0, iotype='out', desc='Gross Annual Energy Production net of array impacts', unit='kWh')
    array_losses    = Float(0.0, iotype='out', desc='Array Losses')
    capacity_factor = Float(0.0, iotype='out', desc='capacity factor')
    turbine_number = Int(100, iotype='out', desc='plant number of turbines')

    # -------------------
    
    def __init__(self, openwind_executable, workbook_path, turbine_name=None, script_file=None, 
                 academic=False, debug=False):
        """ Creates a new LCOE Assembly object """

        foundErrors = False
        if not os.path.isfile(openwind_executable):
            sys.stderr.write('\n*** ERROR: executable {:} not found\n\n'.format(openwind_executable))
            foundErrors = True
        if not os.path.isfile(workbook_path):
            sys.stderr.write('\n*** ERROR: workbook {:} not found\n\n'.format(workbook_path))
            foundErrors = True
        if foundErrors:
            return None
        
        # Set the location where new scripts and turbine files will be written
        
        self.workDir = os.getcwd()
        #self.workDir = os.path.dirname(os.path.realpath(__file__)) # location of this source file
                
        self.openwind_executable = openwind_executable
        self.workbook_path = workbook_path
        self.turbine_name = turbine_name
        self.script_file = script_file
        self.academic = academic
        self.debug = debug
        
        super(openwind_assembly, self).__init__()

        # TODO: hack for now assigning turbine
        self.turb = GenericWindTurbinePowerCurveVT()
        self.turb.power_rating = self.machine_rating
        self.turb.hub_height = self.hub_height
        self.turb.power_curve = np.copy(self.power_curve)
        for i in xrange(0,self.turbine_number):
            self.wt_layout.wt_list.append(self.turb)

    # -------------------
    
    def configure(self):
        """ Add Openwind external code component """

        super(openwind_assembly, self).configure()        
        
        if self.academic:
            #ow = OWACwrapped(self.openwind_executable, scriptFile=self.script_file, debug=True)
            sys.stderr.write('\nERROR - openwind_assembly.py not currently configured for Academic version\n')
            sys.stderr.write('Use ../Academic/openwindAC_assembly.py instead\n')
            quit()
        else:
            ow = OWwrapped(self.openwind_executable, scriptFile=self.script_file, debug=self.debug)
        self.add('ow', ow)
        
        self.driver.workflow.add(['ow'])
        
        # Inputs to OWwrapped
        
        self.connect('rotor_diameter', 'ow.rotor_diameter') # todo: hack to force external code execution
        self.connect('other_losses', 'ow.other_losses')
        self.connect('availability', 'ow.availability')
        
        self.connect('dummyVbl', 'ow.dummyVbl')
        
        # Outputs from OWwrapped
        
        self.connect('ow.array_losses', 'array_losses')
        self.connect('ow.gross_aep', 'gross_aep')
        self.connect('ow.array_aep', 'array_aep')
        self.connect('ow.net_aep', 'net_aep')
        self.connect('ow.turbine_number', 'turbine_number')
    
    # -------------------
    
    def execute(self):
        """
            Set up XML and run OpenWind
            #This will leave OW running - use the File/Exit button to shut it down until
            #  Nick comes up with a way to stop it from the script.
            # 20140326: OW now has Exit operation in scripter
        """

        if self.debug:
            sys.stderr.write("In {0}.execute()...\n".format(self.__class__))

        report_path = self.workDir + '/' + 'scrtest1.txt'
        workbook_path = self.workbook_path
        turbine_name = self.turbine_name

        # Prepare for next iteration here...
        #   - write new scripts
        #   - write new turbine files
        #   - etc.
        #turbine_path = self.workDir + '/' + 'Turbine_Model.owtg'
        #self.writeNewTurbine('Turbine_Model.owtg')

        # write new script for execution  
    
        # newScriptName = 'OpenWind_Script.xml'
        # self.writeNewScript(newScriptName)
        # self.command[1] = newScriptName
        
        # will actually run the workflow
        super(openwind_assembly, self).execute()

        # calculate capacity factor
        #  - assumes that all turbines have the same power rating
        #    and that self.wt_layout is correct
        
        #self.capacity_factor = ((self.net_aep) / (self.wt_layout.wt_list[0].power_rating * 8760.0 * self.turbine_number))
        # 8766 hrs = 365.25 days to agree with OpenWind
        
        self.capacity_factor = ((self.net_aep) / (self.wt_layout.wt_list[0].power_rating * 8766.0 * self.turbine_number))
        
    # -------------------
    
    def writeNewTurbine(self, turbFileName):
        ''' Set up turbine to write to xml
        '''
        rho = [1.225]
        vels = [float(i) for i in range(26)]
        
        # power table
        
        power = []
        for i in xrange(0,4):
            power.append(0.0)
        counter = 5.0
        for i in xrange(5,26):
            myi = min(range(self.power_curve.shape[1]), key=lambda i: abs(self.power_curve[0][i]-counter))
            power.append(self.power_curve[1][myi])
            counter += 1.0 
        power.append(self.power_curve[1][-1])

        # thrust table
        
        thrust = []
        for i in xrange(0,4):
            thrust.append(1.0)
        counter = 5.0
        for j in xrange(5,26):
            myi = min(range(self.ct.shape[1]), key=lambda i: abs(self.ct[0][i]-counter))
            thrust.append(self.ct[1][myi])
            counter += 1.0
        thrust.append(self.ct[1][0])
        
        # RPM table
        
        rpm = []
        for i in xrange(0,4):
            rpm.append(0.0)
        counter = 5.0
        for j in xrange(5,26):
            myi = min(range(self.rpm.shape[1]), key=lambda i: abs(self.rpm[0][i]-counter))
            rpm.append(self.rpm[1][myi])
            counter += 1.0
        rpm.append(self.rpm[1][-1])

        percosts = []
        cut_in_wind_speed = 4.0
        cut_out_wind_speed = 25.0
        blade_number = 3
        turbine_cost = 2000000
        foundation_cost =  100000
        turbine_name = 'NewTurbine'
        desc = 'New Turbine'
        turbtree = rwTurbXML.getTurbTree(turbine_name, desc, \
                                          vels, power, thrust, rpm, \
                                          self.hub_height, self.rotor_diameter, rho, \
                                          percosts, cut_in_wind_speed, cut_out_wind_speed, \
                                          blade_number, self.machine_rating, turbine_cost, foundation_cost)
        turbXML = etree.tostring(turbtree, 
                                 xml_declaration=True,
                                 doctype='<!DOCTYPE {:}>'.format(turbine_name), 
                                 pretty_print=True)

        ofh = open(self.workDir + '/' + turbFileName, 'w')
        ofh.write(turbXML)
        ofh.close()
        
    # -------------------
    
    def writeNewScript(self, scriptFileName):
        '''
          Write a new XML script to scriptFileName and use that as the active
          script for OpenWind
          Operations are: load workbook, replace turbine, energy capture, exit
        '''
        
        script_tree, operations = rwScriptXML.newScriptTree(self.report_path)    
        # add operations to 'operations' (the 'AllOperations' tree in script_tree)
        
        rwScriptXML.makeChWkbkOp(operations,self.workbook_path)       # change workbook
        rwScriptXML.makeRepTurbOp(operations,turbine_name,turbine_path)  # replace turbine
        rwScriptXML.makeEnCapOp(operations)                # run energy capture
        rwScriptXML.makeExitOp(operations)                 # exit
        
        script_XML = etree.tostring(script_tree, 
                                   xml_declaration=True, 
                                   doctype='<!DOCTYPE OpenWindScript>',
                                   pretty_print=True)
        
        self.ow.script_file = self.workDir + '/' + scriptFileName
        ofh = open(thisdir + '/' + self.ow.script_file, 'w')
        ofh.write(script_XML)
        ofh.close()
    
    # -------------------
    
    def updateRptPath(self, rptPathName, newScriptName):
        '''
        Writes a new script file and sets internal script name
        New script writes to 'rptPathName'
        rptPathName should be a full path name (if possible)
        '''
        
        if not hasattr(self,'ow'):
            sys.stderr.write("{:}: 'ow' not defined yet (missing script file?)\n".format(self.__class__))
            raise RuntimeError("OpenWind wrapped executable not defined")
            return
            
        e = rwScriptXML.parseScript(self.ow.script_file, debug=self.debug)
        rp = e.find("ReportPath")
        if rp is None:
            sys.stderr.write('Can\'t find report path in "{:}"\n'.format(self.ow.script_file))
            return
            
        if self.debug:
            sys.stderr.write('Changing report path from "{:}" to "{:}"\n'.format(rp.get('value'),rptPathName))
        rp.set('value',rptPathName)
        
        rwScriptXML.wrtScript(e, newScriptName)
        self.ow.script_file = self.workDir + '/' + newScriptName
        if self.debug:
            sys.stderr.write('Wrote new script file "{:}"\n'.format(self.ow.script_file))
            
#------------------------------------------------------------------

def example():

    # simple test of module
    
    debug = False 
    
    for arg in sys.argv[1:]:
        if arg == '-debug':
            debug = True
        if arg == '-help':
            sys.stderr.write('USAGE: python openwind_assembly.py [-debug]\n')
            exit()
    
    from openwind.findOW import findOW
    owExe = findOW(debug=debug, academic=False)
    if not os.path.isfile(owExe):
        exit()

    test_path = '../test/'
    
    workbook_path = test_path + 'VA_test.blb'
    turbine_name = 'Alstom Haliade 150m 6MW' # should match default turbine in workbook
    script_file = test_path + 'ecScript.xml'
    
    # should check for existence of both owExe and workbook_path before
    #   trying to run openwind
    
    owAsm = openwind_assembly(owExe, workbook_path, turbine_name=turbine_name, script_file=script_file,
                              debug=debug)
                              
    owAsm.configure()
    
    owAsm.updateRptPath('newReport.txt', 'newTestScript.xml')
    
    owAsm.power_curve = np.array([[1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, \
                           11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0, 21.0, 22.0, 23.0, 24.0, 25.0, 26.0], \
                          [0.0, 0.0, 0.0, 187.0, 350.0, 658.30, 1087.4, 1658.3, 2391.5, 3307.0, \
                          4415.70, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, \
                          5000.0, 5000.0, 5000.0, 5000.0, 0.0]])

    owAsm.ct = np.array([[1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, \
                           11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0, 21.0, 22.0, 23.0, 24.0, 25.0, 26.0], \
                          [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, \
                           1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]])

    owAsm.rpm = np.array([[1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, \
                           11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0, 21.0, 22.0, 23.0, 24.0, 25.0, 26.0], \
                          [7.0, 7.0, 7.0, 7.0, 7.0, 7.0, 7.0, 7.0, 7.0, 7.0, \
                           7.0, 7.0, 7.0, 7.0, 7.0, 7.0, 7.0, 7.0, 7.0, 7.0, 7.0, 7.0, 7.0, 7.0, 7.0, 7.0]])

    owAsm.execute() # run the openWind process

    print 'openwind_assembly Final Values'
    print '  NumTurbs {:}'.format(owAsm.turbine_number)
    print '  Gross {:.4f} kWh'.format(owAsm.gross_aep*0.001)
    print '  Array losses {:.2f} %'.format(owAsm.array_losses*100.0)
    print '  Array {:.4f} kWh'.format(owAsm.array_aep*0.001)
    otherLosses = 1.0 - (owAsm.net_aep/owAsm.array_aep)
    print '  Other losses {:.2f} %'.format(otherLosses*100.0)
    print '  Net   {:.4f} kWh'.format(owAsm.net_aep*0.001)
    print '  CF    {:.4f} %'.format(owAsm.capacity_factor*100.0)

if __name__ == "__main__":

    example()

    example()