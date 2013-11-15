"""
aep_csm_assembly.py

Created by NWTC Systems Engineering Sub-Task on 2012-08-01.
Copyright (c) NREL. All rights reserved.
"""

import sys, os, fileinput
import numpy as np

from openmdao.main.api import Component, Assembly, set_as_top, VariableTree
from openmdao.main.datatypes.api import Int, Bool, Float, Array, VarTree

from fusedwind.plant_flow.fused_plant_asym import GenericAEPModel

from NREL_CSM.csmDriveEfficiency import DrivetrainEfficiencyModel
from drivetrain_csm_component import drive_csm_component
from aero_csm_component import aero_csm_component
from aep_csm_component import aep_csm_component

class aep_csm_assembly(GenericAEPModel):

    # ---- Design Variables ----------
    ratedPower = Float(5000.0, units = 'kW', iotype='in', desc= 'rated machine power in kW')
    hubHeight = Float(90.0, units = 'm', iotype='in', desc='hub height of wind turbine above ground / sea level')

    def __init__(self):
        """ 
        Creates a new AEP Assembly object 
        
        """

        super(aep_csm_assembly, self).__init__()

                
    def configure(self):
        ''' configures assembly by adding components, creating the workflow, and connecting the component i/o within the workflow '''

        super(aep_csm_assembly, self).configure()

        self.add('drive', drive_csm_component())
        self.add('aero',aero_csm_component())
        self.add('aep1',aep_csm_component())

        self.driver.workflow.add(['drive', 'aero', 'aep1'])


        # connect inputs to component inputs
        self.connect('ratedPower', ['aero.ratedPower', 'aep1.ratedPower'])
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

        # outputs
        self.connect('aep1.gross_aep', 'gross_aep')
        self.connect('aep1.net_aep', 'net_aep')
        self.connect('aep1.capacity_factor', 'capacity_factor')
        self.create_passthrough('aep1.aep_per_turbine')
    
    def execute(self):

        print "In {0}.execute()...".format(self.__class__)

        super(aep_csm_assembly, self).execute()  # will actually run the workflow

        pass

if __name__=="__main__":

    aepA = aep_csm_assembly()
    
    aepA.execute()
    
    print "5 MW reference turbine"
    print "rated rotor speed: {0}".format(aepA.ratedRotorSpeed)
    print "rated wind speed: {0}".format(aepA.ratedWindSpeed)
    print "maximum efficiency: {0}".format(aepA.maxEfficiency)
    print "gross annual energy production: {0}".format(aepA.gross_aep)
    print "annual energy production: {0}".format(aepA.net_aep)
    print "annual energy production per turbine: {0}".format(aepA.aep_per_turbine)
    print "capacity factor: {0}".format(aepA.capacity_factor)
    print "Power Curve:"
    print aepA.powerCurve