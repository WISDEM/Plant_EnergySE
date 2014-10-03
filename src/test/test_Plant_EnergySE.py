#!/usr/bin/env python
# encoding: utf-8
"""
test_Plant_EnergySE.py

Created by Katherine Dykes on 2014-01-07.
Copyright (c) NREL. All rights reserved.
"""


import unittest
import numpy as np
from commonse.utilities import check_gradient_unit_test
from plant_energyse.basic_aep.basic_aep import aep_component, WeibullCDF, RayleighCDF, BasicAEP
from plant_energyse.nrel_csm_aep.nrel_csm_aep import aep_csm_assembly
from plant_energyse.nrel_csm_aep.aep_csm_component import weibull, aep_csm_component
from plant_energyse.nrel_csm_aep.aero_csm_component import aero_csm_component
from plant_energyse.nrel_csm_aep.CSMDrivetrain import CSMDrivetrain


# Basic AEP model tests

class Test_WeibullCDF(unittest.TestCase):

    def setUp(self):

        self.cdf = WeibullCDF()

        self.cdf.x = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0,
                 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0, 21.0, 22.0, 23.0, 24.0, 25.0, 26.0]

        self.cdf.A = 8.35
        self.cdf.k = 2.15

    def test_functionality(self):
        
        self.cdf.run()
        
        F = np.array([0.01037793,  0.04524528,  0.10480121,  0.18575653,  0.28252447,  0.38820584,
              0.49562699,  0.59829918,  0.69114560,  0.77089646,  0.83613421,  0.88704769,
              0.92500346,  0.95205646,  0.97050303,  0.98254137,  0.99006279,  0.99456267,
              0.99714093,  0.99855575,  0.99929934,  0.99967365,  0.9998541,   0.99993741,
              0.99997424,  0.99998983])
        
        self.assertEqual(self.cdf.F.all(), F.all())

    def test_gradient(self):

        check_gradient_unit_test(self, self.cdf, display=False)

class Test_RayleighCDF(unittest.TestCase):

    def setUp(self):

        self.cdf = RayleighCDF()
        self.cdf.x = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0,
                 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0, 21.0, 22.0, 23.0, 24.0, 25.0, 26.0]
        self.cdf.xbar = 8.35

    def test_functionality(self):
        
        self.cdf.run()
      
        F = np.array([0.01120142,  0.04405846,  0.09641191,  0.16492529,  0.24543643,  0.33337438,
                      0.42418386,  0.51370329,  0.59845474,  0.67582215,  0.74411323,  0.80251778,
                      0.85098711,  0.89006516,  0.92070195,  0.94407508,  0.96143762,  0.97400212,
                      0.98286327,  0.98895582,  0.99304088,  0.99571263,  0.99741748,  0.99847906,
                      0.99912422,  0.99950695])
        
        self.assertEqual(self.cdf.F.all(), F.all())

    def test_gradient(self):

        check_gradient_unit_test(self, self.cdf, display=False)

class Test_aep_component(unittest.TestCase):

    def setUp(self):

        self.aep = aep_component()
        self.aep.power_curve = [
            0.0, 0.0, 0.0, 187.0, 350.0, 658.30, 1087.4, 1658.3, 2391.5, 3307.0, 4415.70,
            5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0,
            5000.0, 5000.0, 0.0]
        self.aep.CDF_V = [
            0.010, 0.045, 0.105, 0.186, 0.283, 0.388, 0.496, 0.598, 0.691, 0.771, 0.836,
            0.887, 0.925, 0.952, 0.971, 0.983, 0.990, 0.995, 0.997, 0.999, 0.999, 1.000, 1.000,
            1.000, 1.000, 1.000]

    def test_functionality(self):
        
        self.aep.run()
        
        self.assertEqual(round(self.aep.net_aep,1), 1389470583.4)

    def test_gradient(self):

        check_gradient_unit_test(self, self.aep, step_size=1.0, display=False)

class TestBasicAEP(unittest.TestCase):

    def setUp(self):

        self.aep = BasicAEP()

        self.aep.AEP_one_turbine = 75.4
        self.aep.array_losses = 0.059
        self.aep.other_losses = 0.0
        self.aep.availability = 0.94
        self.aep.turbine_number = 100

    def test_functionality(self):
        
        self.aep.run()
        
        self.assertEqual(round(self.aep.net_aep,1), 6669.4)

    def test_gradient(self):

        check_gradient_unit_test(self, self.aep)


# -------------------------------------------------------------------------------
# NREL CSM AEP

class Testnrel_csm_aep(unittest.TestCase):

    def setUp(self):

        self.aep = aep_csm_assembly()

        self.aep.machine_rating = 5000.0 # Float(units = 'kW', iotype='in', desc= 'rated machine power in kW')
        self.aep.rotor_diameter = 126.0 # Float(units = 'm', iotype='in', desc= 'rotor diameter of the machine')
        self.aep.max_tip_speed = 80.0 # Float(units = 'm/s', iotype='in', desc= 'maximum allowable tip speed for the rotor')
        self.aep.drivetrain_design = 'geared' # Enum('geared', ('geared', 'single_stage', 'multi_drive', 'pm_direct_drive'), iotype='in')
        self.aep.altitude = 0.0 # Float(0.0, units = 'm', iotype='in', desc= 'altitude of wind plant')
        self.aep.turbine_number = 100 # Int(100, iotype='in', desc = 'total number of wind turbines at the plant')
        self.aep.hub_height = 90.0 # Float(units = 'm', iotype='in', desc='hub height of wind turbine above ground / sea level')s
        self.aep.max_power_coefficient = 0.488 #Float(0.488, iotype='in', desc= 'maximum power coefficient of rotor for operation in region 2')
        self.aep.opt_tsr = 7.525 #Float(7.525, iotype='in', desc= 'optimum tip speed ratio for operation in region 2')
        self.aep.cut_in_wind_speed = 3.0 #Float(3.0, units = 'm/s', iotype='in', desc= 'cut in wind speed for the wind turbine')
        self.aep.cut_out_wind_speed = 25.0 #Float(25.0, units = 'm/s', iotype='in', desc= 'cut out wind speed for the wind turbine')
        self.aep.hub_height = 90.0 #Float(90.0, units = 'm', iotype='in', desc= 'hub height of wind turbine above ground / sea level')
        self.aep.altitude = 0.0 #Float(0.0, units = 'm', iotype='in', desc= 'altitude of wind plant')
        #self.aep.air_density = Float(0.0, units = 'kg / (m * m * m)', iotype='in', desc= 'air density at wind plant site')  # default air density value is 0.0 - forces aero csm to calculate air density in model
        self.aep.drivetrain_design = 'geared' #Enum('geared', ('geared', 'single_stage', 'multi_drive', 'pm_direct_drive'), iotype='in')
        self.aep.shear_exponent = 0.1 #Float(0.1, iotype='in', desc= 'shear exponent for wind plant') #TODO - could use wind model here
        self.aep.wind_speed_50m = 8.02 #Float(8.35, units = 'm/s', iotype='in', desc='mean annual wind speed at 50 m height')
        self.aep.weibull_k= 2.15 #Float(2.1, iotype='in', desc = 'weibull shape factor for annual wind speed distribution')
        self.aep.soiling_losses = 0.0 #Float(0.0, iotype='in', desc = 'energy losses due to blade soiling for the wind plant - average across turbines')
        self.aep.array_losses = 0.10 #Float(0.06, iotype='in', desc = 'energy losses due to turbine interactions - across entire plant')
        self.aep.availability = 0.941 #Float(0.94287630736, iotype='in', desc = 'average annual availbility of wind turbines at plant')
        self.aep.turbine_number = 100 #Int(100, iotype='in', desc = 'total number of wind turbines at the plant')
        self.aep.thrust_coefficient = 0.50 #Float(0.50, iotype='in', desc='thrust coefficient at rated power')

    def test_functionality(self):
        
        self.aep.run()
        
        self.assertEqual(round(self.aep.net_aep,1), 1691553683.6)

class Testaep_csm_component(unittest.TestCase):

    def setUp(self):

        self.aep = aep_csm_component()

        self.aep.power_curve = [0.0, 0.0, 0.0, 0.0, 187.0, 350.0, 658.30, 1087.4, 1658.3, 2391.5, 3307.0, \
                              4415.70, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, \
                              5000.0, 5000.0, 5000.0, 5000.0, 0.0]
        self.aep.wind_curve = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, \
                               11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0, 21.0, 22.0, 23.0, 24.0, 25.0, 26.0]
        self.aep.hub_height = 90.0 #Float(90.0, units = 'm', iotype='in', desc= 'hub height of wind turbine above ground / sea level')
        self.aep.shear_exponent = 0.1 #Float(0.1, iotype='in', desc= 'shear exponent for wind plant') #TODO - could use wind model here
        self.aep.wind_speed_50m = 8.35 #Float(8.35, units = 'm/s', iotype='in', desc='mean annual wind speed at 50 m height')
        self.aep.weibull_k= 2.1 #Float(2.1, iotype='in', desc = 'weibull shape factor for annual wind speed distribution')

    def test_functionality(self):
        
        self.aep.run()
        
        self.assertEqual(round(self.aep.net_aep,1), 1862105019.6)

class Testaero_csm_component(unittest.TestCase):

    def setUp(self):

        self.aero = aero_csm_component()

        self.aero.machine_rating = 5000.0
        self.aero.max_tip_speed = 80.0
        self.aero.rotor_diameter = 126.0
        self.aero.max_power_coefficient = 0.488
        self.aero.opt_tsr = 7.525
        self.aero.cut_in_wind_speed = 3.0
        self.aero.cut_out_wind_speed = 25.0
        self.aero.hub_height = 90.0
        self.aero.altitude = 0.0
        self.aero.air_density = 0.0
        self.aero.max_efficiency = 0.902
        self.aero.thrust_coefficient = 0.50

    def test_functionality(self):
        
        self.aero.run()
        
        self.assertEqual(round(self.aero.rated_rotor_speed,1), 12.1)

# Currently excluding tests for CSMDrivetrain - likely moving to another location

# -------------------------------------------------------------------------------
# Openwind

if __name__ == "__main__":
    unittest.main()
