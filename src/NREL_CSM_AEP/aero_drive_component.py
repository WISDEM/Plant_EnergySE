"""
aero_csm_component.py

Created by NWTC Systems Engineering Sub-Task on 2012-08-01.
Copyright (c) NREL. All rights reserved.
"""

import sys
import numpy as np

from openmdao.main.api import Component, Assembly, set_as_top, VariableTree
from openmdao.main.datatypes.api import Int, Bool, Float, Array, VarTree

from twister.models.csm.csmPowerCurve import csmPowerCurve
from twister.models.csm.csmDriveEfficiency import DrivetrainEfficiencyModel, csmDriveEfficiency

class aero_drive_component(Component):

    # ---- Design Variables ----------
    
    # Drivetrain Efficiency Model
    drivetrain = VarTree(DrivetrainEfficiencyModel, iotype = 'in', desc= "drivetrain efficiency model", required=True) 
    # Rotor
    ratedPower = Float(5000.0, units = 'kW', iotype='in', desc= 'rated machine power in kW')
    # Aero Model 
    powerCurveRaw = Array(np.array([[0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, \
                           11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0, 21.0, 22.0, 23.0, 24.0, 25.0, 26.0], \
                          [0.0, 0.0, 0.0, 0.0, 236.3, 461.6, 797.6, 1266.6, 1890.7, 2692.0, 3692.7, \
                          4904.5, 6165.7, 7426.8, 8687.9, 9949.0, 11210.1, 12471.2, 13732.4, 14993.5, 16254.6, 17515.7, \
                          18776.8, 20038.0, 21299.1, 22560.2, 0.0]]),iotype='in', desc= 'turbine power curve [kw] as a function of wind speed [m/s]') 

    # ------------- Outputs --------------  
    
    ratedWindSpeed = Float(11.506, units = 'm / s', iotype='out', desc='wind speed for rated power')
    powerCurve = Array(np.array([[0,0],[25.0, 0.0]]), iotype='out', desc = 'power curve for a particular rotor')
    maxEfficiency = Float(0.902, iotype='out', desc = 'maximum efficiency of rotor and drivetrain - at rated power') 

    def __init__(self):
        """
        OpenMDAO component to wrap Aerodynamics module of the NREL Cost and Scaling Model (csmAero.py)
        
        Parameters
        ----------
        drivetrainDesign : DrivetrainEfficiencyModel
          drivetrain efficiency model (required and must conform with interface)
        ratedPower : float
          wind turbine rated power [kW]
        powerCurveRaw : array_like of float
          ideal power curve for a particular rotor as a 2-D array of power vs. wind [kW vs. m/s]
          
          
        Returns
        -------
        ratedWindSpeed : float
          wind speed for rated power [m/s]
        powerCurve : array_like of float
          power curve for a particular rotor as a 2-D array of power vs. wind [kW vs. m/s]
        maxEfficiency : float
          maximum efficiency of rotor and drivetrain - at rated power
        
        """


        super(aero_drive_component,self).__init__()

    def execute(self):
        """
        Modifies the ideal power curve to take into account drivetrain efficiency losses through an interface to a drivetrain efficiency model.
        """
        
        print "In {0}.execute() ...".format(self.__class__)
        
        ratedflag = True 
        self.powerCurve = self.powerCurveRaw
        for i in xrange(0,self.powerCurveRaw.shape[1]):
           self.powerCurve[1,i] = self.powerCurveRaw[1,i] * self.drivetrain.getDrivetrainEfficiency(self.powerCurveRaw[1,i],self.ratedPower)
           if (self.powerCurve[1,i] >= self.ratedPower) and (ratedflag):
               ratedflag = False
               self.ratedWindSpeed = self.powerCurve[0,i]
               self.powerCurve[1,i] = self.ratedPower
           elif (self.powerCurve[1,i] >= self.ratedPower):
               self.powerCurve[1,i] = self.ratedPower
        
        self.maxEfficiency = self.drivetrain.getMaxEfficiency()


def example():

    aerotest = aero_drive_component()
    
    drivetrain = csmDriveEfficiency(1)
    aerotest.drivetrain = drivetrain
    
    # Test for NREL 5 MW turbine
    aerotest.execute()
    
    print "NREL 5MW Reference Turbine"
    print "Rated wind speed: {0}".format(aerotest.ratedWindSpeed)
    print "Maximum efficiency: {0}".format(aerotest.maxEfficiency)
    print "Power Curve: "
    print aerotest.powerCurve   

if __name__=="__main__":


    example()