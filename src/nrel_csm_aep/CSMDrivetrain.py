""" 
CSMDrivetrain.py
    
Created by Andrew Ning 2013
Copyright (c)  NREL. All rights reserved.

"""
    
from math import *
import numpy as np

from openmdao.main.api import Component, Assembly, set_as_top, VariableTree
from openmdao.main.datatypes.api import Int, Bool, Float, Array, VarTree, Instance, Enum

from commonse.utilities import smooth_abs, smooth_min, hstack

from fusedwind.interface import base, implement_base

@base
class DrivetrainLossesBase(Component):
    """base component for drivetrain efficiency losses"""

    aeroPower = Array(iotype='in', units='W', desc='aerodynamic power')
    aeroTorque = Array(iotype='in', units='N*m', desc='aerodynamic torque')
    aeroThrust = Array(iotype='in', units='N', desc='aerodynamic thrust')
    ratedPower = Float(iotype='in', units='W', desc='rated power')

    power = Array(iotype='out', units='W', desc='total power after drivetrain losses')

@implement_base(DrivetrainLossesBase)
class CSMDrivetrain(Component):
    """drivetrain losses from NREL cost and scaling model"""

    drivetrainType = Enum('geared', ('geared', 'single_stage', 'multi_drive', 'pm_direct_drive'), iotype='in')
    aeroPower = Array(iotype='in', units='kW', desc='aerodynamic power')
    aeroTorque = Array(iotype='in', units='N*m', desc='aerodynamic torque')
    aeroThrust = Array(iotype='in', units='N', desc='aerodynamic thrust')
    ratedPower = Float(iotype='in', units='kW', desc='rated power')

    power = Array(iotype='out', units='kW', desc='total power after drivetrain losses')

    missing_deriv_policy = 'assume_zero'

    def execute(self):

        drivetrainType = self.drivetrainType
        aeroPower = self.aeroPower
        ratedPower = self.ratedPower


        if drivetrainType == 'geared':
            constant = 0.01289
            linear = 0.08510
            quadratic = 0.0

        elif drivetrainType == 'single_stage':
            constant = 0.01331
            linear = 0.03655
            quadratic = 0.06107

        elif drivetrainType == 'multi_drive':
            constant = 0.01547
            linear = 0.04463
            quadratic = 0.05790

        elif drivetrainType == 'pm_direct_drive':
            constant = 0.01007
            linear = 0.02000
            quadratic = 0.06899


        Pbar0 = aeroPower / ratedPower

        # handle negative power case (with absolute value)
        Pbar1, dPbar1_dPbar0 = smooth_abs(Pbar0, dx=0.01)

        # truncate idealized power curve for purposes of efficiency calculation
        Pbar, dPbar_dPbar1, _ = smooth_min(Pbar1, 1.0, pct_offset=0.01)

        # compute efficiency
        eff = 1.0 - (constant/Pbar + linear + quadratic*Pbar)

        self.power = aeroPower * eff


        # gradients
        dPbar_dPa = dPbar_dPbar1*dPbar1_dPbar0/ratedPower
        dPbar_dPr = -dPbar_dPbar1*dPbar1_dPbar0*aeroPower/ratedPower**2

        deff_dPa = dPbar_dPa*(constant/Pbar**2 - quadratic)
        deff_dPr = dPbar_dPr*(constant/Pbar**2 - quadratic)

        dP_dPa = eff + aeroPower*deff_dPa
        dP_dPr = aeroPower*deff_dPr

        self.J = hstack([np.diag(dP_dPa), dP_dPr])


    def list_deriv_vars(self):

        inputs = ('aeroPower', 'ratedPower')
        outputs = ('power',)

        return inputs, outputs

    def provideJ(self):

        return self.J