# wtlayoutComponents.py
# 2014 05 26
''' simple OpenMDAO components for modifying wt_positions and wt_list
    Components communicate through wt_layout and wt_layout_out
    which should be connected in calling assembly
    
    To use these as templates for other components:
      - replace inputs deltaX/deltaY in WTPupdate with appropriate inputs
      - replace input pwrFactor in WTLupdate with appropriate inputs
      - replace code that modifies wt_layout_out as needed
      
'''

import sys, os

import openwind.openWindUtils as utils
import owAcademicUtils as acutils
import openwind.turbfuncs as turbfuncs

from openmdao.lib.datatypes.api import Float, Int, VarTree
from openmdao.main.api import FileMetadata, Component, VariableTree

# path needed for old fused-wind
#sys.path.append('D:/SystemsEngr/FUSED-Wind/fusedwind/src/fusedwind/plant_flow')

#from fusedwind.plant_flow.fused_plant_vt import GenericWindTurbineVT, 
#from fused_plant_vt import GenericWindTurbineVT, \
#                                                GenericWindTurbinePowerCurveVT, \
#                                                ExtendedWindTurbinePowerCurveVT, \
#                                                GenericWindFarmTurbineLayout
from vt import GenericWindTurbineVT, GenericWindTurbinePowerCurveVT, \
     ExtendedWindTurbinePowerCurveVT, GenericWindFarmTurbineLayout, \
     ExtendedWindFarmTurbineLayout, GenericWindRoseVT

#-----------------------------------------------------------------

class WTPupdate(Component):
    ''' Modify the wt_positions element of a wt_layout 
        Test: shift entire layout by deltaX/deltaY
    '''
    
    wt_layout        = VarTree(ExtendedWindFarmTurbineLayout(), iotype='in', desc='properties for each wind turbine and layout')
    wt_layout_out    = VarTree(ExtendedWindFarmTurbineLayout(), iotype='out', desc='properties for each wind turbine and layout')
    deltaX           = Float(iotype='in', desc='increment in X direction (east)')
    deltaY           = Float(iotype='in', desc='increment in Y direction (north)')
        
    def __init__(self, debug=False, wt_positions=None):

        self.debug = debug
        if self.debug:
            sys.stderr.write('\nIn {:}.__init__()\n'.format(self.__class__))
            
        super(self.__class__, self).__init__()
        
        if wt_positions is not None:
            nt = len(wt_positions)
            
            if self.debug:
                sys.stderr.write('Creating {:} with {:} turbines\n'.format( self.wt_layout.__class__, nt))
            
            # create generic wt_layout[_out]
            
            # wt_list : turbine types
            
            base_turbine_file = '../test/Alstom6MW.owtg'
            wt_list_elem = turbfuncs.owtg_to_wtpc(base_turbine_file)
            self.wt_layout.wt_list = [wt_list_elem for i in range(nt) ]
            self.wt_layout_out.wt_list = [wt_list_elem for i in range(nt) ]
            
            # wt_positions : turbine positions
            
            self.wt_layout.wt_positions = [ [0.0, 0.0] for i in range(nt) ]
            self.wt_layout_out.wt_positions = [ [0.0, 0.0] for i in range(nt) ]

            for i in range(nt):
                self.wt_layout.wt_positions[i][0] = wt_positions[i][0]
                self.wt_layout.wt_positions[i][1] = wt_positions[i][1]
                self.wt_layout_out.wt_positions[i][0] = wt_positions[i][0]
                self.wt_layout_out.wt_positions[i][1] = wt_positions[i][1]
                
    #------------------ 
    
    def execute(self):
        """ Executes our component. """

        if self.debug:
            sys.stderr.write("  In {0}.execute()...\n".format(self.__class__))
        nt = len(self.wt_layout.wt_positions)
        
        if nt < 1:
            sys.stderr.write('{:} : no turbines in layout\n'.format(self.__class__))
        
        # test:    
        #   Move each turbine by deltaX/deltaY
        #   Copy the turbine types (wt_list)
        
        for i in range(nt):
            self.wt_layout_out.wt_positions[i][0] = self.wt_layout.wt_positions[i][0] + self.deltaX
            self.wt_layout_out.wt_positions[i][1] = self.wt_layout.wt_positions[i][1] + self.deltaY
            
            self.wt_layout_out.wt_list[i] = self.wt_layout.wt_list[i] # copy wt_list - do not change this
                
#-----------------------------------------------------------------

class WTLupdate(Component):
    ''' Modify the wt_list (turbine description) element of a wt_layout 
        Test: multiply the power curve by pwrFactor
    '''
    
    wt_layout        = VarTree(ExtendedWindFarmTurbineLayout(), iotype='in', desc='properties for each wind turbine and layout')
    wt_layout_out    = VarTree(ExtendedWindFarmTurbineLayout(), iotype='out', desc='properties for each wind turbine and layout')
    pwrFactor        = Float(iotype='in', desc='multiplier for turbine power')
        
    def __init__(self, debug=False, nturb=None, turbfile=None):

        self.debug = debug
        if self.debug:
            sys.stderr.write('\nIn {:}.__init__()\n'.format(self.__class__))
        super(self.__class__, self).__init__()
        
        self.replturbpath = None
        
        if nturb is not None and turbfile is not None:
            if self.debug:
                sys.stderr.write('Initializing {:} turbines\n'.format(nturb))
            # initialize from file
            wt_list_elem = turbfuncs.owtg_to_wtpc(turbfile)
            self.wt_layout.wt_list = [wt_list_elem for i in range(nturb) ]
              
    #------------------ 
    
    def execute(self):
        """ Executes our component. """

        if self.debug:
            sys.stderr.write("  In {0}.execute()...\n".format(self.__class__))
        nt = len(self.wt_layout.wt_positions)
        
        if nt < 1:
            sys.stderr.write('{:} : no turbines in layout\n'.format(self.__class__))
            
        # Copy the turbine positions and
        #   modify the turbine types
        
        self.wt_layout_out.wt_positions = [ [0.0, 0.0] for i in range(nt) ]
        self.wt_layout_out.wt_list = [ None for i in range(nt) ]
        for i in range(nt):
            self.wt_layout_out.wt_positions[i][0] = self.wt_layout.wt_positions[i][0]
            self.wt_layout_out.wt_positions[i][1] = self.wt_layout.wt_positions[i][1]
            self.wt_layout_out.wt_list[i] = self.wt_layout.wt_list[i]  # copy without modification
        
        # do some turbine mods here
        
        # test :
        #   take first wt_list from wt_layout
        #   multiply by pwrFactor
        #   replace all wt_layout_out.wt_list elements with modified wt_list
        
        if len(self.wt_layout.wt_list) < 1:
            sys.stderr.write('\n*** WTLupdate: wt_list has not been initialized\n\n')
            return
            
        wte = self.wt_layout.wt_list[0]
        wte.power_rating *= self.pwrFactor
        for i in range(len(wte.power_curve)):
            wte.power_curve[i][1] *= self.pwrFactor
        self.wt_layout_out.wt_list = [wte for i in range(nt) ]
    
#------------------------------------------------------------------

if __name__ == "__main__":

    debug = False
    for arg in sys.argv[1:]:
        if arg == '-debug':
            debug = True
        if arg == '-help':
            sys.stderr.write('USAGE: python wtlayoutComponents.py [-debug]\n')
            exit()
        
    # default turbine positions and size of translation
    
    wt_positions = [[456000.00,4085000.00],
                    [456500.00,4085000.00]]

    # Test WTPupdate
    
    wtp = WTPupdate(debug=debug, wt_positions=wt_positions)
    wtp.execute()

    # Test WTLupdate
    
    wtl = WTLupdate(debug=debug, nturb=len(wt_positions), turbfile='../test/Alstom6MW.owtg')
    wtl.pwrFactor = 1.1
    
    # for testing, we need to initialize the wt_positions in wtl
    # (In an assembly, these would be connected to the output of wtp)
    
    nt = len(wt_positions)
    wtl.wt_layout.wt_positions = [ [0.0, 0.0] for i in range(nt) ]
    wtl.wt_layout_out.wt_positions = [ [0.0, 0.0] for i in range(nt) ]

    for i in range(nt):
        wtl.wt_layout.wt_positions[i][0] = wt_positions[i][0]
        wtl.wt_layout.wt_positions[i][1] = wt_positions[i][1]
        
    wtl.execute()
    for i in range(len(wtl.wt_layout_out.wt_list)):
        print '{:} {:.1f} kW'.format(i, 0.001*wtl.wt_layout_out.wt_list[i].power_rating)

##-----------------------------------------------------------------
#
#class WTPMcomp(Component):
#    # original testing function
#    
#    wt_layout        = VarTree(GenericWindFarmTurbineLayout(), iotype='in', desc='properties for each wind turbine and layout')
#    wt_layout_out    = VarTree(GenericWindFarmTurbineLayout(), iotype='out', desc='properties for each wind turbine and layout')
#    deltaX           = Float(iotype='in', desc='increment in X direction (east)')
#    deltaY           = Float(iotype='in', desc='increment in Y direction (north)')
#    f_xy             = Float(iotype='out', desc='dummy output variable')
#        
#    def __init__(self, debug=False):
#
#        self.debug = debug
#        if self.debug:
#            sys.stderr.write('\nIn {:}.__init__()\n'.format(self.__class__))
#        super(self.__class__, self).__init__()
#        
#    #------------------ 
#    
#    def execute(self):
#        """ Executes our component. """
#
#        if self.debug:
#            sys.stderr.write("  In {0}.execute()...\n".format(self.__class__))
#        nt = len(self.wt_layout.wt_positions)
#        deltaX = 2000.0
#        deltaY = -3000.0
#        
#        # Move each turbine by deltaX/deltaY
#        
#        for i in range(nt):
#            self.wt_layout_out.wt_positions[i][0] = self.wt_layout.wt_positions[i][0] + deltaX
#            self.wt_layout_out.wt_positions[i][1] = self.wt_layout.wt_positions[i][1] + deltaY
#        
#        self.f_xy = self.deltaX + self.deltaY
#
#        
#
    #deltaX =  3000.0
    #deltaY = -2000.0
    #
    ## Initialize WTPMcomp component
    #    
    #wtpm = WTPMcomp(debug=debug)
    #
    ## starting point for turbine mods
    #
    #base_turbine_file = '../../test/Alstom6MW.owtg'
    #base_turbine = turbfuncs.owtg_to_wtpc(base_turbine_file)
    #wt_list_elem = base_turbine
    #    
    #wt_list = [wt_list_elem for i in range(len(wt_positions)) ]
    #wtpm.wt_layout.wt_list = wt_list
    #if debug:
    #    sys.stderr.write('Initialized {:} turbines in wt_layout\n'.format(len(wt_positions)))
    #
    ## move turbines farther offshore with each iteration
    #
    #if debug:
    #    ofh = open('wtp.txt', 'w')
    #    
    ##for irun in range(1,5):
    ##    for i in range(len(wt_positions)):
    ##        wt_positions[i][0] += deltaX
    ##        wt_positions[i][1] += deltaY
    ##        if debug:
    ##            ofh.write('{:2d} {:3d} {:.1f} {:.1f}\n'.format(irun, i, wt_positions[i][0], wt_positions[i][1]))
    ##    wtpm.wt_layout.wt_positions = wt_positions
    ##    wtpm.execute() 
        
    #wtpm.wt_layout.wt_positions = wt_positions
    #wtpm.wt_layout_out.wt_positions = wt_positions
    #for irun in range(1,5):
    #    wtpm.execute()
    #    wtpm.wt_layout = wtpm.wt_layout_out 
    #    if debug:
    #        for i in range(len(wt_positions)):
    #            ofh.write('{:2d} {:3d} {:.1f} {:.1f}\n'.format(irun, 
    #              i, wtpm.wt_layout.wt_positions[i][0], wtpm.wt_layout.wt_positions[i][1]))
