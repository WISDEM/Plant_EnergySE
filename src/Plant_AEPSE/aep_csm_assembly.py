"""
aep_csm_assembly.py

Created by NWTC Systems Engineering Sub-Task on 2012-08-01.
Copyright (c) NREL. All rights reserved.
"""

import sys, os, fileinput
import numpy as np

from openmdao.main.api import Component, Assembly, set_as_top, VariableTree
from openmdao.main.datatypes.api import Int, Bool, Float, Array, VarTree

from twister.models.csm.csmDriveEfficiency import DrivetrainEfficiencyModel

from twister.components.drivetrain_csm_component import drive_csm_component
from twister.components.aero_csm_component import aero_csm_component
from twister.components.aep_csm_component import aep_csm_component

class aep_csm_assembly(Assembly):

    # ---- Design Variables ----------
    
    # Turbine configuration
    # rotor
    ratedPower = Float(5000.0, units = 'kW', iotype='in', desc= 'rated machine power in kW')
    # tower / substructure
    hubHeight = Float(90.0, units = 'm', iotype='in', desc='hub height of wind turbine above ground / sea level')

    # See passthrough for additional variable

    # ------------- Outputs -------------- 
    # See passthrough variables below

    def __init__(self):
        """ 
        Creates a new AEP Assembly object 
        
        """

        super(aep_csm_assembly, self).__init__()

                
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

        super(aep_csm_assembly, self).execute()  # will actually run the workflow

        pass
        
    
    #------- Supporting methods --------------
    
    def SelectComponents(self):

        drivec = drive_csm_component()
        self.add('drive', drivec)
        
        aeroc = aero_csm_component()
        self.add('aero',aeroc)
        
        aepc = aep_csm_component()
        self.add('aep1',aepc)
        
    def WorkflowAdd(self):

        self.driver.workflow.add(['drive', 'aero', 'aep1'])

    def WorkflowConnect(self):

        # connect inputs to component inputs
        # turbine configuration
        # rotor
        self.connect('ratedPower', ['aero.ratedPower', 'aep1.ratedPower'])
        # tower
        self.connect('hubHeight', ['aero.hubHeight', 'aep1.hubHeight'])

        # connect i/o between components
        self.connect('drive.drivetrain','aero.drivetrain')
        self.connect('aero.powerCurve','aep1.powerCurve')
        
        # create passthroughs for input variables
        # turbine
        self.create_passthrough('aero.maxTipSpeed')
        self.create_passthrough('aero.rotorDiameter')
        self.create_passthrough('aero.maxPowerCoefficient')
        self.create_passthrough('aero.optTipSpeedRatio')
        self.create_passthrough('aero.cutInWindSpeed')
        self.create_passthrough('aero.cutOutWindSpeed')
        self.create_passthrough('drive.drivetrainDesign')
        # plant
        self.create_passthrough('aep1.shearExponent')
        self.create_passthrough('aep1.windSpeed50m')
        self.create_passthrough('aep1.weibullK')
        self.create_passthrough('aep1.soilingLosses')
        self.create_passthrough('aep1.arrayLosses')
        self.create_passthrough('aep1.availability')
        self.create_passthrough('aep1.turbineNumber')
        self.create_passthrough('aero.altitude')
        self.create_passthrough('aero.airDensity')

        # create passthroughs for key output variables of interest
        self.create_passthrough('aero.ratedRotorSpeed')
        self.create_passthrough('aero.ratedWindSpeed')
        self.create_passthrough('aero.maxEfficiency')
        self.create_passthrough('aero.powerCurve')
        self.create_passthrough('aep1.aep')
        self.create_passthrough('aep1.aepPerTurbine')
        self.create_passthrough('aep1.capacityFactor')

if __name__=="__main__":

    aepA = aep_csm_assembly()
    
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