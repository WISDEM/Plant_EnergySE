# openwindAC_assembly.py
# 2013 03 15
''' Run openWind from openMDAO 
    2013 03 15: G. Scott
    2013 06 07: GNS - revisions
    2014 03 26: GNS - revisions to example: paths, etc.
    
    Requires
    --------
    ElementTree : (should be part of Python distribution)
    OWACcomp : OpenMDAO component wrapper for OpenWind
    
    Notes
    -----
    At its simplest, executing openwindAC_assembly should just run OpenWind
      with a predefined XML script.
      - This script may include 'replace turbine' operations, in which case
        the user must be sure that the turbine file is updated between runs
        to reflect the desired turbine configuration.
      - If the report file needs to be changed, call updateRptFile()
        This will create a new script file
'''

import sys, os
import subprocess
from lxml import etree
import numpy as np

from openmdao.main.api import Component, Assembly, VariableTree
from openmdao.lib.datatypes.api import Float, Array, Int, VarTree

from fusedwind.plant_flow.fused_plant_asym import GenericAEPModel
from fusedwind.plant_flow.fused_plant_vt import GenericWindTurbinePowerCurveVT, ExtendedWindTurbinePowerCurveVT
from fusedwind.plant_flow.fused_plant_vt import GenericWindFarmTurbineLayout

#from openWindExtCode import OWwrapped  # OpenWind inside an OpenMDAO ExternalCode wrapper
#from openWindAcExtCode import OWACwrapped  # OpenWind inside an OpenMDAO ExternalCode wrapper
from openWindAcComponent import OWACcomp  # OpenWind inside an OpenMDAO Component

import Plant_AEPSE.Openwind.Enterprise.rwTurbXML as rwTurbXML
import Plant_AEPSE.Openwind.Enterprise.rwScriptXML as rwScriptXML
import Plant_AEPSE.Openwind.Enterprise.getworkbookvals as getworkbookvals

#------------------------------------------------------------------

class openwindAC_assembly(GenericAEPModel): # todo: has to be assembly or manipulation and passthrough of aep in execute doesnt work
    """ Runs OpenWind from OpenMDAO framework """

    # Inputs
    
    #hub_height     = Float(100.0, iotype='in', desc='turbine hub height', unit='m')
    #rotor_diameter = Float(126.0, iotype='in', desc='turbine rotor diameter', unit='m')
    #power_curve    = Array([], iotype='in', desc='wind turbine power curve')
    #rpm            = Array([], iotype='in', desc='wind turbine rpm curve')
    #ct             = Array([], iotype='in', desc='wind turbine ct curve')
    #machine_rating = Float(6000.0, iotype='in', desc='wind turbine rated power', unit='kW')
    turb_props = VarTree(ExtendedWindTurbinePowerCurveVT(), iotype='in', desc='properties for default turbine')
    
    turbine_number = Int(100, iotype='in', desc='plant number of turbines')
    availability   = Float(0.941, iotype='in', desc='wind plant availability')
    other_losses   = Float(0.0, iotype='in', desc='wind plant losses due to blade soiling, etc')
    dummyVbl       = Float(0, iotype='in', desc='unused variable to make it easy to do DOE runs')
    
    wt_layout      = VarTree(GenericWindFarmTurbineLayout(), iotype='in', desc='properties for each wind turbine and layout')    
    
    # wt_layout.wt_positions[] is an Array with units of m
    
    # TODO: loss inputs
    # TODO: wake model option selections

    # Outputs
      # inherits output vbls net_aep and gross_aep from GenericAEPModel
      
    #ideal_aep = Float(0.0, iotype='out', desc='Ideal Annual Energy Production before topographic, availability and loss impacts', unit='kWh')
    array_aep       = Float(0.0, iotype='out', desc='Gross Annual Energy Production net of array impacts', unit='kWh')
    array_losses    = Float(0.0, iotype='out', desc='Array Losses')
    capacity_factor = Float(0.0, iotype='out', desc='capacity factor')
    nTurbs          = Int(0, iotype='out', desc='Number of turbines')

    # -------------------
    
    def __init__(self, openwind_executable, workbook_path, 
                 turbine_name=None, script_file=None, academic=True,
                 wt_positions=None,
                 debug=False):
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
        
        #if wt_positions is not None:
            #attrs = dir(self)
            #for a in attrs:
            #    print a
                
            #self.wt_layout.wt_positions = wt_positions
            
        super(openwindAC_assembly, self).__init__()

        # TODO: hack for now assigning turbine
        self.turb = GenericWindTurbinePowerCurveVT()
        self.turb.power_rating = self.machine_rating
        self.turb.hub_height = self.hub_height
        self.turb.power_curve = np.copy(self.power_curve)
        for i in xrange(0,self.turbine_number):
            self.wt_layout.wt_list.append(self.turb)

    # -------------------
    
    def configure(self):
        """ make connections """

        super(openwindAC_assembly, self).configure()        
        
        ow = OWACcomp(self.openwind_executable, scriptFile=self.script_file, debug=self.debug)
        #self.add('ow', ow)
        
        self.driver.workflow.add(['ow'])
        
        # Inputs to OWACcomp
        
        self.connect('rotor_diameter', 'ow.rotor_diameter') # todo: hack to force external code execution
        self.connect('other_losses', 'ow.other_losses')
        self.connect('availability', 'ow.availability')
        
        self.connect('dummyVbl', 'ow.dummyVbl')
        
        # Outputs from OWACcomp
        
        self.connect('ow.array_losses', 'array_losses')
        self.connect('ow.gross_aep', 'gross_aep')
        self.connect('ow.array_aep', 'array_aep')
        self.connect('ow.net_aep', 'net_aep')
        self.connect('ow.nTurbs', 'nTurbs')
    
    # -------------------
    
    def execute(self):
        """
            Set up XML and run OpenWind
        """

        sys.stderr.write("In {0}.execute()...\n".format(self.__class__))
        print self.wt_layout.wt_positions

        report_path = self.workDir + '/' + 'scrtest1.txt'
        workbook_path = self.workbook_path

        # Prepare for next iteration here...
        #   - write new scripts
        #   - write new turbine files
        #   - etc.

        # write new script for execution  
    
        # newScriptName = 'OpenWind_Script.xml'
        # self.writeNewScript(newScriptName)
        # self.command[1] = newScriptName
        
        # will actually run the workflow
        super(openwindAC_assembly, self).execute()

        # calculate capacity factor
        #  - assumes that all turbines have the same power rating
        #    and that self.wt_layout is correct
        
        #self.capacity_factor = ((self.net_aep) / (self.wt_layout.wt_list[0].power_rating * 8760.0 * len(self.wt_layout.wt_list)))
        self.capacity_factor = ((self.net_aep) / (self.wt_layout.wt_list[0].power_rating * 8760.0 * self.nTurbs))
        
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
        
        e = rwScriptXML.parseScript(self.ow.script_file)
        rp = e.find("ReportPath")
        if rp is None:
            sys.stderr.write('Can\'t find report path in "{:}"\n'.format(self.ow.script_file))
            return
            
        sys.stderr.write('Changing report path from "{:}" to "{:}"\n'.format(rp.get('value'),rptPathName))
        rp.set('value',rptPathName)
        
        rwScriptXML.wrtScript(e, newScriptName)
        self.ow.script_file = self.workDir + '/' + newScriptName
        sys.stderr.write('Wrote new script file "{:}"\n'.format(self.ow.script_file))
            
#------------------------------------------------------------------

def example():

    owExe = 'C:/rassess/Openwind/OpenWind64_ac.exe'
    
    #workbook_path = 'C:/Models/OpenWind/Workbooks/OpenWind_Model.blb'
    #turbine_name = 'NREL 5 MW'
    workbook_path = 'C:/SystemsEngr/Test/VA_test.blb'
    turbine_name = 'Alstom Haliade 150m 6MW' # should match default turbine in workbook
    #script_file = 'C:/SystemsEngr/test/ecScript.xml'
    script_file = 'C:/SystemsEngr/test/owacScript.xml' # optimize operation
    
    #wt_positions = [[456000.00,4085000.00],
    #                [456500.00,4085000.00]]
    wt_positions = getworkbookvals.getTurbPos(workbook_path, owExe)
    for i in range(len(wt_positions)):
        sys.stderr.write('Turb{:2d} {:.1f} {:.1f}\n'.format(i,wt_positions[i][0],wt_positions[i][1]))
    # Pass these positions to openWindAcComponent somehow

    # should check for existence of both owExe and workbook_path before
    #   trying to run openwind
    
    owAsy = openwindAC_assembly(owExe, workbook_path, 
                             turbine_name=turbine_name, 
                             script_file=script_file,
                             wt_positions=wt_positions,
                             debug=True)
    owAsy.updateRptPath('newReport.txt', 'newTestScript.xml')
    
    # Originally, there was a turbine power/ct/rpm definition here, but that's not
    # part of an owAsy, so that code is now in C:/SystemsEngr/test/pcrvtst.py
    
    owAsy.execute() # run the openWind process

    otherLosses = 1.0 - (owAsy.net_aep/owAsy.array_aep)
    
    print 'Gross {:.4f} kWh'.format(owAsy.gross_aep*0.001)
    print 'Array losses {:.2f} %'.format(owAsy.array_losses*100.0)
    print 'Array {:.4f} kWh'.format(owAsy.array_aep*0.001)
    print 'Other losses {:.2f} %'.format(otherLosses*100.0)
    print 'Net   {:.4f} kWh'.format(owAsy.net_aep*0.001)
    print 'CF    {:.4f} %'.format(owAsy.capacity_factor*100.0)

if __name__ == "__main__":

    example()