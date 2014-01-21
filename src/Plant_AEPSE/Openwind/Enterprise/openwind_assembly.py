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
    hubHeight = Float(90.0, iotype='in', desc='turbine hub height', unit='m')
    rotorDiameter = Float(126.0, iotype='in', desc='turbine rotor diameter', unit='m')
    powerCurve = Array([], iotype='in', desc='wind turbine power curve')
    rpm = Array([], iotype='in', desc='wind turbine rpm curve')
    turbineNumber = Int(100, iotype='in', desc='plant number of turbines')
    ratedPower = Float(5000.0, iotype='in', desc='wind turbine rated power', unit='kW')
    availability = Float(0.941, iotype='in', desc='wind plant availability')
    soilingLosses = Float(0.0, iotype='in', desc='wind plant losses due to blade soiling, etc')
    wt_layout = VarTree(GenericWindFarmTurbineLayout(), iotype='in', desc='properties for each wind turbine and layout')
    # TODO: loss inputs
    # TODO: wake model option selections (should not be OpenMDAO inputs but need to be part up overall inputs)

    # Outputs
    #ideal_aep = Float(0.0, iotype='out', desc='Ideal Annual Energy Production before topographic, availability and loss impacts', unit='kWh')
    array_aep = Float(0.0, iotype='out', desc='Gross Annual Energy Production net of array impacts', unit='kWh')
    array_losses = Float(0.0, iotype='out', desc='Array Losses')

    # -------------------
    
    def __init__(self, owexe, blbpath, tname):
        """ Creates a new LCOE Assembly object """

        self.owexe = owexe
        self.blbpath = blbpath
        self.tname = tname
        super(openwind_assembly, self).__init__()

        # TODO: hack for now assigning turbine
        self.turb = GenericWindTurbinePowerCurveVT()
        self.turb.power_rating = self.ratedPower
        self.turb.hub_height = self.hubHeight
        self.turb.power_curve = np.copy(self.powerCurve)
        for i in xrange(0,self.turbineNumber):
            self.wt_layout.wt_list.append(self.turb)

    def configure(self):
        """ Add Openwind external code component """

        super(openwind_assembly, self).configure()        
        
        ow = OWwrapped(self.owexe)
        self.add('ow', ow)
        
        self.driver.workflow.add(['ow'])
        
        self.connect('rotorDiameter', 'ow.rotorDiameter') # todo: hack to force external code execution
        self.connect('soilingLosses', 'ow.soilingLosses')
        self.connect('availability', 'ow.availability')
        
        self.connect('ow.array_losses', 'array_losses')
        self.connect('ow.gross_aep', 'gross_aep')
        self.connect('ow.array_aep', 'array_aep')
        self.connect('ow.net_aep', 'net_aep')
        #self.connect('ow.capacity_factor', 'capacity_factor')
        
    # -------------------
    
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
          myi = min(range(self.powerCurve.shape[1]), key=lambda i: abs(self.powerCurve[0][i]-counter))
          power.append(self.powerCurve[1][myi])
          counter += 1.0 
        power.append(self.powerCurve[1][-1])

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
        cutInWS = 4.0
        cutOutWS = 25.0
        nblades = 3
        ttlCost = 2000000
        fndCost =  100000
        trbname = 'NewTurbine'
        desc = 'New Turbine'
        turbtree = wrtTurbXML.getTurbTree(trbname, desc, power, thrust, self.hubHeight, self.rotorDiameter,\
                                         percosts, cutInWS, cutOutWS, nblades, self.ratedPower, ttlCost, fndCost)
        turbXML = etree.tostring(turbtree, 
                                 xml_declaration=True,
                                 doctype='<!DOCTYPE {:}>'.format(trbname), 
                                 pretty_print=True)

        thisdir = os.path.dirname(os.path.realpath(__file__))   
    
        ofh = open(thisdir + '/' + 'Turbine_Model.owtg', 'w')
        ofh.write(turbXML)
        ofh.close()
    
        # write new script for execution  
        rpath = thisdir + '/' + 'scrtest1.txt'
        blbpath = self.blbpath
        tname = self.tname
        tpath = thisdir + '/' + 'Turbine_Model.owtg'
    
        scripttree, ops = wrtScriptXML.getScriptTree(rpath)    
        # add operations to 'ops' (the 'AllOperations' tree in scripttree)
        
        wrtScriptXML.makeChWkbkOp(ops,blbpath)       # change workbook
        wrtScriptXML.makeRepTurbOp(ops,tname,tpath)  # replace turbine
        wrtScriptXML.makeEnCapOp(ops)                # run energy capture
        wrtScriptXML.makeExitOp(ops)                 # exit
        
        scriptXML = etree.tostring(scripttree, 
                                   xml_declaration=True, 
                                   doctype='<!DOCTYPE OpenWindScript>',
                                   pretty_print=True)
        
        ofh = open(thisdir + '/' + 'OpenWind_Script.xml', 'w')
        ofh.write(scriptXML)
        ofh.close()
    
        self.ow.scriptfile = thisdir + '/' + 'OpenWind_Script.xml'

        # will actually run the workflow
        super(openwind_assembly, self).execute()

        # calculate capacity factor
        self.capacity_factor = ((self.net_aep) / (self.wt_layout.wt_list[0].power_rating * 8760.0 * len(self.wt_layout.wt_list)))
        
    
#------------------------------------------------------------------

def example():

    # simple test of module
    owExeV1130 = 'C:/Models/Openwind/OpenWind64.exe'
    blbpath = 'C:/Models/OpenWind/Workbooks/OpenWind_Model.blb'
    tname = 'NREL 5 MW'
    ow = openwind_assembly(owExeV1130, blbpath, tname)
    
    ow.powerCurve = np.array([[1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, \
                           11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0, 21.0, 22.0, 23.0, 24.0, 25.0, 26.0], \
                          [0.0, 0.0, 0.0, 187.0, 350.0, 658.30, 1087.4, 1658.3, 2391.5, 3307.0, \
                          4415.70, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, \
                          5000.0, 5000.0, 5000.0, 5000.0, 0.0]])

    ow.execute() # run the openWind process

    print 'Gross {:.4f} kWh'.format(ow.gross_aep)
    print 'Array {:.4f} kWh'.format(ow.array_aep)
    print 'Array losses {:.4f}'.format(ow.array_losses)
    print 'Net   {:.4f} kWh'.format(ow.net_aep)
    print 'CF    {:.4f} %'.format(ow.capacity_factor)

if __name__ == "__main__":

    example()