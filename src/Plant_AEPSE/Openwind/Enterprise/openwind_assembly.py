# openWindComp.py
# 2013 03 15
''' Run openWind from openMDAO 
    2013 03 15: G. Scott
    2013 06 07: GNS - revisions
    
    Requires
    --------
    ElementTree (should be part of Python distribution)
    
'''

import sys, os
import subprocess
import xml.etree.ElementTree as ET

from openmdao.main.api import Component, Assembly, VariableTree
from openmdao.lib.datatypes.api import Float, Array, Int, VarTree

from fusedwind.plant_flow.fused_plant_asym import GenericAEPModel
from fusedwind.plant_flow.fused_plant_vt import GenericWindTurbinePowerCurveVT, GenericWindFarmTurbineLayout

from openWindExtCode import OWwrapped

import wrtTurbXML
from lxml import etree
import wrtScriptXML

import numpy as np

#------------------------------------------------------------------

class openwind_assembly(GenericAEPModel): # todo: has to be assembly or manipulation and passthrough of aep in execute doesnt work
    """ Runs OpenWind from OpenMDAO framework """

    # Inputs
    hub_height = Float(90.0, iotype='in', desc='turbine hub height', unit='m')
    rotor_diameter = Float(126.0, iotype='in', desc='turbine rotor diameter', unit='m')
    power_curve = Array([], iotype='in', desc='wind turbine power curve')
    rpm = Array([], iotype='in', desc='wind turbine rpm curve')
    ct = Array([], iotype='in', desc='wind turbine ct curve')
    turbine_number = Int(100, iotype='in', desc='plant number of turbines')
    machine_rating = Float(5000.0, iotype='in', desc='wind turbine rated power', unit='kW')
    availability = Float(0.941, iotype='in', desc='wind plant availability')
    wt_layout = VarTree(GenericWindFarmTurbineLayout(), iotype='in', desc='properties for each wind turbine and layout')    
    other_losses = Float(0.0, iotype='in', desc='wind plant losses due to blade soiling, etc')
    # TODO: loss inputs
    # TODO: wake model option selections

    # Outputs
    #ideal_aep = Float(0.0, iotype='out', desc='Ideal Annual Energy Production before topographic, availability and loss impacts', unit='kWh')
    array_aep = Float(0.0, iotype='out', desc='Gross Annual Energy Production net of array impacts', unit='kWh')
    array_losses = Float(0.0, iotype='out', desc='Array Losses')
    capacity_factor = Float(0.0, iotype='out', desc='capacity factor')

    # -------------------
    
    def __init__(self, openwind_executable, workbook_path, turbine_name):
        """ Creates a new LCOE Assembly object """

        self.openwind_executable = openwind_executable
        self.workbook_path = workbook_path
        self.turbine_name = turbine_name
        super(openwind_assembly, self).__init__()

        # TODO: hack for now assigning turbine
        self.turb = GenericWindTurbinePowerCurveVT()
        self.turb.power_rating = self.machine_rating
        self.turb.hub_height = self.hub_height
        self.turb.power_curve = np.copy(self.power_curve)
        for i in xrange(0,self.turbine_number):
            self.wt_layout.wt_list.append(self.turb)

    def configure(self):
        """ Add Openwind external code component """

        super(openwind_assembly, self).configure()        
        
        ow = OWwrapped(self.openwind_executable)
        self.add('ow', ow)
        
        self.driver.workflow.add(['ow'])
        
        self.connect('rotor_diameter', 'ow.rotor_diameter') # todo: hack to force external code execution
        self.connect('other_losses', 'ow.other_losses')
        self.connect('availability', 'ow.availability')
        
        self.connect('ow.array_losses', 'array_losses')
        self.connect('ow.gross_aep', 'gross_aep')
        self.connect('ow.array_aep', 'array_aep')
        self.connect('ow.net_aep', 'net_aep')
    
    def execute(self):
        """
            Set up XML and run OpenWind
            This will leave OW running - use the File/Exit button to shut it down until
              Nick comes up with a way to stop it from the script.
        """

        print "In {0}.execute()...".format(self.__class__)

        # Set up turbine to write to xml
        power = []
        for i in xrange(0,4):
          power.append(0.0)
        counter = 5.0
        for i in xrange(5,26):
          myi = min(range(self.power_curve.shape[1]), key=lambda i: abs(self.power_curve[0][i]-counter))
          power.append(self.power_curve[1][myi])
          counter += 1.0 
        power.append(self.power_curve[1][-1])

        thrust = []
        for i in xrange(0,4):
          thrust.append(1.0)
        counter = 5.0
        for j in xrange(5,26):
          myi = min(range(self.ct.shape[1]), key=lambda i: abs(self.ct[0][i]-counter))
          thrust.append(self.ct[1][myi])
          counter += 1.0
        thrust.append(self.ct[1][0])
        
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
        turbtree = wrtTurbXML.getTurbTree(turbine_name, desc, power, thrust, self.hub_height, self.rotor_diameter,\
                                         percosts, cut_in_wind_speed, cut_out_wind_speed, blade_number, self.machine_rating, turbine_cost, foundation_cost)
        turbXML = etree.tostring(turbtree, 
                                 xml_declaration=True,
                                 doctype='<!DOCTYPE {:}>'.format(turbine_name), 
                                 pretty_print=True)

        thisdir = os.path.dirname(os.path.realpath(__file__))   
    
        ofh = open(thisdir + '/' + 'Turbine_Model.owtg', 'w')
        ofh.write(turbXML)
        ofh.close()
    
        # write new script for execution  
        report_path = thisdir + '/' + 'scrtest1.txt'
        workbook_path = self.workbook_path
        turbine_name = self.turbine_name
        turbine_path = thisdir + '/' + 'Turbine_Model.owtg'
    
        script_tree, operations = wrtScriptXML.getScriptTree(report_path)    
        # add operations to 'operations' (the 'AllOperations' tree in script_tree)
        
        wrtScriptXML.makeChWkbkOp(operations,workbook_path)       # change workbook
        wrtScriptXML.makeRepTurbOp(operations,turbine_name,turbine_path)  # replace turbine
        wrtScriptXML.makeEnCapOp(operations)                # run energy capture
        wrtScriptXML.makeExitOp(operations)                 # exit
        
        script_XML = etree.tostring(script_tree, 
                                   xml_declaration=True, 
                                   doctype='<!DOCTYPE OpenWindScript>',
                                   pretty_print=True)
        
        ofh = open(thisdir + '/' + 'OpenWind_Script.xml', 'w')
        ofh.write(script_XML)
        ofh.close()
    
        self.ow.script_file = thisdir + '/' + 'OpenWind_Script.xml'

        # will actually run the workflow
        super(openwind_assembly, self).execute()

        # calculate capacity factor
        self.capacity_factor = ((self.net_aep) / (self.wt_layout.wt_list[0].power_rating * 8760.0 * len(self.wt_layout.wt_list)))
        
    
#------------------------------------------------------------------

def example():

    # simple test of module
    owExeV1130 = 'C:/Models/Openwind/OpenWind64.exe'
    workbook_path = 'C:/Models/OpenWind/Workbooks/OpenWind_Model.blb'
    turbine_name = 'NREL 5 MW'
    ow = openwind_assembly(owExeV1130, workbook_path, turbine_name)
    
    ow.power_curve = np.array([[1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, \
                           11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0, 21.0, 22.0, 23.0, 24.0, 25.0, 26.0], \
                          [0.0, 0.0, 0.0, 187.0, 350.0, 658.30, 1087.4, 1658.3, 2391.5, 3307.0, \
                          4415.70, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, \
                          5000.0, 5000.0, 5000.0, 5000.0, 0.0]])

    ow.ct = np.array([[1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, \
                           11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0, 21.0, 22.0, 23.0, 24.0, 25.0, 26.0], \
                          [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, \
                           1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]])

    ow.rpm = np.array([[1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, \
                           11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0, 21.0, 22.0, 23.0, 24.0, 25.0, 26.0], \
                          [7.0, 7.0, 7.0, 7.0, 7.0, 7.0, 7.0, 7.0, 7.0, 7.0, \
                           7.0, 7.0, 7.0, 7.0, 7.0, 7.0, 7.0, 7.0, 7.0, 7.0, 7.0, 7.0, 7.0, 7.0, 7.0, 7.0]])

    ow.execute() # run the openWind process

    print 'Gross {:.4f} kWh'.format(ow.gross_aep)
    print 'Array {:.4f} kWh'.format(ow.array_aep)
    print 'Array losses {:.4f}'.format(ow.array_losses)
    print 'Net   {:.4f} kWh'.format(ow.net_aep)
    print 'CF    {:.4f} %'.format(ow.capacity_factor)

if __name__ == "__main__":

    example()