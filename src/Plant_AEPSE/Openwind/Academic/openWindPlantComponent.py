# openWindPlantComponent.py
# 2014 04 15
''' Create plants and layouts from files, OpenWind workbooks, etc. '''

import sys, os
import numpy as np

from openmdao.lib.datatypes.api import VarTree, Float, Slot, Array, List, Int, Str, Dict, Enum
from openmdao.main.api import FileMetadata, Component

from fused_plant_vt import GenericWindTurbineVT, GenericWindTurbinePowerCurveVT, \
                           ExtendedWindTurbinePowerCurveVT, GenericWindFarmTurbineLayout
from fused_plant_comp import GenericWSPosition, HubCenterWSPosition, GenericWakeSum, GenericHubWindSpeed, \
                             GenericFlowModel, GenericWakeModel, GenericInflowGenerator, \
                             WindTurbinePowerCurve, PostProcessWindRose, PlantFromWWH, \
                             WindRoseCaseGenerator, PostProcessSingleWindRose, PostProcessMultipleWindRoses

import Plant_AEPSE.Openwind.Academic.owAcademicUtils as acutils
import Plant_AEPSE.Openwind.openWindUtils as utils

#-----------------------------------------------------------

class PlantFromPosFile(Component):
    ''' Create a plant from a 'positions.txt' file '''
    
    ### Inputs
    filename = Str(iotype='in', desc='The positions file name')

    ### Outputs
    wt_layout = VarTree(GenericWindFarmTurbineLayout(), 
                        iotype='out',
                        desc='wind turbine properties and layout')
    wind_rose_array = Array(iotype='out', 
                            desc='Windrose array [directions, frequency, weibull_A, weibull_k]', 
                            unit='m/s')

    def __init__(self, debug=False):
        super(PlantFromPosFile, self).__init__()
        self.debug = debug

    def execute(self):
        ### Reading the positions file
        wtp = acutils.WTPosFile(filename=self.filename, debug=self.debug)
        
        self.wt_layout.wt_positions = np.zeros([wtp.xy.shape[0],2])
        for i in range(wtp.xy.shape[0]):
            self.wt_layout.wt_positions[i,:] = wtp.xy[i]

        #self.wt_layout.wt_list.append(self.wt_desc)
        self.wt_layout.configure_single()
        
        #
        #for wt, wr in self.wwf.windroses.iteritems():
        #    self.wt_layout.wt_positions[i,:] = self.wwf.data[wt][:2]
        #    self.wt_layout.wt_wind_roses.append(wr)
        #    i += 1
        #
        #self.wt_layout.configure_single()
        ## For practical reason we also output the first wind rose array outside the wt_layout
        #self.wind_rose_array = self.wt_layout.wt_wind_roses[0]

    def dump(self):
        sys.stderr.write('WTPosFile dump:\n  filename: {:}\n'.format(self.filename))
        for i in range(self.wt_layout.wt_positions.shape[0]):
            sys.stderr.write('  {:2d} {:.1f} {:.1f}\n'.format(i, 
                self.wt_layout.wt_positions[i,0], self.wt_layout.wt_positions[i,1]))
        
#-----------------------------------------------------------

class PlantFromOWWorkbook(Component):
    ''' Create a plant from an OpenWind workbook '''
    
    ### Inputs
    wbname = Str(iotype='in', desc='The workbook file name')

    ### Outputs
    wt_layout = VarTree(GenericWindFarmTurbineLayout(), iotype='out', desc='wind turbine properties and layout')
    wind_rose_array = Array(iotype='out', desc='Windrose array [directions, frequency, weibull_A, weibull_k]', unit='m/s')

    def __init__(self, wkbk=None, owexe=None, debug=False):
        super(PlantFromOWWorkbook, self).__init__()
        self.debug = debug
    #    self.wkbk = wkbk
    #    self.owexe = owexe
    #    print self.wt_layout.__class__
        
    def execute(self):
        ### Reading the positions file
        wkb = acutils.WTWkbkFile(self.wkbk, self.owexe, debug=self.debug)
        wkb._read()
        xy = wkb.xy
        
        self.wt_layout.wt_positions = np.zeros([xy.shape[0],2])
        for i in range(wkb.xy.shape[0]):
            self.wt_layout.wt_positions[i,:] = wkb.xy[i]

        #self.wt_layout.wt_list.append(self.wt_desc)
        self.wt_layout.configure_single()
        
        #
        #for wt, wr in self.wwf.windroses.iteritems():
        #    self.wt_layout.wt_positions[i,:] = self.wwf.data[wt][:2]
        #    self.wt_layout.wt_wind_roses.append(wr)
        #    i += 1
        #
        #self.wt_layout.configure_single()
        ## For practical reason we also output the first wind rose array outside the wt_layout
        #self.wind_rose_array = self.wt_layout.wt_wind_roses[0]

    def dump(self):
        sys.stderr.write('PlantFromOWWorkbook dump:\n  filename: {:}\n'.format(self.wkbk))
        for i in range(self.wt_layout.wt_positions.shape[0]):
            sys.stderr.write('  {:2d} {:.1f} {:.1f}\n'.format(i, 
                self.wt_layout.wt_positions[i,0], self.wt_layout.wt_positions[i,1]))
        
#------------------------------------------------------------------

if __name__ == "__main__":

    debug = False
    for arg in sys.argv[1:]:
        if arg == '-debug':
            debug = True

    print '\n-------------------- Test Position.txt file ----------\n'
    
    ppf = PlantFromPosFile(debug=debug)
    ppf.filename = '../../test/defaultPositions.txt'
    
    ppf.execute()
    ppf.dump()

    print '\n-------------------- Test Workbook ----------\n'
    
    #wbname = 'C:/SystemsEngr/Test/VA_test.blb'
    wbname = '../../test/VA_test.blb'
    
    from Plant_AEPSE.Openwind.findOW import findOW
    owexe = findOW(debug=debug)
    #owexe = 'C:/rassess/OpenWind/Openwind64.exe'
      
    #pwb = PlantFromOWWorkbook(wkbk=wbname, owexe=owexe)  
    pwb = PlantFromOWWorkbook(debug=debug)
    pwb.wkbk=wbname
    pwb.owexe=owexe
    
    pwb.execute()
    pwb.dump()
    