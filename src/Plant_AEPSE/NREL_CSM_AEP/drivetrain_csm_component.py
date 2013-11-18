"""
drive_csm_component.py

Created by NWTC Systems Engineering Sub-Task on 2012-08-01.
Copyright (c) NREL. All rights reserved.
"""

import sys
import numpy as np

from openmdao.main.api import Component, Assembly, set_as_top, VariableTree
from openmdao.main.datatypes.api import Int, Bool, Float, Array, VarTree, Slot

from NREL_CSM.csmDriveEfficiency import DrivetrainEfficiencyModel, csmDriveEfficiency

class drive_csm_component(Component):

    # ---- Design Variables ----------
    # Turbine configuration
    drivetrain_design = Int(1, iotype='in', desc= 'drivetrain design type 1 = 3-stage geared, 2 = single-stage geared, 3 = multi-generator, 4 = direct drive')

    # ------------- Outputs --------------  
    # Drivetrain Efficiency Model
    drivetrain = Slot(DrivetrainEfficiencyModel, iotype = 'out', desc= "drivetrain efficiency model")    

    def execute(self):
        """
        OpenMDAO component to wrap drivetrain model fo the NREL _cost and Scaling Model (csmDriveEffiency.py)

        Parameters
        ----------
        drivetrain_design : int
          drivetrain design type 1 = 3-stage geared, 2 = single-stage geared, 3 = multi-generator, 4 = direct drive
    
        Returns
        -------
        drivetrain : DrivetrainEfficiencyModel
          drivetrain efficiency model (must conform to interface)    


        """

        print "In {0}.execute()...".format(self.__class__)
         
        self.drivetrain = csmDriveEfficiency(self.drivetrain_design)

def example():
  
    drive = drive_csm_component
    
    drivetrain = csmDriveEfficiency(1)
    drive.drivetrain = drivetrain
    
    drive.execute
    
    print "Max Efficiency: {0}".format(drive.drivetrain.getMaxEfficiency())

if __name__=="__main__":

    example()