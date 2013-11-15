"""
aep_csm_assembly.py

Created by NWTC Systems Engineering Sub-Task on 2012-08-01.
Copyright (c) NREL. All rights reserved.
"""

import sys, os, fileinput
import numpy as np

from openmdao.main.api import Component, Assembly, set_as_top, VariableTree
from openmdao.main.datatypes.api import Int, Bool, Float, Array, VarTree

from twister.components.drivetrain_csm_component import drive_csm_component
from twister.components.rotor_cst_component import RotorAeroComponent, WTPerfComponent, GeometryAero, Atmosphere, Controller, ref15MW_aero
from twister.components.aep_csm_component import aep_csm_component

class aep_cst_assembly(Assembly):

    # ---- Design Variables ----------
    # See passthrough variables below

    # ------------- Outputs -------------- 
    # See passthrough variables below

    def __init__(self):
        """ Creates a new AEP Assembly object """

        super(aep_cst_assembly, self).__init__()

                
    def configure(self):
        ''' configures assembly by adding components, creating the workflow, and connecting the component i/o within the workflow '''

        # Create assembly instances (mode swapping ocurrs here)
        self.SelectComponents()

        # Set up the workflow
        self.WorkflowAdd()

        # Connect the components
        self.WorkflowConnect()
    
    def execute(self):

        print "In {0}.execute()...".format(self.__class__)

        super(aep_cst_assembly, self).execute()  # will actually run the workflow

        pass
        
    
    #------- Supporting methods --------------
    
    def SelectComponents(self):

        drivec = drive_csm_component()
        self.add('drive', drivec)

        analysisc = WTPerfComponent() # only allowing WTPerf type of analysis at present
        self.add('anlsys', analysisc)
        
        aeroc = RotorAeroComponent()
        self.add('aero',aeroc)
        
        aepc = aep_csm_component()
        self.add('aep1',aepc)
        
    def WorkflowAdd(self):

        self.driver.workflow.add(['drive', 'anlsys', 'aero', 'aep1'])

    def WorkflowConnect(self):

        # create passthroughs for component inputs
        self.create_passthrough('aep1.ratedPower') # should be same variable as controller - slot passthrough issue
        self.create_passthrough('aep1.hubHeight') # should be same variable as atm - slot passthrough issue
        self.create_passthrough('drive.drivetrainDesign')
        self.create_passthrough('aero.control')
        self.create_passthrough('aero.ref_wind_speed')
        self.create_passthrough('aero.pitch_at_extreme_wind_load')
        self.create_passthrough('aero.npts_cp_curve')
        self.create_passthrough('aero.exclude_region25')
        self.create_passthrough('anlsys.atm')
        self.create_passthrough('anlsys.geometry')    
        self.create_passthrough('aep1.shearExponent') # should be same variable as atm - slot passthrough issue
        self.create_passthrough('aep1.windSpeed50m')
        self.create_passthrough('aep1.weibullK')
        self.create_passthrough('aep1.soilingLosses')
        self.create_passthrough('aep1.arrayLosses')
        self.create_passthrough('aep1.availability')
        self.create_passthrough('aep1.turbineNumber')      
        
        # connect i/o between components
        self.connect('drive.drivetrain','aero.drivetrain')
        self.connect('anlsys.analysis', 'aero.analysis')
        self.connect('aero.powerCurve','aep1.powerCurve')
 
        # create passthroughs for key output variables of interest
        self.create_passthrough('aero.ratedRotorSpeed')
        self.create_passthrough('aero.ratedWindSpeed')
        self.create_passthrough('aero.maxEfficiency')
        self.create_passthrough('aero.powerCurve')
        self.create_passthrough('aep1.aep')
        self.create_passthrough('aep1.aepPerTurbine')
        self.create_passthrough('aep1.capacityFactor')

if __name__=="__main__":

    # run default analysis
    aepA = aep_cst_assembly()
    #aepA.exclude_region25 = True

    control = Controller()
    aepA.control = control
    
    geometry = GeometryAero()
    aepA.geometry = geometry
    
    atm = Atmosphere()
    aepA.atm = atm
    
    aepA.execute()
    
    print "5 MW reference turbine"
    print "rated rotor speed: {0}".format(aepA.ratedRotorSpeed)
    print "rated wind speed: {0}".format(aepA.ratedWindSpeed)
    print "maximum efficiency: {0}".format(aepA.maxEfficiency)
    print "annual energy production: {0}".format(aepA.aep)
    print "annual energy production per turbine: {0}".format(aepA.aepPerTurbine)
    print "capacity factor: {0}".format(aepA.capacityFactor)
    print "Power Curve:"
    print aepA.powerCurve

    f = open('wtp_scratch\powercurve5.txt', 'w')
    for i in xrange(0,aepA.powerCurve.shape[1]):
    		print >> f, '{0}, {1}'.format(aepA.powerCurve[0,i], aepA.powerCurve[1,i])
    f.close()

    '''# increase rotor diameter by 10%
    r = np.copy(aepA.geometry.r) * 1.1
    r_af = np.copy(aepA.geometry.r_af) * 1.1
    aepA.geometry.r_af = r_af
    aepA.geometry.r = r

    aepA.execute()
    
    print "5 MW reference turbine"
    print "rated rotor speed: {0}".format(aepA.ratedRotorSpeed)
    print "rated wind speed: {0}".format(aepA.ratedWindSpeed)
    print "maximum efficiency: {0}".format(aepA.maxEfficiency)
    print "annual energy production: {0}".format(aepA.aep)
    print "annual energy production per turbine: {0}".format(aepA.aepPerTurbine)
    print "capacity factor: {0}".format(aepA.capacityFactor)
    print "Power Curve:"
    print aepA.powerCurve

    # test 1.5 MW
    
    aepA.ratedPower = 1500.0
    aepA.hubHeight = 80.0
    #aepA.exclude_region25 = True

    control = Controller()
    control.ratedPower = 1.5e6
    control.maxOmega = 21.8
    aepA.control = control
    
    geometry = GeometryAero()
    r_aero, af = ref15MW_aero()  # defaults to 5MW model
    geometry.r_af = r_aero
    geometry.afarr = af
    geometry.r = [1.75, 7.875, 13.125, 23.625, 35.0]
    geometry.chord = [2.149, 2.7237, 2.3912, 1.64745, 0.96145]
    geometry.theta = [11.1, 10.496, 6.098, 1.186, 0.06]
    geometry.precone = 0.0
    geometry.tilt = 5.0
    aepA.geometry = geometry
    
    atm = Atmosphere()
    atm.hubHt = 85.295
    aepA.atm = atm
    
    aepA.execute()
    
    print "1.5 MW reference turbine"
    print "rated rotor speed: {0}".format(aepA.ratedRotorSpeed)
    print "rated wind speed: {0}".format(aepA.ratedWindSpeed)
    print "maximum efficiency: {0}".format(aepA.maxEfficiency)
    print "annual energy production: {0}".format(aepA.aep)
    print "annual energy production per turbine: {0}".format(aepA.aepPerTurbine)
    print "capacity factor: {0}".format(aepA.capacityFactor)
    print "Power Curve:"
    print aepA.powerCurve

    f = open('wtp_scratch\powercurve15.txt', 'w')
    for i in xrange(0,aepA.powerCurve.shape[1]):
    		print >> f, '{0}, {1}'.format(aepA.powerCurve[0,i], aepA.powerCurve[1,i])
    f.close()'''