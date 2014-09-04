# 1 ---------

# A simple test of nrel_csm_bos model
from nrel_csm_bos.nrel_csm_bos import bos_csm_assembly

bos = bos_csm_assembly()

# 1 ---------
# 2 ---------

# Set input parameters
bos.machine_rating = 5000.0
bos.rotor_diameter = 126.0
bos.turbine_cost = 5950209.283
bos.turbine_number = 100
bos.hub_height = 90.0
bos.RNA_mass = 256634.5 # RNA mass is not used in this simple model

# 2 ---------
# 3 ---------

bos.run()

# 3 ---------
# 4 --------- 

print "BOS cost offshore: {0}".format(bos.bos_costs)
print "BOS cost per turbine: {0}".format(bos.bos_costs / bos.turbine_number)
print

# 4 ----------
# 5 ----------

bos.sea_depth = 0.0
bos.turbine_cost = 5229222.77
bos.run()
print "BOS cost onshore: {0}".format(bos.bos_costs)
print "BOS cost per turbine: {0}".format(bos.bos_costs / bos.turbine_number)
print

# 5 ---------- 
# 6 ----------

# A simple test of nrel_csm_om model
from nrel_csm_om.nrel_csm_om import om_csm_assembly

om = om_csm_assembly()

# 6 ----------
# 7 ----------

# Ste input parameters
om.machine_rating = 5000.0 # Need to manipulate input or underlying component will not execute
om.net_aep = 1701626526.28
om.sea_depth = 20.0
om.year = 2010
om.month = 12
om.turbine_number = 100

# 7 ----------
# 8 ----------

om.run()

# 8 -----------
# 9 -----------

print "OM offshore {:.1f}".format(om.avg_annual_opex)
print "OM by turbine {0}".format(om.OPEX_breakdown.preventative_opex / om.turbine_number)
print "LRC by turbine {0}".format(om.OPEX_breakdown.corrective_opex / om.turbine_number)
print "LLC by turbine {0}".format(om.OPEX_breakdown.lease_opex / om.turbine_number)
print

# 9 -----------
# 10 -----------

om.sea_depth = 0.0
om.run()
print "OM onshore {:.1f}".format(om.avg_annual_opex)
print "OM by turbine {0}".format(om.OPEX_breakdown.preventative_opex / om.turbine_number)
print "LRC by turbine {0}".format(om.OPEX_breakdown.corrective_opex / om.turbine_number)
print "LLC by turbine {0}".format(om.OPEX_breakdown.lease_opex / om.turbine_number)

# 10 -----------
# 11 ----------

# A simple test of ecn_offshore_om model
from ecn_offshore_om.ecn_offshore_om import om_ecn_assembly

om2 = om_ecn_assembly('C:/Models/ECN Model/ECN O&M Model.xls')

# 11 ----------
# 12 ----------

# Set input parameters
om2.machine_rating = 5000.0
om2.turbine_cost = 9000000.0
om2.turbine_number = 100
om2.project_lifetime = 20

# 12 ----------
# 13 ----------

om2.run()

# 13 ----------
# 14 ----------

print "Availability {:.1f}% ".format(om2.availability*100.0)
print "OnM Annual Costs ${:.3f} ".format(om2.avg_annual_opex)
print "OM by turbine {0}".format(om2.OPEX_breakdown.preventative_opex / om2.turbine_number)
print "LRC by turbine {0}".format(om2.OPEX_breakdown.corrective_opex / om2.turbine_number)
print "LLC by turbine {0}".format(om2.OPEX_breakdown.lease_opex / om2.turbine_number)

# 14 ----------