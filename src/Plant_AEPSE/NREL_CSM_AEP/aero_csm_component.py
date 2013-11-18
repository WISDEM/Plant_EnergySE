"""
aero_csm_component.py

Created by NWTC Systems Engineering Sub-Task on 2012-08-01.
Copyright (c) NREL. All rights reserved.
"""

import sys
import numpy as np

from openmdao.main.api import Component, Assembly, set_as_top, VariableTree
from openmdao.main.datatypes.api import Int, Bool, Float, Array, VarTree, Slot

from NREL_CSM.csmPowerCurve import csmPowerCurve
from NREL_CSM.csmDriveEfficiency import DrivetrainEfficiencyModel, csmDriveEfficiency

class aero_csm_component(Component):

    # ---- Design Variables ----------
    
    # Drivetrain Efficiency Model
    drivetrain = Slot(DrivetrainEfficiencyModel, iotype = 'in', desc= "drivetrain efficiency model", required = True)   
    
    # Turbine configuration
    #rotor
    machine_rating = Float(5000.0, units = 'kW', iotype='in', desc= 'rated machine power in kW')
    max_tip_speed = Float(80.0, units = 'm/s', iotype='in', desc= 'maximum allowable tip speed for the rotor')
    rotor_diameter = Float(126.0, units = 'm', iotype='in', desc= 'rotor diameter of the machine') 
    max_power_coefficient = Float(0.488, iotype='in', desc= 'maximum power coefficient of rotor for operation in region 2')
    opt_tsr = Float(7.525, iotype='in', desc= 'optimum tip speed ratio for operation in region 2')
    cut_in_wind_speed = Float(3.0, units = 'm/s', iotype='in', desc= 'cut in wind speed for the wind turbine')
    cut_out_wind_speed = Float(25.0, units = 'm/s', iotype='in', desc= 'cut out wind speed for the wind turbine')
    #tower/substructure
    hub_height = Float(90.0, units = 'm', iotype='in', desc= 'hub height of wind turbine above ground / sea level')
    
    #Plant configuration
    altitude = Float(0.0, units = 'm', iotype='in', desc= 'altitude of wind plant')
    air_density = Float(0.0, units = 'kg / (m * m * m)', iotype='in', desc= 'air density at wind plant site')  # default air density value is 0.0 - forces aero csm to calculate air density in model


    # ------------- Outputs --------------  
    
    rated_wind_speed = Float(11.506, units = 'm / s', iotype='out', desc='wind speed for rated power')
    rated_rotor_speed = Float(12.10, units = 'rpm', iotype='out', desc = 'rotor speed at rated power')
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
        max_tip_speed : float
          maximum allowable tip speed for the rotor [m/s]
        rotor_diameter : float
          rotor diameter of the machine [m]
        max_power_coefficient : float
          maximum power coefficient of rotor for operation in region 2
        opt_tsr : float
          optimum tip speed ratio for operation in region 2
        cut_in_wind_speed : float
          cut in wind speed for the wind turbine [m/s]
        cut_out_wind_speed : float
          cut out wind speed for the wind turbine [m/s]
        hub_height : float
          hub height of wind turbine above ground / sea level
        altitude : float
          altitude of wind plant [m]
        air_density : float
          air density at wind plant site [kg / m^3]
          
        Returns
        -------
        rated_wind_speed : float
          wind speed for rated power [m/s]
        rated_rotor_speed : float
          rotor speed at rated power [m/s]
        power_curve : array_like of float
          power curve for a particular rotor as a 2-D array of power vs. wind [kW vs. m/s]
        max_efficiency : float
          maximum efficiency of rotor and drivetrain - at rated power
        
        """

        super(aero_csm_component,self).__init__()

        #initialize csmPowerCurve model
        self.aeroSim = csmPowerCurve()
        self.drivetrain = csmDriveEfficiency(1)


    def execute(self):
        """
        Executes Aerodynamics Sub-module of the NREL _cost and Scaling Model to create a power curve based on a limited set of inputs.
        It then modifies the ideal power curve to take into account drivetrain efficiency losses through an interface to a drivetrain efficiency model.
        """
        print "In {0}.execute() ...".format(self.__class__)
         
        self.aeroSim.compute(self.drivetrain, self.hub_height, self.machine_rating, self.max_tip_speed, \
                             self.rotor_diameter, self.max_power_coefficient, self.opt_tsr, \
                             self.cut_in_wind_speed, self.cut_out_wind_speed, self.altitude, self.air_density)

        self.rated_wind_speed = self.aeroSim.getRatedWindSpeed()
        self.rated_rotor_speed = self.aeroSim.getRatedRotorSpeed()
        self.power_curve = self.aeroSim.getPowerCurve()
        self.max_efficiency = self.aeroSim.getMaxEfficiency()

def example():
  
    aerotest = aero_csm_component()
    
    drivetrain = csmDriveEfficiency(1)
    aerotest.drivetrain = drivetrain
    
    # Test for NREL 5 MW turbine
    aerotest.execute()
    
    print "NREL 5MW Reference Turbine"
    print "Rated rotor speed: {0}".format(aerotest.rated_rotor_speed)
    print "Rated wind speed: {0}".format(aerotest.rated_wind_speed)
    print "Maximum efficiency: {0}".format(aerotest.max_efficiency)
    print "Power Curve: "
    print aerotest.power_curve   

if __name__=="__main__":


    example()