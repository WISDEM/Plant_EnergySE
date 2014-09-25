# 1 ---------

# A simple test of the basic_aep model
from basic_aep.basic_aep import aep_weibull_assembly
import numpy as np

aeptest = aep_weibull_assembly()


# 1 ---------
# 2 ---------

# Set input parameters

aeptest.wind_curve = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, \
                           11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0, 21.0, 22.0, 23.0, 24.0, 25.0, 26.0])
aeptest.power_curve = np.array([0.0, 0.0, 0.0, 187.0, 350.0, 658.30, 1087.4, 1658.3, 2391.5, 3307.0, 4415.70, \
                          5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, \
                          5000.0, 5000.0, 0.0])
aeptest.A = 8.35
aeptest.k = 2.15

# 2 ---------
# 3 ---------

aeptest.run()

# 3 ---------
# 4 --------- 

print "AEP gross output: {0}".format(aeptest.gross_aep)
print "AEP output: {0}".format(aeptest.net_aep)
print

# 4 ----------
# 5 ----------

# A simple test of nrel_csm_aep model
from nrel_csm_aep.nrel_csm_aep import aep_csm_assembly

aepA = aep_csm_assembly()

# 5 ---------- 
# 6 ----------

# Set input parameters

# 6 ----------
# 7 ----------

aepA.run()

# 7 ----------
# 8 ----------

print "5 MW reference turbine"
print "rated rotor speed: {0}".format(aepA.rated_rotor_speed)
print "rated wind speed: {0}".format(aepA.rated_wind_speed)
print "maximum efficiency: {0}".format(aepA.max_efficiency)
print "gross annual energy production: {0}".format(aepA.gross_aep)
print "annual energy production: {0}".format(aepA.net_aep)
print "Power Curve:"
print aepA.power_curve

# 8 -----------