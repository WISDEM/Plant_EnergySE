"""
aero_csm_component.py

Created by NWTC Systems Engineering Sub-Task on 2012-08-01.
Copyright (c) NREL. All rights reserved.
"""

import sys
import numpy as np

from openmdao.main.api import Component, Assembly, set_as_top, VariableTree
from openmdao.main.datatypes.api import Int, Bool, Float, Array, VarTree

from NREL_CSM.csmPowerCurve import csmPowerCurve
from NREL_CSM.csmDriveEfficiency import DrivetrainEfficiencyModel, csmDriveEfficiency

class aero_drive_component(Component):

    # ---- Design Variables ----------
    
    # Drivetrain Efficiency Model
    drivetrain = VarTree(DrivetrainEfficiencyModel, iotype = 'in', desc= "drivetrain efficiency model", required=True) 
    # Rotor
    machine_rating = Float(5000.0, units = 'kW', iotype='in', desc= 'rated machine power in kW')
    # Aero Model 
    power_curve_raw = Array(np.array([[0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, \
                           11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0, 21.0, 22.0, 23.0, 24.0, 25.0, 26.0], \
                          [0.0, 0.0, 0.0, 0.0, 236.3, 461.6, 797.6, 1266.6, 1890.7, 2692.0, 3692.7, \
                          4904.5, 6165.7, 7426.8, 8687.9, 9949.0, 11210.1, 12471.2, 13732.4, 14993.5, 16254.6, 17515.7, \
                          18776.8, 20038.0, 21299.1, 22560.2, 0.0]]),iotype='in', desc= 'turbine power curve [kw] as a function of wind speed [m/s]') 

    # ------------- Outputs --------------  
    
    rated_wind_speed = Float(11.506, units = 'm / s', iotype='out', desc='wind speed for rated power')
    power_curve = Array(np.array([[0,0],[25.0, 0.0]]), iotype='out', desc = 'power curve for a particular rotor')
    max_efficiency = Float(0.902, iotype='out', desc = 'maximum efficiency of rotor and drivetrain - at rated power') 

    def __init__(self):
        """
        OpenMDAO component to wrap Aerodynamics module of the NREL _cost and Scaling Model (csmAero.py)
        
        Parameters
        ----------
        drivetrain_design : DrivetrainEfficiencyModel
          drivetrain efficiency model (required and must conform with interface)
        machine_rating : float
          wind turbine rated power [kW]
        power_curve_raw : array_like of float
          ideal power curve for a particular rotor as a 2-D array of power vs. wind [kW vs. m/s]
          
          
        Returns
        -------
        rated_wind_speed : float
          wind speed for rated power [m/s]
        power_curve : array_like of float
          power curve for a particular rotor as a 2-D array of power vs. wind [kW vs. m/s]
        max_efficiency : float
          maximum efficiency of rotor and drivetrain - at rated power
        
        """


        super(aero_drive_component,self).__init__()

    def execute(self):
        """
        Modifies the ideal power curve to take into account drivetrain efficiency losses through an interface to a drivetrain efficiency model.
        """
        
        print "In {0}.execute() ...".format(self.__class__)
        
        ratedflag = True 
        self.power_curve = self.power_curve_raw
        for i in xrange(0,self.power_curve_raw.shape[1]):
           self.power_curve[1,i] = self.power_curve_raw[1,i] * self.drivetrain.getDrivetrainEfficiency(self.power_curve_raw[1,i],self.machine_rating)
           if (self.power_curve[1,i] >= self.machine_rating) and (ratedflag):
               ratedflag = False
               self.rated_wind_speed = self.power_curve[0,i]
               self.power_curve[1,i] = self.machine_rating
           elif (self.power_curve[1,i] >= self.machine_rating):
               self.power_curve[1,i] = self.machine_rating
        
        self.max_efficiency = self.drivetrain.getMaxEfficiency()


def example():

    aerotest = aero_drive_component()
    
    drivetrain = csmDriveEfficiency(1)
    aerotest.drivetrain = drivetrain
    
    # Test for NREL 5 MW turbine
    aerotest.execute()
    
    print "NREL 5MW Reference Turbine"
    print "Rated wind speed: {0}".format(aerotest.rated_wind_speed)
    print "Maximum efficiency: {0}".format(aerotest.max_efficiency)
    print "Power Curve: "
    print aerotest.power_curve   

if __name__=="__main__":


    example()