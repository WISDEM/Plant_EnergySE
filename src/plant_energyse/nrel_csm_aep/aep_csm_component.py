"""
aep_csm_component.py

Created by NWTC Systems Engineering Sub-Task on 2012-08-01.
Copyright (c) NREL. All rights reserved.
"""

from openmdao.main.api import Component, Assembly, set_as_top, VariableTree
from openmdao.main.datatypes.api import Int, Bool, Float, Array, VarTree

from fusedwind.plant_flow.comp import BaseAEPAggregator
from fusedwind.interface import implement_base

from math import *
import numpy as np

# ---------------------------------

def weibull(X,K,L):
    ''' 
    Return Weibull probability at speed X for distribution with k=K, c=L 
    
    Parameters
    ----------
    X : float
       wind speed of interest [m/s]
    K : float
       Weibull shape factor for site
    L : float
       Weibull scale factor for site [m/s]
       
    Returns
    -------
    w : float
      Weibull pdf value
    '''
    w = (K/L) * ((X/L)**(K-1)) * exp(-((X/L)**K))
    return w

# ---------------------------
@implement_base(BaseAEPAggregator)
class aep_csm_component(Component):
  
    # Variables
    power_curve = Array(iotype='in', units='kW', desc='total power after drivetrain losses')
    wind_curve = Array(iotype='in', units='m/s', desc='wind curve associated with power curve')
    hub_height = Float(iotype='in', units = 'm', desc='hub height of wind turbine above ground / sea level')
    shear_exponent = Float(iotype='in', desc= 'shear exponent for wind plant') #TODO - could use wind model here
    wind_speed_50m = Float(iotype='in', units = 'm/s', desc='mean annual wind speed at 50 m height')
    weibull_k= Float(iotype='in', desc = 'weibull shape factor for annual wind speed distribution')
    machine_rating = Float(iotype='in', units='kW', desc='machine power rating')

    # Parameters
    soiling_losses = Float(0.0, iotype='in', desc = 'energy losses due to blade soiling for the wind plant - average across turbines')
    array_losses = Float(0.06, iotype='in', desc = 'energy losses due to turbine interactions - across entire plant')
    availability = Float(0.94287630736, iotype='in', desc = 'average annual availbility of wind turbines at plant')
    turbine_number = Int(100, iotype='in', desc = 'total number of wind turbines at the plant')

    # Output
    gross_aep = Float(iotype='out', desc='Gross Annual Energy Production before availability and loss impacts', unit='kWh')
    net_aep = Float(units= 'kW * h', iotype='out', desc='Annual energy production in kWh')  # use PhysicalUnits to set units='kWh'
    power_array = Array(iotype='out', units='kW', desc='total power after drivetrain losses')
    capacity_factor = Float(iotype='out', desc='plant capacity factor')

    def execute(self):
        """
        Executes AEP Sub-module of the NREL _cost and Scaling Model by convolving a wind turbine power curve with a weibull distribution.  
        It then discounts the resulting AEP for availability, plant and soiling losses.
        """

        self.power_array = [self.wind_curve, self.power_curve]

        hubHeightWindSpeed = ((self.hub_height/50)**self.shear_exponent)*self.wind_speed_50m
        K = self.weibull_k
        L = hubHeightWindSpeed / exp(log(gamma(1.+1./K)))

        turbine_energy = 0.0
        for i in xrange(0,self.power_array.shape[1]):
           X = self.power_array[0,i]
           result = self.power_array[1,i] * weibull(X, K, L)
           turbine_energy += result

        ws_inc = self.power_array[0,1] - self.power_array[0,0]
        self.gross_aep = turbine_energy * 8760.0 * self.turbine_number * ws_inc
        self.net_aep = self.gross_aep * (1.0-self.soiling_losses)* (1.0-self.array_losses) * self.availability
        self.capacity_factor = self.net_aep / (8760 * self.machine_rating)

def example():

    aeptest = aep_csm_component()
    
    aeptest.power_curve = [0.0, 0.0, 0.0, 0.0, 187.0, 350.0, 658.30, 1087.4, 1658.3, 2391.5, 3307.0, \
                          4415.70, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, \
                          5000.0, 5000.0, 5000.0, 5000.0, 0.0]
    aeptest.wind_curve = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, \
                           11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0, 21.0, 22.0, 23.0, 24.0, 25.0, 26.0]

    aeptest.run()

    print "AEP output: {0}".format(aeptest.net_aep)

if __name__=="__main__":

    example()