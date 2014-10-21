# openWindComponent.py
# 2014 10 16
'''
  Execute OpenWind as an OpenMDAO Component
  
  2014 10 16: this is based on openWindAcComponent.py
    BUT: the 'academic' version of OpenWind has gone away
    The new Enterprise OW included the functions of the former academic version.
    They are enabled by setting the following line in OpenWind64.ini:
      ExternalOptimiser Yes

  __init__() has a new argument: extOpt=False
    If set to True, OWcomp will have 'academic' functionality
    
  After execute(), the following variables have been updated:
        nTurbs   
        net_aep  
        gross_aep
  They can be accessed through appropriate connections.

  NOTE: Script file must contain an Optimize/Optimise operation - otherwise,
    no results will be found.
  
  Typical use (e.g., from an Assembly):
    ow = OWcomp(owExe, scriptFile=scrptName, debug=False, stopOW=True, start_once=False, opt_log=False)
    
  main() runs OWcomp.execute() 3 times, moving and modifying the turbines each time
  
'''

import os.path

import sys, time
import subprocess
from lxml import etree

import academic.owAcademicUtils as acutils
import plant_energyse.openwind.openWindUtils as utils
import plant_energyse.openwind.rwScriptXML as rwScriptXML
import plant_energyse.openwind.rwTurbXML as rwTurbXML
import plant_energyse.openwind.turbfuncs as turbfuncs

from openmdao.lib.datatypes.api import Float, Int, VarTree
from openmdao.main.api import FileMetadata, Component, VariableTree

from fusedwind.plant_flow.vt import GenericWindTurbineVT, \
               GenericWindTurbinePowerCurveVT, ExtendedWindTurbinePowerCurveVT, \
               GenericWindFarmTurbineLayout,   ExtendedWindFarmTurbineLayout

from fusedwind.interface import implement_base
from fusedwind.plant_flow.comp import BaseAEPAggregator

#-----------------------------------------------------------------

@implement_base(BaseAEPAggregator)
class OWcomp(Component):
    """ A simple OpenMDAO component for OpenWind academic

        Args:
           owExe (str): full path to OpenWind executable
           scriptFile (str): path to XML script that OpenWind will run

     """

    # inputs
    rotor_diameter   = Float(126.0, iotype='in', units='m', desc='connecting rotor diameter to force run on change') # todo: hack for now
    availability     = Float(0.95,  iotype='in', desc='availability')
    other_losses     = Float(0.0,   iotype='in', desc='soiling losses')      
    wt_layout        = VarTree(ExtendedWindFarmTurbineLayout(), iotype='in', desc='properties for each wind turbine and layout')    
    dummyVbl         = Float(0,   iotype='in',  desc='unused variable to make it easy to do DOE runs')

    # outputs
    gross_aep        = Float(0.0, iotype='out', desc='Gross Output')
    net_aep          = Float(0.0, iotype='out', desc='Net Output')
    nTurbs           = Int(0,     iotype='out', desc='Number of turbines')
    #array_aep        = Float(0.0, iotype='out', desc='Array output - NOT USED IN ACADEMIC VERSION')
    #array_efficiency = Float(0.0, iotype='out', desc='Array Efficiency')
    #array_losses     = Float(0.0, iotype='out', desc='Array losses')
    
    def __init__(self, owExe, scriptFile=None, extOpt=False, debug=False, 
      stopOW=True, start_once=False, opt_log=False):

        """ Constructor for the OWwrapped component """

        self.debug = debug
        if self.debug:
            sys.stderr.write('\nIn {:}.__init__()\n'.format(self.__class__))
        super(OWcomp, self).__init__()

        # public variables
        
        self.input_file = 'myinput.txt'
        self.output_file = 'myoutput.txt'
        self.stderr = 'myerror.log'
        
        # external_files : member of Component class = list of FileMetadata objects
        self.external_files = [
            FileMetadata(path=self.output_file),
            FileMetadata(path=self.stderr),
        ]
        
        self.stopOW = stopOW
        self.start_once = start_once
        self.replace_turbine = False
        self.opt_log = opt_log
        self.extOpt = extOpt
        
        self.resname = '' # start with empty string
        
        self.script_file = scriptFile
        self.scriptOK = False
        if scriptFile is not None:

            # Check script file for validity and extract some path information
            self.scriptOK = self.parse_scriptFile()
            if not self.scriptOK:
                raise ValueError
                return
                
            self.scriptDict = rwScriptXML.rdScript(self.script_file, self.debug)
            if self.debug:
                sys.stderr.write('Script File Contents:\n')
                for k in self.scriptDict.keys():
                    sys.stderr.write('  {:12s} {:}\n'.format(k,self.scriptDict[k]))
        
        # Log all optimization settings?
        if self.opt_log:
            self.olname = 'owOptLog.txt'
            self.olfh = open(self.olname, 'w')
            if self.debug:
                sys.stderr.write('Logging optimization params to {:}\n'.format(self.olname))
                
        # Set the version of OpenWind that we want to use
        self.command = [owExe, self.script_file]
        
        # Keep the initial value of rotor diam so we can
        # see if it (or other turb param) has changed
        self.rtr_diam_init = self.rotor_diameter
        #  ... other params ....
        
        # Try starting OpenWind here (if self.start_once is True)
        if self.start_once:
            self.proc = subprocess.Popen(self.command)
            self.pid = self.proc.pid
            if self.debug:
                sys.stderr.write('Started OpenWind with pid {:}\n'.format(self.pid))
                sys.stderr.write('  OWComp: dummyVbl {:}\n'.format(self.dummyVbl))
        
        if self.debug:
            sys.stderr.write('\nLeaving {:}.__init__()\n\n'.format(self.__class__))
        
    #------------------ 
    
    def parse_scriptFile(self):

        # OW looks for the notify files and writes the 'results.txt' file to the 
        #   directory that contains the *blb workbook file
        # Find where the results file will be found     
        
        if not os.path.isfile(self.script_file):
            sys.stderr.write('\n*** OpenWind script file "{:}" not found\n'.format(self.script_file))
            return False

        try:
            e = etree.parse(self.script_file)
            self.rptpath = e.getroot().find('ReportPath').get('value')
        except:
            sys.stderr.write("\n*** Can't find ReportPath in {:}\n".format(self.script_file))
            self.rptpath = 'NotFound'
            return False
        
        # Make sure there's an optimize operation - otherwise OW won't find anything
        foundOpt = False
        self.replace_turbine = False
        ops = e.getroot().findall('.//Operation')
        for op in ops:
            optype = op.find('Type').get('value')
            
            if optype == 'Optimize' or optype == 'Optimise':
                foundOpt = True
                break
            if optype == 'Replace Turbine Type':
                self.replace_turbine = True
                sys.stderr.write('\n*** WARNING: start_once will be set to False because Replace Turbine\n')
                sys.stderr.write('         operation is present in {:}\n\n'.format(self.script_file))
                self.start_once = False
                
        if not foundOpt:
            sys.stderr.write('\n*** ERROR: no Optimize operation found in {:}\n\n'.format(self.script_file))
            return False
        
        if self.replace_turbine and self.start_once:
            sys.stderr.write("*** WARNING: can't use start_once when replacing turbine\n")
            sys.stderr.write("       setting start_once to False\n")
            self.start_once = False
               
        # Find the workbook folder and save as dname
        self.dname = None
        for op in ops:
            if op.find('Type').get('value') == 'Change Workbook':
                wkbk = op.find('Path').get('value')
                if not os.path.isfile(wkbk):
                    sys.stderr.write("\n*** OpenWind workbook file {:}\n  not found\n".format(wkbk))
                    sys.stderr.write("  (specified in script file {:})\n".format(self.script_file))
                    return False
                self.dname = os.path.dirname(wkbk)
                if self.debug:
                    sys.stderr.write('Working directory: {:}\n'.format(self.dname))
                break

        self.resname = '/'.join([self.dname,'results.txt'])
        
        return True
        
    #------------------ 
    
    def execute(self):
        """ Executes our component. """

        if self.debug:
            sys.stderr.write("In {0}.execute() {1}...\n".format(self.__class__, self.script_file))
        
        if (len(self.resname) < 1):
            sys.stderr.write('\n*** ERROR: OWcomp results file name not assigned! (problem with script file?)\n\n')
            return False

        # Prepare input file here
        #   - write a new script file?
        #   - write a new turbine file to overwrite the one referenced
        #       in the existing script_file?

        # If there is a turbine replacement operation in the script:
        #   write new turbine description file based on contents of first turbine in layout
        
        #if 'replturbpath' in self.scriptDict: 
        if self.replace_turbine:
            if len(self.wt_layout.wt_list) < 1:
                sys.stderr.write('\n*** ERROR ***  OWcomp::execute(): no turbines in wt_layout!\n\n')
                return False
            if self.debug:
                sys.stderr.write('Replacement turbine parameters:\n')
                #sys.stderr.write('{:}\n'.format(turbfuncs.wtpc_dump(self.wt_layout.wt_list[0])))
                sys.stderr.write('{:}\n'.format(turbfuncs.wtpc_dump(self.wt_layout.wt_list[0], shortFmt=True)))
                #sys.stderr.write('{:}\n'.format(wtlDump(self.wt_layout.wt_list[0])))
                
            newXML = turbfuncs.wtpc_to_owtg(self.wt_layout.wt_list[0], 
                                            trbname='ReplTurb', 
                                            desc='OWcomp replacement turbine')
            if len(newXML) > 50:
                tfname = self.scriptDict['replturbpath'] # this is the file that will be overwritten with new turbine parameters
                tfh = open(tfname, 'w')
                tfh.write(newXML)
                tfh.close()
                maxPower = self.wt_layout.wt_list[0].power_rating
                if self.debug:
                    sys.stderr.write('Wrote new turbine file to {:} (rated pwr {:.2f} MW\n'.format(tfname, maxPower*0.000001))
            else:
                sys.stderr.write('*** NO new turbine file written\n')
            
        # Execute the component and save process ID
        if not self.start_once:
            self.proc = subprocess.Popen(self.command)
            self.pid = self.proc.pid
            if self.debug:
                sys.stderr.write('Started OpenWind with pid {:}\n'.format(self.pid))
                sys.stderr.write('  OWComp: dummyVbl {:}\n'.format(self.dummyVbl))
                #sys.stderr.write('Report Path: {:}\n'.format(self.rptpath))

            # Watch for 'results.txt', meaning that OW has run once with the default locations 
            
            if self.debug:
                sys.stderr.write('OWComp waiting for {:} (first run -  positions unchanged)\n'.format(self.resname))
            acutils.waitForNotify(watchFile=self.resname, path=self.dname, debug=False, callback=self.getCBvalue)

        # Now OW is waiting for a new position file
        # Write new positions and notify file - this time it should use updated positions

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
                sys.stderr.write('OWComp waiting for {:} (modified positions)\n'.format(self.resname))
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
            return False
        
        # Set the output variables
        #   - array_aep is not available from Academic 'results.txt' file
        self.nTurbs = len(netNRGturb)
        self.net_aep = netEnergy
        self.gross_aep = sum(grossNRGturb)
        if self.debug:
            sys.stderr.write('{:}\n'.format(self.dump()))
        
        # Log optimization values
        if self.opt_log:
            self.olfh.write('{:3d} G {:.4f} N {:.4f} XY '.format(self.exec_count, self.gross_aep, self.net_aep))
            for ii in range(len(wt_positions)):
                self.olfh.write('{:8.1f} {:9.1f} '.format(self.wt_layout.wt_positions[ii][0], self.wt_layout.wt_positions[ii][1]))
            self.olfh.write('\n')
                
        if not self.start_once and self.stopOW:
            if self.debug:
                sys.stderr.write('Stopping OpenWind with pid {:}\n'.format(self.pid))
            self.proc.terminate()
            
        self.checkReport() # check for execution errors

        if self.debug:
            sys.stderr.write("Leaving {0}.execute() {1}...\n\n".format(self.__class__, self.script_file))

    #------------------ 
    
    def parse_results_no_extopt():
        ''' parse the results of an OpenWind run WITHOUT external optimization '''
        
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

    #------------------ 
    
    def terminateOW(self):
        ''' Terminate the OpenWind process '''
        if self.debug:
            sys.stderr.write('Stopping OpenWind with pid {:}\n'.format(self.pid))
        self.proc.terminate()

    #------------------ 
    
    def checkReport(self):
        ''' check the report file for errors '''
        
        fname = self.scriptDict['rptpath']
        if self.debug:
            sys.stderr.write('checkReport : {:}\n'.format(fname))
        fh = open(fname, 'r')
        for line in fh.readlines():
            if line.startswith('Failed to find and replace turbine type'):
                sys.stderr.write('\n*** ERROR: turbine replacement operation failed\n')
                sys.stderr.write('    Replace {:}\n'.format(self.scriptDict['replturbname']))
                sys.stderr.write('    with    {:}\n'.format(self.scriptDict['replturbpath']))
                sys.stderr.write('\n')
                
        fh.close()
        
#------------------------------------------------------------------

def dummy_wt_list():
    wtl = ExtendedWindTurbinePowerCurveVT()
    nv = 20
    
    wtl.hub_height = 100.0
    wtl.rotor_diameter = 90.0
    wtl.power_rating = 3.0
    wtl.rpm_curve   = [ [float(i), 10.0] for i in range(nv) ]
    wtl.pitch_curve = [ [float(i),  0.0] for i in range(nv) ]
    wtl.c_t_curve   = [ [float(i), 10.0] for i in range(nv) ]
    wtl.power_curve = [ [float(i), 10.0] for i in range(nv) ]
    return wtl

#------------------------------------------------------------------

def wtlDump(wtl):
    wstr = 'WTL: pclen {:}'.format(len(wtl.c_t_curve))
    return wstr
        
#------------------------------------------------------------------

''' OWComp.wt_layout is a ExtendedWindFarmTurbineLayout(VariableTree) and has
      wt_list = List(ExtendedWindTurbinePowerCurveVT(), desc='The wind turbine list of descriptions [n_wt]')
      wt_positions = Array(units='m', desc='Array of wind turbines attached to particular positions [n_wt, 2]')
      (among others)

    We use wt_positions to move the turbines - we update the values and copy them to 
      file 'positions.txt' at each iteration using writePositionFile()
      (ow.wt_layout.wt_positions and wt_positions are 2 copies of the same data)
      
    If we are replacing the turbines, we use wt_list to hold the modified turbine.
      We initialize wt_layout.wt_list with copies of the values in base_turbine_file.
      At each iteration, we tweak the values in wt_layout.wt_list.
        When OWComp.execute runs, it writes a new turbine file
          using the values in wt_layout.wt_list[0]
        This turbine file is the same one specified in the script: 
          <TurbinePath value="../templates/ReplTurb.owtg"/>
        When OpenWind runs the Replace Turbine operation, it looks for all turbines whose name matches
          the value in <TurbineName value="NREL 5MW"/> and replaces them with the turbine described in
          file <TurbinePath>

    Does the base_turbine_file need to match the default turbine in the workbook?
    How can we get that name?
      - run OW energy capture, scan file
      - but scripted energy capture doesn't have full description of turbine
          
'''

def example(owExe):

    debug = False
    start_once = False
    modify_turbine = False
    opt_log = False
    extOpt = False
    
    for arg in sys.argv[1:]:
        if arg == '-debug':
            debug = True
        if arg == '-once':
            start_once = True
        if arg == '-log':
            opt_log = True
        if arg == '-modturb':
            modify_turbine = True
        if arg == '-extopt':
            extOpt = True
        if arg == '-help':
            sys.stderr.write('USAGE: python openWindComponent.py [-once] [-debug] [-modturb] [-extopt]\n')
            exit()
    
    # Find OpenWind executable
    if not os.path.isfile(owExe):
        sys.stderr.write('OpenWind executable file "{:}" not found\n'.format(owExe))
        exit()

    # set the external optimiser flag to extOpt:
    #    True : can use our optimizing routines
    acutils.owIniSet(owExe, extVal=extOpt, debug=True)
    
    # If we are not externally optimizing, we can start OW once and let it run to completion
    
    if not extOpt:
        start_once = True
        
    # Set OpenWind script name
    testpath = 'templates/'
    #owXMLname = testpath + 'rtecScript.xml' # replace turb, energy capture #KLD - this script does not work for me with this component
    owXMLname = testpath + 'owScript.xml' # optimize operation
    #owXMLname = testpath + 'rtopScript.xml' # replace turb, optimize
    
    if modify_turbine:
        owXMLname = testpath + 'rtopScript.xml' # replace turb, optimize
        
    if not os.path.isfile(owXMLname):
        sys.stderr.write('OpenWind script file "{:}" not found\n'.format(owXMLname))
        exit()
    
    dscript = rwScriptXML.rdScript(owXMLname,debug=debug) # Show our operations
    workbook = dscript['workbook']
    
    # default turbine positions and size of translation
    
    wt_positions = [[456000.00,4085000.00],
                    [456500.00,4085000.00]]
    deltaX =  3000.0
    deltaY = -2000.0
    #deltaX =  200.0
    #deltaY = -200.0
    deltaX =  3.000
    deltaY = -2.000
    
    # Read turbine positions from workbook
    if debug:
        sys.stderr.write('Getting turbine positions from {:}\n'.format(workbook))        
    wb = acutils.WTWkbkFile(wkbk=workbook, owexe=owExe)
    wt_positions = wb.xy
    if debug:
        sys.stderr.write('Got {:} turbine positions\n'.format(len(wt_positions)))        
    
    # Initialize OWcomp component
    ow = OWcomp(owExe=owExe, debug=debug, scriptFile=owXMLname, 
                extOpt=extOpt,
                start_once=start_once, opt_log=opt_log) #, stopOW=False)

    if not ow.scriptOK:
        sys.stderr.write("\n*** ERROR found in script file\n\n")
        exit()
    
    # starting point for turbine mods
    #wt_list_elem = dummy_wt_list()    
    base_turbine_file = testpath + 'NREL5MW.owtg'
    wt_list_elem = turbfuncs.owtg_to_wtpc(base_turbine_file)
    
    if not extOpt:
        # If we're not optimizing externally, run ow and return
        
        ow.execute()
        
        print '\nFinal values'
        owd = ow.dump()
        print '  {:}'.format(owd)
        print '-' * 40, '\n'
        
        return
    
    # external optimization
            
    ow.wt_layout.wt_list = [ wt_list_elem for i in range(len(wt_positions)) ]
    if debug:
        sys.stderr.write('Initialized {:} turbines in wt_layout\n'.format(len(wt_positions)))
    
    # With each iteration
    #   move turbines farther offshore 
    #   possibly modify the turbine rotor diam and power curve and replace turbine
    
    if debug:
        ofh = open('wtp.txt', 'w')
        
    for irun in range(1,4):
        for i in range(len(wt_positions)):
            wt_positions[i][0] += deltaX
            wt_positions[i][1] += deltaY
            if debug:
                ofh.write('{:2d} {:3d} {:.1f} {:.1f}\n'.format(irun, i, wt_positions[i][0], wt_positions[i][1]))
        ow.wt_layout.wt_positions = wt_positions
        
        # modify the turbine
        ow.rotor_diameter += 1.0
        if ow.replace_turbine:
            wt_list_elem = ow.wt_layout.wt_list[0]
            wt_list_elem.power_rating *= 1.05
            for i in range(len(wt_list_elem.power_curve)):
                wt_list_elem.power_curve[i][1] *= 1.05
            ow.wt_layout.wt_list = [wt_list_elem for i in range(len(ow.wt_layout.wt_list)) ]
            if debug:
                ofh.write('Updated {:} turbines with:\n'.format(len(ow.wt_layout.wt_list)))
                ofh.write(turbfuncs.wtpc_dump(ow.wt_layout.wt_list[0]))
        
        ow.execute() # run the openWind process
        
        print '\nFinal values'
        owd = ow.dump()
        print '  {:}'.format(owd)
        print '-' * 40, '\n'

    if start_once:
        ow.terminateOW()

if __name__ == "__main__":

    # Substitute your own path to Openwind Enterprise
    #owExe = 'C:/Models/Openwind/openWind64_ac.exe'
    owExe = 'D:/rassess/Openwind/openWind64_ac.exe' # Old Academic v.1275
    owExe = 'D:/rassess/Openwind/openWind64.exe'
    example(owExe)