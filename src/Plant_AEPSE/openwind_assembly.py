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
from twister.fused_plant import GenericAEPModel, GenericWindTurbinePowerCurveDesc, GenericWindFarmTurbineLayout
from twister.models.AEP.openWindExtCode import OWwrapped

import wrtTurbXML
from lxml import etree
import wrtScriptXML

import numpy as np

#------------------------------------------------------------------

class openwind_assembly(Assembly): # todo: has to be assembly or manipulation and passthrough of aep in execute doesnt work
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
    #array_aep = Float(0.0, iotype='out', desc='Gross Annual Energy Production net of array impacts', unit='kWh')
    #array_losses = Float(0.0, iotype='out', desc='Array Losses')
    # while framework not working
    #gross_aep = Float(0.0, iotype='out', desc='Gross Annual Energy Production before availability and loss impacts', unit='kWh')
    #net_aep = Float(0.0, iotype='out', desc='Net Annual Energy Production after availability and loss impacts', unit='kWh')
    #capacity_factor = Float(0.0, iotype='out', desc='Capacity factor for wind plant') # ??? generic or specific? will be easy to calculate, # P-E: OK


    # -------------------
    
    def __init__(self):
        """ Creates a new LCOE Assembly object """

        super(openwind_assembly, self).__init__()

        # TODO: hack for now assigning turbine
        self.turb = GenericWindTurbinePowerCurveDesc()
        self.turb.power_rating = self.ratedPower
        self.turb.hub_height = self.hubHeight
        self.turb.power_curve = np.copy(self.powerCurve)
        for i in xrange(0,self.turbineNumber):
            self.wt_layout.wt_list.append(self.turb)

    def configure(self):
        """ Add Openwind external code component """

        super(openwind_assembly, self).configure()        
        
        ow = OWwrapped()
        self.add('ow', ow)
        
        self.driver.workflow.add(['ow'])
        
        self.connect('rotorDiameter', 'ow.rotorDiameter') # todo: hack to force external code execution
        self.connect('soilingLosses', 'ow.soilingLosses')
        self.connect('availability', 'ow.availability')
        
        self.create_passthrough('ow.array_losses')
        self.create_passthrough('ow.gross_aep')
        self.create_passthrough('ow.array_aep')
        self.create_passthrough('ow.net_aep')
        #self.create_passthrough('ow.capacity_factor')
        
    # -------------------
    
    def execute(self):
        """
            Set up XML and run OpenWind
            This will leave OW running - use the File/Exit button to shut it down until
              Nick comes up with a way to stop it from the script.
        """

        print "In {0}.execute()...".format(self.__class__)

        # Set up turbine to write to xml
        thrust = [0.000, 0.000, 0.000, 0.878, 0.880, 0.881, 0.881, 0.882, 0.882, 0.843, 
                  0.764, 0.544, 0.390, 0.297, 0.235, 0.190, 0.156, 0.131,
                  0.111, 0.096, 0.083, 0.073, 0.064, 0.057, 0.051, 0.046 ]
        power = []
        for i in xrange(0,4):
          power.append(0.0)
        counter = 4.0
        for i in xrange(0, self.powerCurve.shape[1]):
            while counter < self.powerCurve[0][i]:
              counter += 1.0
            if abs(counter - (self.powerCurve[0][i])) < 0.10:
              power.append(self.powerCurve[1][i])
              counter += 1.0
            if counter >= 26:
              break
        power.append(self.ratedPower)
        power.append(self.ratedPower)
        percosts = []
        cutInWS = 3.0
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
    
        ofh = open('C:/Python27/Openmdao-0.7.0/twister/models/AEP/Turbine_Model.owtg', 'w')
        ofh.write(turbXML)
        ofh.close()
    
        # write new script for execution  
        rpath = 'C:/Python27/Openmdao-0.7.0/twister/models/AEP/scrtest1.txt'
        blbpath = 'C:/Python27/Openmdao-0.7.0/twister/models/AEP/OpenWind_Model.blb'
        tname = 'NREL 5 MW'
        tpath = 'C:/Python27/Openmdao-0.7.0/twister/models/AEP/Turbine_Model.owtg'
    
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
        
        ofh = open('C:/Python27/Openmdao-0.7.0/twister/models/AEP/OpenWind_Script.xml', 'w')
        ofh.write(scriptXML)
        ofh.close()
    
        self.ow.scriptfile = 'C:/Python27/Openmdao-0.7.0/twister/models/AEP/OpenWind_Script.xml'

        # will actually run the workflow
        super(openwind_assembly, self).execute()
        
    
#------------------------------------------------------------------

if __name__ == "__main__":

    # simple test of module
    
    ow = openwind_assembly()
    
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