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

import owAcademicUtils as acutils

from openmdao.main.api import Component, Assembly, VariableTree
from openmdao.main.api import set_as_top
from openmdao.lib.datatypes.api import Float, Array, Int, VarTree

from fusedwind.interface import implement_base
from fusedwind.plant_flow.asym import BaseAEPModel
from fusedwind.plant_flow.vt import GenericWindTurbineVT, \
               GenericWindTurbinePowerCurveVT, ExtendedWindTurbinePowerCurveVT, \
               GenericWindFarmTurbineLayout,   ExtendedWindFarmTurbineLayout

from openWindAcComponent import OWACcomp  # OpenWind inside an OpenMDAO Component

import plant_energyse.openwind.rwTurbXML as rwTurbXML
import plant_energyse.openwind.rwScriptXML as rwScriptXML
import plant_energyse.openwind.getworkbookvals as getworkbookvals
import plant_energyse.openwind.turbfuncs as turbfuncs

#------------------------------------------------------------------

@implement_base(BaseAEPModel)
class openwindAC_assembly(Assembly): # todo: has to be assembly or manipulation and passthrough of aep in execute doesnt work
    """ Runs OpenWind from OpenMDAO framework """

    # Inputs
    
    turb_props = VarTree(ExtendedWindTurbinePowerCurveVT(), iotype='in', desc='properties for default turbine')
    
    turbine_number = Int(100, iotype='in', desc='plant number of turbines')
    # TODO: loss inputs
    # TODO: wake model option selections

    # Outputs
      # inherits output vbls net_aep and gross_aep from GenericAEPModel
      
    gross_aep        = Float(0.0, iotype='out', desc='Gross Output')
    net_aep          = Float(0.0, iotype='out', desc='Net Output')
    #array_aep       = Float(0.0, iotype='out', desc='Gross Annual Energy Production net of array impacts', unit='kWh')
    total_losses    = Float(0.0, iotype='out', desc='Total Losses (gross to net)')
    capacity_factor = Float(0.0, iotype='out', desc='capacity factor')

    # -------------------
    
    #def __init__(self, openwind_executable, workbook_path, 
    # try with default values to fix problem with interface.py
    def __init__(self, 
                 openwind_executable=None, workbook_path=None, 
                 turbine_name=None, # not used?
                 script_file=None, 
                 academic=True,
                 wt_positions=None,
                 machine_rating=None,
                 start_once=False,
                 debug=False):
        """ Creates a new GenericAEPModel Assembly object for OpenWind Academic """

        foundErrors = False
        if openwind_executable is None:
            sys.stderr.write('\n*** ERROR: executable not assigned\n\n')
            foundErrors = True
        elif not os.path.isfile(openwind_executable):
            sys.stderr.write('\n*** ERROR: executable {:} not found\n\n'.format(openwind_executable))
            foundErrors = True
        if workbook_path is None:
            sys.stderr.write('\n*** ERROR: workbook_path not assigned\n\n')
            foundErrors = True
        elif not os.path.isfile(workbook_path):
            sys.stderr.write('\n*** ERROR: workbook {:} not found\n\n'.format(workbook_path))
            foundErrors = True
        if foundErrors:
            return None
        
        # Set the location where new scripts and turbine files will be written
        
        self.workDir = os.getcwd()
        #self.workDir = os.path.dirname(os.path.realpath(__file__)) # location of this source file
        
        self.ow = None # the Openwind Component
                
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
        
        #self.turb = GenericWindTurbinePowerCurveVT()
        self.turb = ExtendedWindTurbinePowerCurveVT()
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

        #owtg_file = '../test/NREL5MW.owtg'
        #sys.stderr.write('\n*** WARNING: initializing turbine from {:} - why??\n\n'.format(owtg_file))
        #trb = turbfuncs.owtg_to_wtpc(owtg_file)
        
        if self.debug:
            sys.stderr.write('\n*** WARNING: initializing turbine from ExtendedWindTurbinePowerCurveVT\n\n')
        trb = ExtendedWindTurbinePowerCurveVT()
        #trb.power_rating = 1000000.0 # watts!
        trb.power_rating = self.machine_rating
        
        for i in range(nt):
            self.wt_layout.wt_list[i] = trb
        
        # show parameters
        
        if self.debug:
            sys.stderr.write('Initial Turbine Positions\n')
            for i in range(len(self.wt_layout.wt_positions)):
                sys.stderr.write('{:3d} {:.1f} {:.1f}\n'.format(i, 
                   self.wt_layout.wt_positions[i][0],self.wt_layout.wt_positions[i][1]))
            
            s = turbfuncs.wtpc_dump(self.wt_layout.wt_list[0])
            sys.stderr.write('\n' + s)
            
        #report_path = self.workDir + '/' + 'scrtest1.txt'
        #workbook_path = self.workbook_path

        # Prepare for next iteration here...
        #   - write new scripts
        #   - write new turbine files
        #   - etc.
        
        # owtg_str = turbfuncs.wtpc_to_owtg(self.turb_props)
        
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
            #self.capacity_factor = ((self.net_aep) / (self.wt_layout.wt_list[0].power_rating*0.001 * 8760.0 * self.nTurbs))
            # 8766 hrs = 365.25 days to agree with OpenWind
            self.capacity_factor = ((self.net_aep) / (self.wt_layout.wt_list[0].power_rating*0.001 * 8766.0 * self.nTurbs))
        
        self.total_losses = (self.gross_aep - self.net_aep) / self.gross_aep
        
    # -------------------
    
    def updateRptPath(self, rptPathName, newScriptName):
        '''
        Updates the output report path by writing a new script file ('newScriptName')
          that includes the new report path ('rptPathName'), then setting the value
          of ow.script_file to 'newScriptName' (with proper folder)
          
        Writes a new script file and sets self.ow.script_file
        New script is identical to current script, except that it writes to 'rptPathName'
        rptPathName should be a full path name (if possible)
        '''
        
        if self.ow is None:
            sys.stderr.write('*** WARNING: calling updateRptPath() before ow (OpenWind component) is set\n')
            return
            
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
    
    def updateAssyRptPath(self, rptPathName, newScriptName):
        '''
        Updates the output report path by writing a new script file ('newScriptName')
          that includes the new report path ('rptPathName'), then setting the value
          of self.script_file to 'newScriptName' (with proper folder)
        
        Similar to updateRptPath() but modifies self.script file, since self.ow may not be set yeet 
        '''
        
        e = rwScriptXML.parseScript(self.script_file)
        rp = e.find("ReportPath")
        if rp is None:
            sys.stderr.write('Can\'t find report path in "{:}"\n'.format(self.ow.script_file))
            return
        
        if self.debug:    
            sys.stderr.write('Changing report path from "{:}" to "{:}"\n'.format(rp.get('value'),rptPathName))
        rp.set('value',rptPathName)
        
        rwScriptXML.wrtScript(e, newScriptName)
        self.script_file = self.workDir + '/' + newScriptName
        if self.debug:    
            sys.stderr.write('Wrote new script file "{:}"\n'.format(self.script_file))
            
    # -------------------
    
    #def writeNewScript(self, scriptFileName):
    #    '''
    #      Write a new XML script to scriptFileName and use that as the active
    #      script for OpenWind
    #      Operations are: load workbook, replace turbine, energy capture, exit
    #      NOT USED
    #    '''
    #    
    #    script_tree, operations = rwScriptXML.newScriptTree(self.report_path)    
    #    # add operations to 'operations' (the 'AllOperations' tree in script_tree)
    #    
    #    rwScriptXML.makeChWkbkOp(operations,self.workbook_path)       # change workbook
    #    rwScriptXML.makeRepTurbOp(operations,turbine_name,turbine_path)  # replace turbine
    #    rwScriptXML.makeEnCapOp(operations)                # run energy capture
    #    rwScriptXML.makeExitOp(operations)                 # exit
    #    
    #    script_XML = etree.tostring(script_tree, 
    #                               xml_declaration=True, 
    #                               doctype='<!DOCTYPE OpenWindScript>',
    #                               pretty_print=True)
    #    
    #    self.ow.script_file = self.workDir + '/' + scriptFileName
    #    ofh = open(thisdir + '/' + self.ow.script_file, 'w')
    #    ofh.write(script_XML)
    #    ofh.close()
    
#------------------------------------------------------------------

def example(owExe):

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

    if not os.path.isfile(owExe):
        sys.stderr.write('OpenWind executable file "{:}" not found\n'.format(owExe))
        exit()

    # set the external optimiser flag to True so that we can use our optimizing routines
    
    acutils.owIniSet(owExe, extVal=True, debug=True)
    
    testPath = '../templates/'
    #workbook_path = testPath + 'VA_test.blb'
    workbook_path = testPath + 'owTestWkbkExtend.blb'
    
    script_file = testPath + 'owacScript.xml' # optimize operation
    if modify_turbine:
        script_file = testPath + 'rtopScript.xml' # replace turbine, optimize
        #script_file = testPath + 'rtecScript.xml' # replace turbine, energy capture
        if debug:
            sys.stderr.write('Turbine will be modified\n')

    if not os.path.isfile(script_file):
        sys.stderr.write('OpenWind script file "{:}" not found\n'.format(script_file))
        exit()
  
    # ----- Run OpenWind once to get initial turbine positions
    
    if debug:
        sys.stderr.write('\n--------- Running OpenWind to get turbine positions --------------\n')
    wt_positions, ttypes = getworkbookvals.getTurbPos(workbook_path, owExe, delFiles=False)
    if debug:
        sys.stderr.write('Initial turbine positions from workbook {:}\n'.format(workbook_path))
        for i in range(len(wt_positions)):
            sys.stderr.write("  Turb{:2d} {:.1f} {:.1f} '{:}'\n".format(i,
              wt_positions[i][0],wt_positions[i][1], ttypes[i]))
        sys.stderr.write('--------- Finished Running OpenWind to get turbine positions --------------\n\n')

    # ----- Create OW_assembly object
    
    #turbine_name = 'Alstom Haliade 150m 6MW' # should match default turbine in workbook
    #machine_rating = 6000000.0 # machine_rating and power_rating are in W
    
    turbine_name = ttypes[0] # should match default turbine in workbook
    # How to get machine_rating for this turbine?
    #   - could search all *owtg files for matching name, then get rating
    fname, machine_rating = turbfuncs.findOWTG(testPath, turbine_name)
    
    # should check for existence of both owExe and workbook_path before
    #   trying to run openwind
    
    owAsy = openwindAC_assembly(owExe, workbook_path, 
                             script_file=script_file,
                             wt_positions=wt_positions,
                             turbine_name=turbine_name, 
                             machine_rating=machine_rating,
                             start_once=start_once,
                             debug=debug) 
    
    #owAsy.configure()
    
    owAsy.updateAssyRptPath('newReport.txt', 'newTestScript.xml')
    #owAsy.updateRptPath('newReport.txt', 'newTestScript.xml')
    
    # Originally, there was a turbine power/ct/rpm definition here, but that's not
    # part of an owAsy, so that code is now in C:/SystemsEngr/test/pcrvtst.py
    
    if True:
        owa = set_as_top(owAsy)
        if debug:
            sys.stderr.write('\n*** Running top-level assembly\n')
        owa.run()
    
    else:
        owAsy.execute() # run the openWind process

    # ----- Summary
    
    print 'openwindAC_assembly results:'
    print '  Gross {:.4f} mWh'.format(owAsy.gross_aep*0.001)
    print '  Net   {:.4f} mWh'.format(owAsy.net_aep*0.001)
    print '  Total losses {:.2f} %'.format(owAsy.total_losses*100.0)
    print '  CF    {:.2f} %'.format(owAsy.capacity_factor*100.0)
    print '  Using {:} turbines with power rating of {:.3f} MW'.format(
          len(owAsy.wt_layout.wt_positions), owAsy.machine_rating/1000000.0)

if __name__ == "__main__":

    # Substitue your own path to Openwind Enterprise
    #owExe = 'C:/Models/Openwind/openWind64_ac.exe'
    #owExe = 'D:/rassess/Openwind/openWind64_ac.exe' # Old Academic v.1275
    owExe = 'D:/rassess/Openwind/openWind64.exe'
    example(owExe)
