"""
aep_csm_component.py

Created by NWTC Systems Engineering Sub-Task on 2012-08-01.
Copyright (c) NREL. All rights reserved.
"""

import sys
import numpy as np

from openmdao.main.api import Component, Assembly, set_as_top, VariableTree
from openmdao.main.datatypes.api import Int, Bool, Float, Array, VarTree

from NREL_CSM.csmAEP import csmAEP
from fusedwind.plant_flow.fused_plant_asym import GenericAEPModel

class aep_weibull_assembly(GenericAEPModel):

    def __init__(self):
        
        super(aep_weibull_assembly, self).__init__()

    def configure(self):
      
        super(aep_weibull_assembly, self).configure()
        
        self.add('aep', aep_weibull_component())
        
        self.driver.workflow.add(['aep'])
        
        #inputs
        #self.create_passthrough('aep.powerCurve') #TODO - array issue openmdao
        self.create_passthrough('aep.ratedPower')
        self.create_passthrough('aep.hubHeight')
        self.create_passthrough('aep.shearExponent')
        self.create_passthrough('aep.windSpeed50m')
        self.create_passthrough('aep.soilingLosses')
        self.create_passthrough('aep.arrayLosses')
        self.create_passthrough('aep.availability')
        self.create_passthrough('aep.turbineNumber')
        
        # outputs
        self.connect('aep.gross_aep', 'gross_aep')
        self.connect('aep.net_aep', 'net_aep')
        self.connect('aep.capacity_factor', 'capacity_factor')
        self.create_passthrough('aep.aep_per_turbine')

class aep_weibull_component(Component): # todo: has to be a component or manipulation and passthrough of net_aep doesnt work...
  
    # ---- Design Variables ----------    
    #Turbine configuration
    #rotor
    powerCurve = Array(np.array([[0.0,0.0],[25.0,0.0]]),iotype='in', desc= 'turbine power curve [kw] as a function of wind speed [m/s]')
    ratedPower = Float(5000.0, units='kW', iotype='in', desc= 'wind turbine rated power')
    #tower / substructure
    hubHeight = Float(90.0, units = 'm', iotype='in', desc='hub height of wind turbine above ground / sea level')
    
    #Plant configuration
    shearExponent = Float(0.1, iotype='in', desc= 'shear exponent for wind plant') #TODO - could use wind model here
    windSpeed50m = Float(8.35, units = 'm/s', iotype='in', desc='mean annual wind speed at 50 m height')
    weibullK= Float(2.1, iotype='in', desc = 'weibull shape factor for annual wind speed distribution')
    soilingLosses = Float(0.0, iotype='in', desc = 'energy losses due to blade soiling for the wind plant - average across turbines')
    arrayLosses = Float(0.059, iotype='in', desc = 'energy losses due to turbine interactions - across entire plant')
    availability = Float(0.94, iotype='in', desc = 'average annual availbility of wind turbines at plant')
    turbineNumber = Int(100, iotype='in', desc = 'total number of wind turbines at the plant')

    # ------------- Outputs -------------- 
    aep_per_turbine = Float(0.0, units = 'kW * h', iotype='out', desc = 'Annual energy production in kWh per turbine')
    gross_aep = Float(0.0, iotype='out', desc='Gross Annual Energy Production before availability and loss impacts', unit='kWh')
    net_aep = Float(0.0, iotype='out', desc='Net Annual Energy Production after availability and loss impacts', unit='kWh')
    capacity_factor = Float(0.0, iotype='out', desc='Capacity factor for wind plant') # ??? generic or specific? will be easy to calculate, # P-E: OK


    def __init__(self):

        """
        OpenMDAO component to wrap AEP module of the NREL Cost and Scaling Model (csmAEP.py)
        
        Parameters
        ----------
        powerCurve : array_like of float
          turbine power curve [kw] as a function of wind speed [m/s]
        ratedPower : float
          wind turbine rated power [kW]
        hubHeight : float
          hub height of wind turbine above ground / sea level [m]
        shearExponent : float
          shear exponent for wind plant
        windSpeed50m : float
          mean annual wind speed at 50 m height [m/s]
        weibullK : float
          weibull shape factor for annual wind speed distribution
        soilingLosses : float
          energy losses due to blade soiling for the wind plant - average across turbines
        arrayLosses : float
          energy losses due to turbine interactions - across entire plant
        availability : float
          average annual availbility of wind turbines at plant
        turbineNumber : int
          total number of wind turbines at the plant
        
        Returns
        -------
        aep : float
          Annual energy production in kWh
        capacityFactor : float
          Annual capacity factor for a wind plant
        aepPerTurbine : float
          Annual energy production in kWh per turbine
        
        """

        super(aep_weibull_component,self).__init__()

    def execute(self):
        """
        Executes AEP Sub-module of the NREL Cost and Scaling Model by convolving a wind turbine power curve with a weibull distribution.  
        It then discounts the resulting AEP for availability, plant and soiling losses.
        """

        print "In {0}.execute() ...".format(self.__class__)

        #initialize csmAEP model
        self.aepSim = csmAEP()

        self.aepSim.compute(self.powerCurve, self.ratedPower, self.hubHeight, self.shearExponent, \
                            self.windSpeed50m, self.weibullK, self.soilingLosses, self.arrayLosses, \
                            self.availability)

        self.aep_per_turbine = self.aepSim.getAEP() 
        self.net_aep = self.aepSim.getAEP() * self.turbineNumber
        self.gross_aep = self.net_aep / (1 - self.arrayLosses)
        self.capacity_factor = self.aepSim.getCapacityFactor()


def example():

    aeptest = aep_weibull_assembly()
    
    #print aeptest.aep.ratedPower
    
    aeptest.aep.powerCurve = [[0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, \
                           11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0, 21.0, 22.0, 23.0, 24.0, 25.0, 26.0], \
                          [0.0, 0.0, 0.0, 0.0, 187.0, 350.0, 658.30, 1087.4, 1658.3, 2391.5, 3307.0, \
                          4415.70, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, \
                          5000.0, 5000.0, 5000.0, 5000.0, 0.0]]
    aeptest.execute()

    print "AEP gross output: {0}".format(aeptest.gross_aep)
    print "AEP output: {0}".format(aeptest.net_aep)  
    print "AEP output per turbine: {0}".format(aeptest.aep_per_turbine)
    print "capacity factor: {0}".format(aeptest.capacity_factor)

if __name__=="__main__":

    example()