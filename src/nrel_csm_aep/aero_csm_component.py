"""
aero_csm_component.py

Created by NWTC Systems Engineering Sub-Task on 2012-08-01.
Copyright (c) NREL. All rights reserved.
"""

import numpy as np

from openmdao.main.api import Component, Assembly, set_as_top, VariableTree
from openmdao.main.datatypes.api import Int, Bool, Float, Array, VarTree, Instance

class aero_csm_component(Component): 
    
    # Variables
    machine_rating = Float(5000.0, units = 'kW', iotype='in', desc= 'rated machine power in kW')
    max_tip_speed = Float(80.0, units = 'm/s', iotype='in', desc= 'maximum allowable tip speed for the rotor')
    rotor_diameter = Float(126.0, units = 'm', iotype='in', desc= 'rotor diameter of the machine') 
    max_power_coefficient = Float(0.488, iotype='in', desc= 'maximum power coefficient of rotor for operation in region 2')
    opt_tsr = Float(7.525, iotype='in', desc= 'optimum tip speed ratio for operation in region 2')
    cut_in_wind_speed = Float(3.0, units = 'm/s', iotype='in', desc= 'cut in wind speed for the wind turbine')
    cut_out_wind_speed = Float(25.0, units = 'm/s', iotype='in', desc= 'cut out wind speed for the wind turbine')
    hub_height = Float(90.0, units = 'm', iotype='in', desc= 'hub height of wind turbine above ground / sea level')
    altitude = Float(0.0, units = 'm', iotype='in', desc= 'altitude of wind plant')
    air_density = Float(0.0, units = 'kg / (m * m * m)', iotype='in', desc= 'air density at wind plant site')  # default air density value is 0.0 - forces aero csm to calculate air density in model
    max_efficiency = Float(0.902, iotype='in', desc = 'maximum efficiency of rotor and drivetrain - at rated power') 

    # Outputs
    rated_wind_speed = Float(11.506, units = 'm / s', iotype='out', desc='wind speed for rated power')
    rated_rotor_speed = Float(12.126, units = 'rpm', iotype='out', desc = 'rotor speed at rated power')
    power_curve = Array(iotype='out', units='kW', desc='total power before drivetrain losses')
    wind_curve = Array(iotype='out', units='m/s', desc='wind curve associated with power curve')

    def __init__(self):
        """
        OpenMDAO component to wrap Aerodynamics module of the NREL _cost and Scaling Model (csmAero.py)
        
        """

        super(aero_csm_component,self).__init__()

    def execute(self):
        """
        Executes Aerodynamics Sub-module of the NREL _cost and Scaling Model to create a power curve based on a limited set of inputs.
        It then modifies the ideal power curve to take into account drivetrain efficiency losses through an interface to a drivetrain efficiency model.
        """
        print "In {0}.execute() ...".format(self.__class__)
         
        # initialize input parameters
        self.hubHt      = self.hub_height
        self.ratedPower = self.machine_rating
        self.maxTipSpd  = self.max_tip_speed
        self.rotorDiam  = self.rotor_diameter
        self.maxCp      = self.max_power_coefficient
        self.maxTipSpdRatio = self.opt_tsr
        self.cutInWS    =  self.cut_in_wind_speed
        self.cutOutWS   = self.cut_out_wind_speed
        self.altitude   = self.altitude

        if self.air_density == 0.0:      
            # Compute air density 
            ssl_pa     = 101300  # std sea-level pressure in Pa
            gas_const  = 287.15  # gas constant for air in J/kg/K
            gravity    = 9.80665 # standard gravity in m/sec/sec
            lapse_rate = 0.0065  # temp lapse rate in K/m
            ssl_temp   = 288.15  # std sea-level temp in K
        
            self.airDensity = (ssl_pa * (1-((lapse_rate*(self.altitude + self.hubHt))/ssl_temp))**(gravity/(lapse_rate*gas_const))) / \
              (gas_const*(ssl_temp-lapse_rate*(self.altitude + self.hubHt)))
        else:
            self.airDensity = airDensity

        # determine power curve inputs
        self.reg2pt5slope  = 0.05
        
        #self.max_efficiency = self.drivetrain.getMaxEfficiency()
        self.ratedHubPower = self.ratedPower / self.max_efficiency  # RatedHubPower

        self.omegaM = self.maxTipSpd/(self.rotorDiam/2.)  # Omega M - rated rotor speed
        omega0 = self.omegaM/(1+self.reg2pt5slope)       # Omega 0 - rotor speed at which region 2 hits zero torque
        Tm = self.ratedHubPower*1000/self.omegaM         # Tm - rated torque

        # compute rated rotor speed
        self.ratedRPM = (30/np.pi) * self.omegaM
        
        # compute variable-speed torque constant k
        kTorque = (self.airDensity*np.pi*self.rotorDiam**5*self.maxCp)/(64*self.maxTipSpdRatio**3) # k
        
        b = -Tm/(self.omegaM-omega0)                       # b - quadratic formula values to determine omegaT
        c = (Tm*omega0)/(self.omegaM-omega0)               # c
        
        # omegaT is rotor speed at which regions 2 and 2.5 intersect
        # add check for feasibility of omegaT calculation 09/20/2012
        omegaTflag = True
        if (b**2-4*kTorque*c) > 0:
           omegaT = -(b/(2*kTorque))-(np.sqrt(b**2-4*kTorque*c)/(2*kTorque))  # Omega T
           #print [kTorque, b, c, omegaT]
        
           windOmegaT = (omegaT*self.rotorDiam)/(2*self.maxTipSpdRatio) # Wind  at omegaT (M25)
           pwrOmegaT  = kTorque*omegaT**3/1000                                # Power at ometaT (M26)
        
           # compute rated wind speed
           d = self.airDensity*np.pi*self.rotorDiam**2.*0.25*self.maxCp
           self.ratedWindSpeed = \
              0.33*( (2.*self.ratedHubPower*1000.      / (    d))**(1./3.) ) + \
              0.67*( (((self.ratedHubPower-pwrOmegaT)*1000.) / (1.5*d*windOmegaT**2.))  + windOmegaT )
        else:
           omegaTflag = False
           windOmegaT = self.ratedRPM
           pwrOmegaT = self.ratedPower


        # set up for idealized power curve
        n = 161 # number of wind speed bins
        itp = [None] * n
        ws_inc = 0.25  # size of wind speed bins for integrating power curve
        Wind = []
        Wval = 0.0
        Wind.append(Wval)
        for i in xrange(1,n):
           Wval += ws_inc
           Wind.append(Wval)

        # determine idealized power curve 
        self.idealPowerCurve (Wind, itp, kTorque, windOmegaT, pwrOmegaT, n , omegaTflag)

        # add a fix for rated wind speed calculation inaccuracies kld 9/21/2012
        ratedWSflag = False
        # determine power curve after losses
        mtp = [None] * n
        for i in xrange(0,n):
           mtp[i] = itp[i] #* self.drivetrain.getDrivetrainEfficiency(itp[i],self.ratedHubPower)
           #print [Wind[i],itp[i],self.drivetrain.getDrivetrainEfficiency(itp[i],self.ratedHubPower),mtp[i]] # for testing
           if (mtp[i] > self.ratedPower):
              if not ratedWSflag:
                ratedWSflag = True
              mtp[i] = self.ratedPower

        self.rated_wind_speed = self.ratedWindSpeed
        self.rated_rotor_speed = self.ratedRPM
        self.power_curve = mtp
        self.wind_curve = Wind

    def idealPowerCurve( self, Wind, ITP, kTorque, windOmegaT, pwrOmegaT, n , omegaTflag):
        """
        Determine the ITP (idealized turbine power) array
        """
       
        idealPwr = 0.0

        for i in xrange(0,n):
            if (Wind[i] >= self.cutOutWS ) or (Wind[i] <= self.cutInWS):
                idealPwr = 0.0  # cut out
            else:
                if omegaTflag:
                    if ( Wind[i] > windOmegaT ):
                       idealPwr = (self.ratedHubPower-pwrOmegaT)/(self.ratedWindSpeed-windOmegaT) * (Wind[i]-windOmegaT) + pwrOmegaT # region 2.5
                    else:
                       idealPwr = kTorque * (Wind[i]*self.maxTipSpdRatio/(self.rotorDiam/2.0))**3 / 1000.0 # region 2             
                else:
                    idealPwr = kTorque * (Wind[i]*self.maxTipSpdRatio/(self.rotorDiam/2.0))**3 / 1000.0 # region 2

            ITP[i] = idealPwr
            #print [Wind[i],ITP[i]]
        
        return

def example():
  
    aerotest = aero_csm_component()
    
    # Test for NREL 5 MW turbine
    aerotest.run()
    
    print "NREL 5MW Reference Turbine"
    print "Rated rotor speed: {0}".format(aerotest.rated_rotor_speed)
    print "Rated wind speed: {0}".format(aerotest.rated_wind_speed)
    print "Maximum efficiency: {0}".format(aerotest.max_efficiency)
    print "Power Curve: "
    print aerotest.power_curve   

if __name__=="__main__":


    example()