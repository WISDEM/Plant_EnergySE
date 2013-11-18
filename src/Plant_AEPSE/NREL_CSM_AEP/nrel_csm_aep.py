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
    machine_rating = Float(5000.0, units = 'kW', iotype='in', desc= 'rated machine power in kW')
    hub_height = Float(90.0, units = 'm', iotype='in', desc='hub height of wind turbine above ground / sea level')

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
        self.add('aep',aep_csm_component())

        self.driver.workflow.add(['drive', 'aero', 'aep'])


        # connect inputs to component inputs
        self.connect('machine_rating', ['aero.machine_rating', 'aep.machine_rating'])
        self.connect('hub_height', ['aero.hub_height', 'aep.hub_height'])

        # connect i/o between components
        self.connect('drive.drivetrain','aero.drivetrain')
        self.connect('aero.power_curve','aep.power_curve')
        
        # create passthroughs for input variables
        # turbine
        self.create_passthrough('aero.max_tip_speed')
        self.create_passthrough('aero.rotor_diameter')
        self.create_passthrough('aero.max_power_coefficient')
        self.create_passthrough('aero.opt_tsr')
        self.create_passthrough('aero.cut_in_wind_speed')
        self.create_passthrough('aero.cut_out_wind_speed')
        self.create_passthrough('drive.drivetrain_design')
        # plant
        self.create_passthrough('aep.shear_exponent')
        self.create_passthrough('aep.weibull_k')
        self.create_passthrough('aep.soiling_losses')
        self.create_passthrough('aep.array_losses')
        self.create_passthrough('aep.availability')
        self.create_passthrough('aep.turbine_number')
        self.create_passthrough('aero.altitude')
        self.create_passthrough('aero.air_density')

        # create passthroughs for key output variables of interest
        self.create_passthrough('aero.rated_rotor_speed')
        self.create_passthrough('aero.rated_wind_speed')
        self.create_passthrough('aero.max_efficiency')
        self.create_passthrough('aero.power_curve')

        # outputs
        self.connect('aep.gross_aep', 'gross_aep')
        self.connect('aep.net_aep', 'net_aep')
        self.connect('aep.capacity_factor', 'capacity_factor')
        self.create_passthrough('aep.aep_per_turbine')
    
    def execute(self):

        print "In {0}.execute()...".format(self.__class__)

        super(aep_csm_assembly, self).execute()  # will actually run the workflow

def example():

    aepA = aep_csm_assembly()
    #aepA.machine_rating = 5000.0 # Setting an input to get components to execute
    
    aepA.execute()
    
    print "5 MW reference turbine"
    print "rated rotor speed: {0}".format(aepA.rated_rotor_speed)
    print "rated wind speed: {0}".format(aepA.rated_wind_speed)
    print "maximum efficiency: {0}".format(aepA.max_efficiency)
    print "gross annual energy production: {0}".format(aepA.gross_aep)
    print "annual energy production: {0}".format(aepA.net_aep)
    print "annual energy production per turbine: {0}".format(aepA.aep_per_turbine)
    print "capacity factor: {0}".format(aepA.capacity_factor)
    print "Power Curve:"
    print aepA.power_curve

if __name__=="__main__":

    example()