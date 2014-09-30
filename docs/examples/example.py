# 1 ---------

# A simple test of the basic_aep model
from plant_energyse.basic_aep.basic_aep import aep_weibull_assembly
import numpy as np

aep = aep_weibull_assembly()


# 1 ---------
# 2 ---------

# Set input parameters

aep.wind_curve = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, \
                           11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0, 21.0, 22.0, 23.0, 24.0, 25.0, 26.0])
aep.power_curve = np.array([0.0, 0.0, 0.0, 187.0, 350.0, 658.30, 1087.4, 1658.3, 2391.5, 3307.0, 4415.70, \
                          5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, \
                          5000.0, 5000.0, 0.0])
aep.A = 8.35
aep.k = 2.15
aep.array_losses = 0.059
aep.other_losses = 0.0
aep.availability = 0.94
aep.turbine_number = 100

# 2 ---------
# 3 ---------

aep.run()

# 3 ---------
# 4 --------- 

print "Annual energy production for an offshore wind plant with 100 NREL 5 MW reference turbines."
print "AEP gross output (before losses): {0:.1f} kWh".format(aep.gross_aep)
print "AEP net output (after losses): {0:.1f} kWh".format(aep.net_aep)
print

# 4 ----------
# 5 ----------

# A simple test of nrel_csm_aep model
from plant_energyse.nrel_csm_aep.nrel_csm_aep import aep_csm_assembly

aep = aep_csm_assembly()

# 5 ---------- 
# 6 ----------

# Set input parameters
aep.machine_rating = 5000.0 # Float(units = 'kW', iotype='in', desc= 'rated machine power in kW')
aep.rotor_diameter = 126.0 # Float(units = 'm', iotype='in', desc= 'rotor diameter of the machine')
aep.max_tip_speed = 80.0 # Float(units = 'm/s', iotype='in', desc= 'maximum allowable tip speed for the rotor')
aep.drivetrain_design = 'geared' # Enum('geared', ('geared', 'single_stage', 'multi_drive', 'pm_direct_drive'), iotype='in')
aep.altitude = 0.0 # Float(0.0, units = 'm', iotype='in', desc= 'altitude of wind plant')
aep.turbine_number = 100 # Int(100, iotype='in', desc = 'total number of wind turbines at the plant')
aep.hub_height = 90.0 # Float(units = 'm', iotype='in', desc='hub height of wind turbine above ground / sea level')s
aep.max_power_coefficient = 0.488 #Float(0.488, iotype='in', desc= 'maximum power coefficient of rotor for operation in region 2')
aep.opt_tsr = 7.525 #Float(7.525, iotype='in', desc= 'optimum tip speed ratio for operation in region 2')
aep.cut_in_wind_speed = 3.0 #Float(3.0, units = 'm/s', iotype='in', desc= 'cut in wind speed for the wind turbine')
aep.cut_out_wind_speed = 25.0 #Float(25.0, units = 'm/s', iotype='in', desc= 'cut out wind speed for the wind turbine')
aep.hub_height = 90.0 #Float(90.0, units = 'm', iotype='in', desc= 'hub height of wind turbine above ground / sea level')
#aep.air_density = Float(0.0, units = 'kg / (m * m * m)', iotype='in', desc= 'air density at wind plant site')  # default air density value is 0.0 - forces aero csm to calculate air density in model
aep.shear_exponent = 0.1 #Float(0.1, iotype='in', desc= 'shear exponent for wind plant') #TODO - could use wind model here
aep.wind_speed_50m = 8.02 #Float(8.35, units = 'm/s', iotype='in', desc='mean annual wind speed at 50 m height')
aep.weibull_k= 2.15 #Float(2.1, iotype='in', desc = 'weibull shape factor for annual wind speed distribution')
aep.soiling_losses = 0.0 #Float(0.0, iotype='in', desc = 'energy losses due to blade soiling for the wind plant - average across turbines')
aep.array_losses = 0.10 #Float(0.06, iotype='in', desc = 'energy losses due to turbine interactions - across entire plant')
aep.availability = 0.941 #Float(0.94287630736, iotype='in', desc = 'average annual availbility of wind turbines at plant')
aep.thrust_coefficient = 0.50 #Float(0.50, iotype='in', desc='thrust coefficient at rated power')

# 6 ----------
# 7 ----------

aep.run()

# 7 ----------
# 8 ----------

print "Annual energy production for an offshore wind plant with 100 NREL 5 MW reference turbines."    
print "AEP gross output (before losses): {0:.1f} kWh".format(aep.gross_aep)
print "AEP net output (after losses): {0:.1f} kWh".format(aep.net_aep)
print "Rated rotor speed: {0:.2f} rpm".format(aep.rated_rotor_speed)
print "Rated wind speed: {0:.2f} m/s".format(aep.rated_wind_speed)

# 8 -----------
# 9 -----------

from plant_energyse.openwind.enterprise.openwind_assembly import openwind_assembly

# 9 -----------
# 10 ----------

# set file inputs from test folder
test_path = '../test/'
workbook_path = test_path + 'VA_test.blb'
turbine_name = 'Alstom Haliade 150m 6MW' # should match default turbine in workbook
script_file = test_path + 'ecScript.xml'

if not os.path.isfile(script_file):
    sys.stderr.write('OpenWind script file "{:}" not found\n'.format(script_file))
    exit()

if not os.path.isfile(owExe):
    sys.stderr.write('OpenWind executable file "{:}" not found\n'.format(owExe))
    exit()

owAsm = openwind_assembly(owExe, workbook_path, turbine_name=turbine_name, script_file=script_file,
                          debug=debug)

owAsm.updateRptPath('newReport.txt', 'newTestScript.xml')

# 10 -----------
# 11 -----------

owAsm.power_curve = np.array([[1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, \
                       11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0, 21.0, 22.0, 23.0, 24.0, 25.0, 26.0], \
                      [0.0, 0.0, 0.0, 187.0, 350.0, 658.30, 1087.4, 1658.3, 2391.5, 3307.0, \
                      4415.70, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, \
                      5000.0, 5000.0, 5000.0, 5000.0, 0.0]])

owAsm.ct = np.array([[1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, \
                       11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0, 21.0, 22.0, 23.0, 24.0, 25.0, 26.0], \
                      [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, \
                       1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]])

owAsm.rpm = np.array([[1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, \
                       11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0, 21.0, 22.0, 23.0, 24.0, 25.0, 26.0], \
                      [7.0, 7.0, 7.0, 7.0, 7.0, 7.0, 7.0, 7.0, 7.0, 7.0, \
                       7.0, 7.0, 7.0, 7.0, 7.0, 7.0, 7.0, 7.0, 7.0, 7.0, 7.0, 7.0, 7.0, 7.0, 7.0, 7.0]])

# 11 -----------
# 12 -----------

owAsm.run() # run the openWind process

# 12 -----------
# 13 -----------

otherLosses = 1.0 - (owAsm.net_aep/owAsm.array_aep)

print 'Openwind assembly output:'
print '  AEP gross output (before losses): {:.1f} kWh'.format(owAsm.gross_aep*0.001)
print '  Array losses: {:.2f} %'.format(owAsm.array_losses*100.0)
print '  Array energy production: {:.1f} kWh'.format(owAsm.array_aep*0.001)
print '  Other losses: {:.2f} %'.format(otherLosses*100.0)
print '  AEP net output: (after losses) {:.1f} kWh'.format(owAsm.net_aep*0.001)
print '  Capacity factor: {:.2f} %'.format(owAsm.capacity_factor*100.0)

# 13 -----------