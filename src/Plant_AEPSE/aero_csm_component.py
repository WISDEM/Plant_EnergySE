"""
aero_csm_component.py

Created by NWTC Systems Engineering Sub-Task on 2012-08-01.
Copyright (c) NREL. All rights reserved.
"""

import sys
import numpy as np

from openmdao.main.api import Component, Assembly, set_as_top, VariableTree
from openmdao.main.datatypes.api import Int, Bool, Float, Array, VarTree, Slot

from twister.models.csm.csmPowerCurve import csmPowerCurve
from twister.models.csm.csmDriveEfficiency import DrivetrainEfficiencyModel, csmDriveEfficiency

class aero_csm_component(Component):

    # ---- Design Variables ----------
    
    # Drivetrain Efficiency Model
    drivetrain = Slot(DrivetrainEfficiencyModel, iotype = 'in', desc= "drivetrain efficiency model", required = True)   
    
    # Turbine configuration
    #rotor
    ratedPower = Float(5000.0, units = 'kW', iotype='in', desc= 'rated machine power in kW')
    maxTipSpeed = Float(80.0, units = 'm/s', iotype='in', desc= 'maximum allowable tip speed for the rotor')
    rotorDiameter = Float(126.0, units = 'm', iotype='in', desc= 'rotor diameter of the machine') 
    maxPowerCoefficient = Float(0.488, iotype='in', desc= 'maximum power coefficient of rotor for operation in region 2')
    optTipSpeedRatio = Float(7.525, iotype='in', desc= 'optimum tip speed ratio for operation in region 2')
    cutInWindSpeed = Float(3.0, units = 'm/s', iotype='in', desc= 'cut in wind speed for the wind turbine')
    cutOutWindSpeed = Float(25.0, units = 'm/s', iotype='in', desc= 'cut out wind speed for the wind turbine')
    #tower/substructure
    hubHeight = Float(90.0, units = 'm', iotype='in', desc= 'hub height of wind turbine above ground / sea level')
    
    #Plant configuration
    altitude = Float(0.0, units = 'm', iotype='in', desc= 'altitude of wind plant')
    airDensity = Float(0.0, units = 'kg / (m * m * m)', iotype='in', desc= 'air density at wind plant site')  # default air density value is 0.0 - forces aero csm to calculate air density in model


    # ------------- Outputs --------------  
    
    ratedWindSpeed = Float(11.506, units = 'm / s', iotype='out', desc='wind speed for rated power')
    ratedRotorSpeed = Float(12.10, units = 'rpm', iotype='out', desc = 'rotor speed at rated power')
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
        maxTipSpeed : float
          maximum allowable tip speed for the rotor [m/s]
        rotorDiameter : float
          rotor diameter of the machine [m]
        maxPowerCoefficient : float
          maximum power coefficient of rotor for operation in region 2
        optTipSpeedRatio : float
          optimum tip speed ratio for operation in region 2
        cutInWindSpeed : float
          cut in wind speed for the wind turbine [m/s]
        cutOutWindSpeed : float
          cut out wind speed for the wind turbine [m/s]
        hubHeight : float
          hub height of wind turbine above ground / sea level
        altitude : float
          altitude of wind plant [m]
        airDensity : float
          air density at wind plant site [kg / m^3]
          
        Returns
        -------
        ratedWindSpeed : float
          wind speed for rated power [m/s]
        ratedRotorSpeed : float
          rotor speed at rated power [m/s]
        powerCurve : array_like of float
          power curve for a particular rotor as a 2-D array of power vs. wind [kW vs. m/s]
        maxEfficiency : float
          maximum efficiency of rotor and drivetrain - at rated power
        
        """

        super(aero_csm_component,self).__init__()

        #initialize csmPowerCurve model
        self.aeroSim = csmPowerCurve()
        self.drivetrain = csmDriveEfficiency(1)


    def execute(self):
        """
        Executes Aerodynamics Sub-module of the NREL Cost and Scaling Model to create a power curve based on a limited set of inputs.
        It then modifies the ideal power curve to take into account drivetrain efficiency losses through an interface to a drivetrain efficiency model.
        """
        print "In {0}.execute() ...".format(self.__class__)
         
        self.aeroSim.compute(self.drivetrain, self.hubHeight, self.ratedPower, self.maxTipSpeed, \
                             self.rotorDiameter, self.maxPowerCoefficient, self.optTipSpeedRatio, \
                             self.cutInWindSpeed, self.cutOutWindSpeed, self.altitude, self.airDensity)

        self.ratedWindSpeed = self.aeroSim.getRatedWindSpeed()
        self.ratedRotorSpeed = self.aeroSim.getRatedRotorSpeed()
        self.powerCurve = self.aeroSim.getPowerCurve()
        self.maxEfficiency = self.aeroSim.getMaxEfficiency()

def example():
  
    aerotest = aero_csm_component()
    
    drivetrain = csmDriveEfficiency(1)
    aerotest.drivetrain = drivetrain
    
    # Test for NREL 5 MW turbine
    aerotest.execute()
    
    print "NREL 5MW Reference Turbine"
    print "Rated rotor speed: {0}".format(aerotest.ratedRotorSpeed)
    print "Rated wind speed: {0}".format(aerotest.ratedWindSpeed)
    print "Maximum efficiency: {0}".format(aerotest.maxEfficiency)
    print "Power Curve: "
    print aerotest.powerCurve   

if __name__=="__main__":


    example()