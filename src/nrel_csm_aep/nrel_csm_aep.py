"""
aep_csm_assembly.py

Created by NWTC Systems Engineering Sub-Task on 2012-08-01.
Copyright (c) NREL. All rights reserved.
"""

import numpy as np

from openmdao.main.api import Component, Assembly, set_as_top, VariableTree
from openmdao.main.datatypes.api import Int, Bool, Float, Array, VarTree, Enum

from fusedwind.plant_flow.asym import BaseAEPModel
from fusedwind.interface import implement_base

from CSMDrivetrain import CSMDrivetrain
from aero_csm_component import aero_csm_component
from aep_csm_component import aep_csm_component

@implement_base(BaseAEPModel)
class aep_csm_assembly(Assembly):

    # Variables
    machine_rating = Float(5000.0, units = 'kW', iotype='in', desc= 'rated machine power in kW')
    max_tip_speed = Float(80.0, units = 'm/s', iotype='in', desc= 'maximum allowable tip speed for the rotor')
    rotor_diameter = Float(126.0, units = 'm', iotype='in', desc= 'rotor diameter of the machine') 
    max_power_coefficient = Float(0.488, iotype='in', desc= 'maximum power coefficient of rotor for operation in region 2')
    opt_tsr = Float(7.525, iotype='in', desc= 'optimum tip speed ratio for operation in region 2')
    cut_in_wind_speed = Float(3.0, units = 'm/s', iotype='in', desc= 'cut in wind speed for the wind turbine')
    cut_out_wind_speed = Float(25.0, units = 'm/s', iotype='in', desc= 'cut out wind speed for the wind turbine')
    hub_height = Float(90.0, units = 'm', iotype='in', desc= 'hub height of wind turbine above ground / sea level')
    altitude = Float(0.0, units = 'm', iotype='in', desc= 'altitude of wind plant')
    air_density = Float(0.0, units = 'kg / (m * m * m)', iotype='in', desc= 'air density at wind plant site')  # default air density value is 0.0 - forces aero csm to calculate air density in model
    drivetrain_design = Enum('geared', ('geared', 'single_stage', 'multi_drive', 'pm_direct_drive'), iotype='in')
    shear_exponent = Float(0.1, iotype='in', desc= 'shear exponent for wind plant') #TODO - could use wind model here
    wind_speed_50m = Float(8.35, units = 'm/s', iotype='in', desc='mean annual wind speed at 50 m height')
    weibull_k= Float(2.1, iotype='in', desc = 'weibull shape factor for annual wind speed distribution')
    soiling_losses = Float(0.0, iotype='in', desc = 'energy losses due to blade soiling for the wind plant - average across turbines')
    array_losses = Float(0.06, iotype='in', desc = 'energy losses due to turbine interactions - across entire plant')
    availability = Float(0.94287630736, iotype='in', desc = 'average annual availbility of wind turbines at plant')
    turbine_number = Int(100, iotype='in', desc = 'total number of wind turbines at the plant')
    thrust_coefficient = Float(0.50, iotype='in', desc='thrust coefficient at rated power')

    # Outputs
    rated_wind_speed = Float(11.506, units = 'm / s', iotype='out', desc='wind speed for rated power')
    rated_rotor_speed = Float(12.126, units = 'rpm', iotype='out', desc = 'rotor speed at rated power')
    rotor_thrust = Float(iotype='out', units='N', desc='maximum thrust from rotor')    
    rotor_torque = Float(iotype='out', units='N * m', desc = 'torque from rotor at rated power') 
    power_curve = Array(np.array([[4.0,80.0],[25.0, 5000.0]]), iotype='out', desc = 'power curve for a particular rotor')
    max_efficiency = Float(0.902, iotype='out', desc = 'maximum efficiency of rotor and drivetrain - at rated power')  
    gross_aep = Float(0.0, iotype='out', desc='Gross Annual Energy Production before availability and loss impacts', unit='kWh')
    net_aep = Float(0.0, units= 'kW * h', iotype='out', desc='Annual energy production in kWh')  # use PhysicalUnits to set units='kWh'
                
    def configure(self):
        ''' configures assembly by adding components, creating the workflow, and connecting the component i/o within the workflow '''

        self.add('drive', CSMDrivetrain())
        self.add('aero',aero_csm_component())
        self.add('aep',aep_csm_component())

        self.driver.workflow.add(['drive', 'aero', 'aep'])

        # connect inputs to component inputs
        self.connect('machine_rating', ['aero.machine_rating', 'drive.ratedPower'])
        self.connect('hub_height', ['aero.hub_height', 'aep.hub_height'])

        # connect i/o between components
        #self.connect('drive.drivetrain','aero.drivetrain')
        self.connect('aero.power_curve','drive.aeroPower')
        self.connect('drive.power',['aep.power_curve'])
        self.connect('aero.wind_curve', 'aep.wind_curve')
        self.connect('aep.power_array','power_curve')

        # create passthroughs for input variables
        # turbine
        self.connect('max_tip_speed','aero.max_tip_speed')
        self.connect('rotor_diameter','aero.rotor_diameter')
        self.connect('max_power_coefficient','aero.max_power_coefficient')
        self.connect('opt_tsr','aero.opt_tsr')
        self.connect('cut_in_wind_speed','aero.cut_in_wind_speed')
        self.connect('cut_out_wind_speed','aero.cut_out_wind_speed')
        self.connect('drivetrain_design','drive.drivetrainType')
        self.connect('thrust_coefficient','aero.thrust_coefficient')
        # plant
        self.connect('shear_exponent','aep.shear_exponent')
        self.connect('weibull_k','aep.weibull_k')
        self.connect('soiling_losses','aep.soiling_losses')
        self.connect('array_losses','aep.array_losses')
        self.connect('availability', 'aep.availability')
        self.connect('turbine_number','aep.turbine_number')
        self.connect('altitude','aero.altitude')
        self.connect('air_density','aero.air_density')

        # connect outputs
        self.connect('aero.rated_rotor_speed','rated_rotor_speed')
        self.connect('aero.rated_wind_speed', 'rated_wind_speed')
        self.connect('aero.rotor_thrust','rotor_thrust')
        self.connect('aero.rotor_torque','rotor_torque')
        self.connect('aero.max_efficiency', 'max_efficiency') #TODO: update maximum efficiency sourcing
        self.connect('aep.gross_aep', 'gross_aep')
        self.connect('aep.net_aep', 'net_aep')
        #self.connect('aep.capacity_factor', 'capacity_factor')
        #self.create_passthrough('aep.aep_per_turbine')

def example():

    aepA = aep_csm_assembly()

    aepA.machine_rating = 5000.0 # Float(units = 'kW', iotype='in', desc= 'rated machine power in kW')
    aepA.rotor_diameter = 126.0 # Float(units = 'm', iotype='in', desc= 'rotor diameter of the machine')
    aepA.max_tip_speed = 80.0 # Float(units = 'm/s', iotype='in', desc= 'maximum allowable tip speed for the rotor')
    aepA.drivetrain_design = 'geared' # Enum('geared', ('geared', 'single_stage', 'multi_drive', 'pm_direct_drive'), iotype='in')
    aepA.altitude = 0.0 # Float(0.0, units = 'm', iotype='in', desc= 'altitude of wind plant')
    aepA.turbine_number = 100 # Int(100, iotype='in', desc = 'total number of wind turbines at the plant')
    aepA.hub_height = 90.0 # Float(units = 'm', iotype='in', desc='hub height of wind turbine above ground / sea level')s
    aepA.max_power_coefficient = 0.488 #Float(0.488, iotype='in', desc= 'maximum power coefficient of rotor for operation in region 2')
    aepA.opt_tsr = 7.525 #Float(7.525, iotype='in', desc= 'optimum tip speed ratio for operation in region 2')
    aepA.cut_in_wind_speed = 3.0 #Float(3.0, units = 'm/s', iotype='in', desc= 'cut in wind speed for the wind turbine')
    aepA.cut_out_wind_speed = 25.0 #Float(25.0, units = 'm/s', iotype='in', desc= 'cut out wind speed for the wind turbine')
    aepA.hub_height = 90.0 #Float(90.0, units = 'm', iotype='in', desc= 'hub height of wind turbine above ground / sea level')
    aepA.altitude = 0.0 #Float(0.0, units = 'm', iotype='in', desc= 'altitude of wind plant')
    #aepA.air_density = Float(0.0, units = 'kg / (m * m * m)', iotype='in', desc= 'air density at wind plant site')  # default air density value is 0.0 - forces aero csm to calculate air density in model
    aepA.drivetrain_design = 'geared' #Enum('geared', ('geared', 'single_stage', 'multi_drive', 'pm_direct_drive'), iotype='in')
    aepA.shear_exponent = 0.1 #Float(0.1, iotype='in', desc= 'shear exponent for wind plant') #TODO - could use wind model here
    aepA.wind_speed_50m = 8.02 #Float(8.35, units = 'm/s', iotype='in', desc='mean annual wind speed at 50 m height')
    aepA.weibull_k= 2.15 #Float(2.1, iotype='in', desc = 'weibull shape factor for annual wind speed distribution')
    aepA.soiling_losses = 0.0 #Float(0.0, iotype='in', desc = 'energy losses due to blade soiling for the wind plant - average across turbines')
    aepA.array_losses = 0.10 #Float(0.06, iotype='in', desc = 'energy losses due to turbine interactions - across entire plant')
    aepA.availability = 0.941 #Float(0.94287630736, iotype='in', desc = 'average annual availbility of wind turbines at plant')
    aepA.turbine_number = 100 #Int(100, iotype='in', desc = 'total number of wind turbines at the plant')
    aepA.thrust_coefficient = 0.50 #Float(0.50, iotype='in', desc='thrust coefficient at rated power')

    aepA.run()
    
    print "5 MW reference turbine"
    print "rated rotor speed: {0}".format(aepA.rated_rotor_speed)
    print "rated wind speed: {0}".format(aepA.rated_wind_speed)
    print "maximum efficiency: {0}".format(aepA.max_efficiency)
    print "gross annual energy production: {0}".format(aepA.gross_aep)
    print "annual energy production: {0}".format(aepA.net_aep)
    print "Power Curve:"
    print aepA.power_curve
    print aepA.aep.net_aep

if __name__=="__main__":

    example()