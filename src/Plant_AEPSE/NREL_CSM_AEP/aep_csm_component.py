"""
aep_csm_component.py

Created by NWTC Systems Engineering Sub-Task on 2012-08-01.
Copyright (c) NREL. All rights reserved.
"""

from openmdao.main.api import Component, Assembly, set_as_top, VariableTree
from openmdao.main.datatypes.api import Int, Bool, Float, Array, VarTree

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

class aep_csm_component(Component):
  
    # Variables
    power_curve = Array(np.array([[0.0,0.0],[25.0,0.0]]),iotype='in', desc= 'turbine power curve [kw] as a function of wind speed [m/s]')
    hub_height = Float(90.0, units = 'm', iotype='in', desc='hub height of wind turbine above ground / sea level')
    shear_exponent = Float(0.1, iotype='in', desc= 'shear exponent for wind plant') #TODO - could use wind model here
    wind_speed_50m = Float(8.02, units = 'm/s', iotype='in', desc='mean annual wind speed at 50 m height')
    weibull_k= Float(2.15, iotype='in', desc = 'weibull shape factor for annual wind speed distribution')

    # Parameters
    soiling_losses = Float(0.0, iotype='in', desc = 'energy losses due to blade soiling for the wind plant - average across turbines')
    array_losses = Float(0.10, iotype='in', desc = 'energy losses due to turbine interactions - across entire plant')
    availability = Float(0.941, iotype='in', desc = 'average annual availbility of wind turbines at plant')
    turbine_number = Int(100, iotype='in', desc = 'total number of wind turbines at the plant')

    # Output
    gross_aep = Float(0.0, iotype='out', desc='Gross Annual Energy Production before availability and loss impacts', unit='kWh')
    net_aep = Float(0.0, units= 'kW * h', iotype='out', desc='Annual energy production in kWh')  # use PhysicalUnits to set units='kWh'


    def __init__(self):

        """
        OpenMDAO component to wrap AEP module of the NREL _cost and Scaling Model (csmAEP.py)
        
        Parameters
        ----------
        power_curve : array_like of float
          turbine power curve [kw] as a function of wind speed [m/s]
        machine_rating : float
          wind turbine rated power [kW]
        hub_height : float
          hub height of wind turbine above ground / sea level [m]
        shear_exponent : float
          shear exponent for wind plant
        wind_speed_50m : float
          mean annual wind speed at 50 m height [m/s]
        weibull_k : float
          weibull shape factor for annual wind speed distribution
        soiling_losses : float
          energy losses due to blade soiling for the wind plant - average across turbines
        array_losses : float
          energy losses due to turbine interactions - across entire plant
        availability : float
          average annual availbility of wind turbines at plant
        turbine_number : int
          total number of wind turbines at the plant
        
        Returns
        -------
        aep : float
          Annual energy production in kWh
        capacityFactor : float
          Annual capacity factor for a wind plant
        aep_per_turbine : float
          Annual energy production in kWh per turbine
        
        """

        super(aep_csm_component,self).__init__()

    def execute(self):
        """
        Executes AEP Sub-module of the NREL _cost and Scaling Model by convolving a wind turbine power curve with a weibull distribution.  
        It then discounts the resulting AEP for availability, plant and soiling losses.
        """

        print "In {0}.execute() ...".format(self.__class__)

        hubHeightWindSpeed = ((self.hub_height/50)**self.shear_exponent)*self.wind_speed_50m
        K = self.weibull_k
        L = hubHeightWindSpeed / exp(log(gamma(1.+1./K)))

        turbine_energy = 0.0
        for i in xrange(0,self.power_curve.shape[1]):
           X = self.power_curve[0,i]
           result = self.power_curve[1,i] * weibull(X, K, L)
           turbine_energy += result

        ws_inc = self.power_curve[0,1] - self.power_curve[0,0]
        self.gross_aep = turbine_energy * 8760.0 * self.turbine_number * ws_inc
        self.net_aep = self.gross_aep * (1.0-self.soiling_losses)* (1.0-self.array_losses) * self.availability

def example():

    aeptest = aep_csm_component()
    
    aeptest.power_curve = [[0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, \
                           11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0, 21.0, 22.0, 23.0, 24.0, 25.0, 26.0], \
                          [0.0, 0.0, 0.0, 0.0, 187.0, 350.0, 658.30, 1087.4, 1658.3, 2391.5, 3307.0, \
                          4415.70, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, \
                          5000.0, 5000.0, 5000.0, 5000.0, 0.0]]

    aeptest.execute()

    print "AEP output: {0}".format(aeptest.net_aep)

if __name__=="__main__":

    example()