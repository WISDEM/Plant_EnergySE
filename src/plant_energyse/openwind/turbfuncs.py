# turbfuncs.py
# 2014 04 15

''' Functions to convert between OpenWind and FUSED-Wind representations
    of wind turbines
'''

"""
class GenericWindTurbinePowerCurveVT(GenericWindTurbineVT):
    hub_height = Float(desc='Machine hub height', unit='m')
    rotor_diameter = Float(desc='Machine rotor diameter', unit='m')
    power_rating = Float(desc='Machine power rating', unit='W') 

    c_t_curve = Array(desc='Machine thrust coefficients by wind speed at hub')
    power_curve = Array(desc='Machine power output [W] by wind speed at hub')
    cut_in_wind_speed = Float(desc='The cut-in wind speed of the wind turbine', unit='m/s') 
    cut_out_wind_speed = Float(desc='The cut-out wind speed of the wind turbine', unit='m/s') 
    rated_wind_speed = Float(desc='The rated wind speed of the wind turbine', unit='m/s')
    air_density = Float(desc='The air density the power curve are valid for', unit='kg/(m*m*m)')
class ExtendedWindTurbinePowerCurveVT(GenericWindTurbinePowerCurveVT):
    rpm_curve = Array(desc='Machine rpm [rpm] by wind speed at hub') 
    pitch_curve = Array(desc='The wind turbine pitch curve', unit='deg') 
    
"""
import sys, os
import rwTurbXML
import numpy as np
from lxml import etree

#from fused_plant_vt import GenericWindTurbineVT, GenericWindTurbinePowerCurveVT, \
#                           ExtendedWindTurbinePowerCurveVT, GenericWindFarmTurbineLayout
#from fusedwind.plant_flow.fused_plant_vt import GenericWindTurbineVT, GenericWindTurbinePowerCurveVT, \
#                           ExtendedWindTurbinePowerCurveVT, GenericWindFarmTurbineLayout
# 2014 09 22: using new fusedwind vt.py
from fusedwind.plant_flow.vt import GenericWindTurbineVT, GenericWindTurbinePowerCurveVT, \
     ExtendedWindTurbinePowerCurveVT, GenericWindFarmTurbineLayout, \
     GenericWindRoseVT

#---------------------------------------------

def owtg_to_wtpc(owtg_file):
    ''' convert OWTG turbine definition file for openWind to FUSED-Wind ExtendedWindTurbinePowerCurveVT '''
    
    wtpc = ExtendedWindTurbinePowerCurveVT()
    tree = rwTurbXML.parseOWTG(owtg_file)
    
    if tree is None:
        sys.stderr.write('\n*** ERROR: could not parse turbine file "{:}"\n\n"'.format(owtg_file))
        return None
    
    vels, pwrs = rwTurbXML.getPwrTbls(tree)
    wtpc.power_curve = np.array([vels, pwrs]).transpose()
    
    vels, thrusts = rwTurbXML.getThrustTbls(tree)
    wtpc.c_t_curve = np.array([vels, thrusts]).transpose()
    
    vels, rpms = rwTurbXML.getRPMTbls(tree)
    wtpc.rpm_curve = np.array([vels, rpms]).transpose()
    
    name, capKW, hubHt, rtrDiam = rwTurbXML.getTurbParams(tree)
    wtpc.hub_height = hubHt
    wtpc.rotor_diameter = rtrDiam
    wtpc.power_rating = 1000.0 * capKW
    
    return wtpc

#---------------------------------------------

def wtpc_to_owtg(wtpc, trbname='GenericTurbine', desc='GenericDescription'):
    ''' convert FUSED-Wind ExtendedWindTurbinePowerCurveVT to OWTG string for openWind '''
    
    #rpm = [0.0 for i in range(wtpc.power_curve.shape[0]) ] 
    # rpm not stored in GenericWindTurbinePowerCurveVT
    #  but it is in Extended...
    
    #sys.stderr.write('{:}\n'.format(wtpc.power_curve.__class__))
    if wtpc.power_curve.ndim < 2:
        sys.stderr.write('\n*** WARNING wtpc_to_owtg(): wtpc power curve not specified\n\n')
        return ''
    
    turbtree = rwTurbXML.newTurbTree(trbname, desc,
        wtpc.power_curve[:,0], 
        wtpc.power_curve[:,1], 
        wtpc.c_t_curve[:,1], 
        wtpc.rpm_curve[:,1], 
        wtpc.hub_height, 
        wtpc.rotor_diameter, 
        machineRating=wtpc.power_rating*0.001)
        
    turbXML = etree.tostring(turbtree, 
                             xml_declaration=True,
                             doctype='<!DOCTYPE {:}>'.format(trbname), 
                             pretty_print=True)
    return turbXML

#---------------------------------------------

def wtpc_dump(wtpc, shortFmt=False):
    ''' dump FUSED-Wind ExtendedWindTurbinePowerCurveVT contents to string '''
    s = 'Dump of ExtendedWindTurbinePowerCurveVT\n'
    s = s + '  HH {:5.1f}m\n  RD {:5.1f}m\n  PR {:7.1f}kW\n'.format(wtpc.hub_height, wtpc.rotor_diameter, wtpc.power_rating)
    if len(wtpc.power_curve) < 1:
        s = s + '  *** No Power Curve specified!\n'
    
    if shortFmt:    
        for i in range(len(wtpc.power_curve)):
            s = s + ' {:7.1f}'.format(wtpc.power_curve[i,0])
        s = s + '\n'
        for i in range(len(wtpc.power_curve)):
            s = s + ' {:7.1f}'.format(wtpc.power_curve[i,1])
        s = s + '\n'
    else:
        for i in range(len(wtpc.power_curve)):
            s = s + '    {:4.1f} mps {:7.1f} kW\n'.format(wtpc.power_curve[i,0], wtpc.power_curve[i,1])
        
    return  s
     
#------------------------------------------------------------------

if __name__ == "__main__":

    # Read OWTG file and convert to ExtendedWindTurbinePowerCurveVT
    
    #owtg_name = 'C:/SystemsEngr/test/Alstom6MW.owtg'
    owtg_name = 'test/Alstom6MW.owtg'
    wtpc = owtg_to_wtpc(owtg_name)
    
    # Convert back to OWTG
    
    txml = wtpc_to_owtg(wtpc)
    print txml
    
    s = wtpc_dump(wtpc)
    print s
       