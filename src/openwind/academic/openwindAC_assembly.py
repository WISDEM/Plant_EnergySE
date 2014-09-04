# openwindAC_assembly.py
# (was openwindACpt_assembly.py)
# 2013 03 15
# Uses passthroughs

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
from openmdao.main.api import set_as_top
from openmdao.lib.datatypes.api import Float, Array, Int, VarTree

from fusedwind.plant_flow.fused_plant_asym import GenericAEPModel
from fusedwind.plant_flow.fused_plant_vt import GenericWindTurbinePowerCurveVT, ExtendedWindTurbinePowerCurveVT
from fusedwind.plant_flow.fused_plant_vt import GenericWindFarmTurbineLayout

#from openWindExtCode import OWwrapped  # OpenWind inside an OpenMDAO ExternalCode wrapper
#from openWindAcExtCode import OWACwrapped  # OpenWind inside an OpenMDAO ExternalCode wrapper
from openWindAcComponent import OWACcomp  # OpenWind inside an OpenMDAO Component

import openwind.rwTurbXML as rwTurbXML
import openwind.rwScriptXML as rwScriptXML
import openwind.getworkbookvals as getworkbookvals
import openwind.turbfuncs as turbfuncs

#------------------------------------------------------------------

class openwindAC_assembly(GenericAEPModel): # todo: has to be assembly or manipulation and passthrough of aep in execute doesnt work
    """ Runs OpenWind from OpenMDAO framework """

    # Inputs
    
    turb_props = VarTree(ExtendedWindTurbinePowerCurveVT(), iotype='in', desc='properties for default turbine')
    
    turbine_number = Int(100, iotype='in', desc='plant number of turbines')
    # TODO: loss inputs
    # TODO: wake model option selections

    # Outputs
      # inherits output vbls net_aep and gross_aep from GenericAEPModel
      
    #array_aep       = Float(0.0, iotype='out', desc='Gross Annual Energy Production net of array impacts', unit='kWh')
    total_losses    = Float(0.0, iotype='out', desc='Total Losses (gross to net)')
    capacity_factor = Float(0.0, iotype='out', desc='capacity factor')

    # -------------------
    
    def __init__(self, openwind_executable, workbook_path, 
                 turbine_name=None, 
                 script_file=None, 
                 academic=True,
                 wt_positions=None,
                 machine_rating=None,
                 start_once=False,
                 debug=False):
        """ Creates a new GenericAEPModel Assembly object for OpenWind Academic """

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
        self.machine_rating = machine_rating
        self.start_once = start_once
        
        if self.debug:
            sys.stderr.write('\nIn {:}.__init__()\n'.format(self.__class__))
        
        # Set initial positions of turbines
        
        self.init_wt_positions = []    
        if wt_positions is not None:
            self.init_wt_positions = wt_positions    
            #self.wt_layout.wt_positions = wt_positions

        # TODO: hack for now assigning turbine
        
        self.turb = GenericWindTurbinePowerCurveVT()
        if self.machine_rating is not None:
            self.turb.power_rating = self.machine_rating
        #self.turb.hub_height = self.hub_height
        #self.turb.power_curve = np.copy(self.power_curve)
        
        # self.wt_layout is created with a passthrough in configure(), but doesn't exist yet
        #for i in xrange(0,self.turbine_number):
        #    self.wt_layout.wt_list.append(self.turb)
        
        # call to super().__init__ needs to be at the end
        #   - otherwise, self.* declared later will not exist
            
        super(openwindAC_assembly, self).__init__()

    # -------------------
    
    def configure(self):
        """ make connections """

        if self.debug:
            sys.stderr.write('\nIn {:}.configure()\n'.format(self.__class__))
        
        super(openwindAC_assembly, self).configure()        
        
        # Create component instances
        
        ow = OWACcomp(self.openwind_executable, 
                      scriptFile=self.script_file, 
                      start_once=self.start_once,
                      debug=self.debug)
        self.add('ow', ow)
        
        # Add components to workflow
        
        self.driver.workflow.add(['ow'])
        
        # Inputs to OWACcomp
        
        self.connect('turb_props.rotor_diameter', 'ow.rotor_diameter') # todo: hack to force external code execution
        
        self.create_passthrough('ow.other_losses')
        self.create_passthrough('ow.availability')
        self.create_passthrough('ow.wt_layout')
        
        self.create_passthrough('ow.dummyVbl')
        
        # Outputs from OWACcomp
        
        # We can't create passthroughs for gross_aep and net_aep because they're inherited from GenericAEPModel
        #self.create_passthrough('ow.gross_aep')
        #self.create_passthrough('ow.net_aep')
        self.connect('ow.gross_aep', 'gross_aep')
        self.connect('ow.net_aep', 'net_aep')
        
        self.create_passthrough('ow.nTurbs')
        
        self.wt_layout.wt_list = [self.turb for i in range(len(self.init_wt_positions))]
        
        if self.debug:
            conns = self.list_connections()
            sys.stderr.write('Connections\n')
            for conn in conns:
                sys.stderr.write('  {:} to {:}\n'.format(conn[0],conn[1]))
    
    # -------------------
    
    def execute(self):
        """
            Set up XML and run OpenWind
        """

        if self.debug:
            sys.stderr.write("\nIn {0}.execute()...\n".format(self.__class__))
        
        # ---- Set up parameters
            
        # initial positions are 'connect'ed to OWcomp object with passthrough of wt_layout
        
        # set turbine positions
        #   - from initial positions?
        #   - using another component that sets positions?
        
        self.wt_layout.wt_positions = self.init_wt_positions # use initial positions
        
        # 2014 05 26 - initialize or modify the turbine type here
        #   - read from file
        #   - modify existing turbine type
        #   - add component that returns a new turbine type
        # trb == ExtendedWindTurbinePowerCurveVT()
        
        nt = len(self.wt_layout.wt_positions)
        
        # initialize from file
        owtg_file = 'C:/SystemsEngr/Plant_AEPSE/src/Plant_AEPSE/test/Alstom6MW.owtg'
        trb = turbfuncs.owtg_to_wtpc(owtg_file)
        
        for i in range(nt):
            self.wt_layout.wt_list[i] = trb
        
        # show parameters
        
        if self.debug:
            for i in range(len(self.wt_layout.wt_positions)):
                sys.stderr.write('{:3d} {:.1f} {:.1f}\n'.format(i, 
                   self.wt_layout.wt_positions[i][0],self.wt_layout.wt_positions[i][1]))
            
            s = turbfuncs.wtpc_dump(self.wt_layout.wt_list[0])
            sys.stderr.write(s)
            
        #report_path = self.workDir + '/' + 'scrtest1.txt'
        #workbook_path = self.workbook_path

        # Prepare for next iteration here...
        #   - write new scripts
        #   - write new turbine files
        #   - etc.
        
        owtg_str = turbfuncs.wtpc_to_owtg(self.turb_props)
        
        # write new script for execution  
    
        # newScriptName = 'OpenWind_Script.xml'
        # self.writeNewScript(newScriptName)
        # self.command[1] = newScriptName
        
        # ---- Run the workflow
        
        super(openwindAC_assembly, self).execute()

        # ---- Process results
        
        # calculate capacity factor
        #  - assumes that all turbines have the same power rating
        #    and that self.wt_layout is correct
        
        if (self.wt_layout.wt_list[0].power_rating is None or 
            self.wt_layout.wt_list[0].power_rating == 0.0):
            self.capacity_factor = 0.0
            sys.stderr.write('\n*** WARNING: turbine power_rating not set\n\n')
        else:
            # power_rating is in W, but net_aep is in kWh
            self.capacity_factor = ((self.net_aep) / (self.wt_layout.wt_list[0].power_rating*0.001 * 8760.0 * self.nTurbs))
        
        self.total_losses = (self.gross_aep - self.net_aep) / self.gross_aep
        
    # -------------------
    
    def updateRptPath(self, rptPathName, newScriptName):
        '''
        Writes a new script file and sets self.ow.script_file
        New script is identical to current script, except that it writes to 'rptPathName'
        rptPathName should be a full path name (if possible)
        '''
        
        e = rwScriptXML.parseScript(self.ow.script_file)
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
            
    # -------------------
    
    def writeNewScript(self, scriptFileName):
        '''
          Write a new XML script to scriptFileName and use that as the active
          script for OpenWind
          Operations are: load workbook, replace turbine, energy capture, exit
          NOT USED
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
    
#------------------------------------------------------------------

def example():

    debug = False 
    start_once = False
    modify_turbine = False
    
    for arg in sys.argv[1:]:
        if arg == '-debug':
            debug = True
        if arg == '-once':
            start_once = True
        if arg == '-modturb':
            modify_turbine = True
        if arg == '-help':
            sys.stderr.write('USAGE: python openWindAcComponent.py [-once] [-debug] [-modturb]\n')
            exit()
    
    owExe = 'C:/rassess/Openwind/OpenWind64_ac.exe'
    from openwind.findOW import findOW
    owExe = findOW(debug=debug, academic=True)
    
    workbook_path = '../../test/VA_test.blb'
    
    turbine_name = 'Alstom Haliade 150m 6MW' # should match default turbine in workbook
    machine_rating = 6000.0
    
    script_file = '../../test/owacScript.xml' # optimize operation
    if modify_turbine:
        script_file = '../../test/rtopScript.xml' # replace turbine, optimize
        if debug:
            sys.stderr.write('Turbine will be modified\n')
        
    wt_positions = getworkbookvals.getTurbPos(workbook_path, owExe, delFiles=False)
    if debug:
        sys.stderr.write('Initial turbine positions from workbook\n')
        for i in range(len(wt_positions)):
            sys.stderr.write('  Turb{:2d} {:.1f} {:.1f}\n'.format(i,wt_positions[i][0],wt_positions[i][1]))

    # should check for existence of both owExe and workbook_path before
    #   trying to run openwind
    
    owAsy = openwindAC_assembly(owExe, workbook_path, 
                             turbine_name=turbine_name, 
                             script_file=script_file,
                             wt_positions=wt_positions,
                             machine_rating=machine_rating,
                             start_once=start_once,
                             debug=debug) 
    owAsy.updateRptPath('newReport.txt', 'newTestScript.xml')
    
    # Originally, there was a turbine power/ct/rpm definition here, but that's not
    # part of an owAsy, so that code is now in C:/SystemsEngr/test/pcrvtst.py
    
    if True:
        owa = set_as_top(owAsy)
        if debug:
            sys.stderr.write('\n*** Running top-level assembly\n')
        owa.run()
    
    else:
        owAsy.execute() # run the openWind process

    print 'openwindAC_assembly results:'
    print '  Gross {:.4f} mWh'.format(owAsy.gross_aep*0.001)
    print '  Net   {:.4f} mWh'.format(owAsy.net_aep*0.001)
    print '  Total losses {:.2f} %'.format(owAsy.total_losses*100.0)
    print '  CF    {:.2f} %'.format(owAsy.capacity_factor*100.0)

if __name__ == "__main__":

    example()

#------------------- OLD CODE ---------------------

    #hub_height     = Float(100.0, iotype='in', desc='turbine hub height', unit='m')
    #rotor_diameter = Float(126.0, iotype='in', desc='turbine rotor diameter', unit='m')
    #power_curve    = Array([], iotype='in', desc='wind turbine power curve')
    #rpm            = Array([], iotype='in', desc='wind turbine rpm curve')
    #ct             = Array([], iotype='in', desc='wind turbine ct curve')
    #machine_rating = Float(6000.0, iotype='in', desc='wind turbine rated power', unit='kW')
    #availability   = Float(0.941, iotype='in', desc='wind plant availability')
    #other_losses   = Float(0.0, iotype='in', desc='wind plant losses due to blade soiling, etc')
    #dummyVbl       = Float(0, iotype='in', desc='unused variable to make it easy to do DOE runs')
    
    #wt_layout      = VarTree(GenericWindFarmTurbineLayout(), iotype='in', desc='properties for each wind turbine and layout')    
    #wt_layout      = VarTree(GenericWindFarmTurbineLayout(), iotype='out', desc='properties for each wind turbine and layout')    
    
    #ideal_aep      = Float(0.0, iotype='out', desc='Ideal Annual Energy Production before topographic, availability and loss impacts', unit='kWh')
    #array_losses   = Float(0.0, iotype='out', desc='Array Losses')
    #nTurbs         = Int(0, iotype='out', desc='Number of turbines')
    
        #self.connect('ow.array_losses', 'array_losses')
        #self.connect('ow.array_aep', 'array_aep') # not available in Academic version
        
    #workbook_path = 'C:/Models/OpenWind/Workbooks/OpenWind_Model.blb'
    #turbine_name = 'NREL 5 MW'
    #script_file = 'C:/SystemsEngr/test/ecScript.xml'

    #otherLosses = 1.0 - (owAsy.net_aep/owAsy.array_aep)
    
    #print '  Array losses {:.2f} %'.format(owAsy.array_losses*100.0)
    #print '  Array {:.4f} kWh'.format(owAsy.array_aep*0.001)
    #print '  Other losses {:.2f} %'.format(otherLosses*100.0)
    
        #self.capacity_factor = ((self.net_aep) / (self.wt_layout.wt_list[0].power_rating * 8760.0 * len(self.wt_layout.wt_list)))
