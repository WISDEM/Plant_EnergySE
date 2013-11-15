"""
aep_csm_component.py

Created by NWTC Systems Engineering Sub-Task on 2012-08-01.
Copyright (c) NREL. All rights reserved.
"""

import sys
import numpy as np

from openmdao.main.api import Component, Assembly, set_as_top, VariableTree
from openmdao.main.datatypes.api import Int, Bool, Float, Array, VarTree

from twister.models.csm.csmAEP import csmAEP

class aep_csm_component(Component):
  
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

    aep = Float(0.0, units= 'kW * h', iotype='out', desc='Annual energy production in kWh')  # use PhysicalUnits to set units='kWh'
    capacityFactor = Float(0.0, iotype='out', desc= 'Annual capacity factor for a wind plant')
    aepPerTurbine = Float(0.0, units = 'kW * h', iotype='out', desc = 'Annual energy production in kWh per turbine')


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

        super(aep_csm_component,self).__init__()

        #initialize csmAEP model
        self.aepSim = csmAEP()


    def execute(self):
        """
        Executes AEP Sub-module of the NREL Cost and Scaling Model by convolving a wind turbine power curve with a weibull distribution.  
        It then discounts the resulting AEP for availability, plant and soiling losses.
        """

        print "In {0}.execute() ...".format(self.__class__)

        self.aepSim.compute(self.powerCurve, self.ratedPower, self.hubHeight, self.shearExponent, self.windSpeed50m, self.weibullK, self.soilingLosses, self.arrayLosses, self.availability)

        self.aepPerTurbine = self.aepSim.getAEP()
        self.aep = self.aepPerTurbine * self.turbineNumber
        self.capacityFactor = self.aepSim.getCapacityFactor()

def example():

    aeptest = aep_csm_component()
    
    aeptest.powerCurve = [[0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, \
                           11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0, 21.0, 22.0, 23.0, 24.0, 25.0, 26.0], \
                          [0.0, 0.0, 0.0, 0.0, 187.0, 350.0, 658.30, 1087.4, 1658.3, 2391.5, 3307.0, \
                          4415.70, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, \
                          5000.0, 5000.0, 5000.0, 5000.0, 0.0]]
    aeptest.execute()

    print "AEP output: {0}".format(aeptest.aep)  
    print "AEP output per turbine: {0}".format(aeptest.aepPerTurbine)
    print "capacity factor: {0}".format(aeptest.capacityFactor)

if __name__=="__main__":

    example()