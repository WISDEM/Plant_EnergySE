"""
aep_csm_component.py

Created by NWTC Systems Engineering Sub-Task on 2012-08-01.
Copyright (c) NREL. All rights reserved.
"""

import numpy as np

from openmdao.main.api import Component, Assembly, set_as_top, VariableTree
from openmdao.main.datatypes.api import Int, Bool, Float, Array, VarTree

from commonse.utilities import hstack, vstack

from fusedwind.plant_flow.fused_plant_asym import GenericAEPModel

class aep_weibull_assembly(GenericAEPModel):

    def __init__(self):
        
        super(aep_weibull_assembly, self).__init__()

    def configure(self):
      
        super(aep_weibull_assembly, self).configure()
        
        self.add('aep', aep_component())
        self.add('cdf', WeibullCDF())
        
        self.driver.workflow.add(['aep', 'cdf'])
        
        #inputs
        self.create_passthrough('aep.power_curve') #TODO - array issue openmdao
        self.create_passthrough('aep.array_losses')
        self.create_passthrough('aep.other_losses')
        self.create_passthrough('aep.availability')
        self.create_passthrough('aep.turbine_number')
        self.create_passthrough('cdf.A')
        self.create_passthrough('cdf.k')
        self.create_passthrough('cdf.x')
        
        # connections
        self.connect('cdf.F', 'aep.CDF_V')
        
        # outputs
        self.connect('aep.gross_aep', 'gross_aep')
        self.connect('aep.net_aep', 'net_aep')

class CDFBase(Component):
    """cumulative distribution function"""

    x = Array(iotype='in')

    F = Array(iotype='out')


class WeibullCDF(CDFBase):
    """Weibull cumulative distribution function"""

    A = Float(iotype='in', desc='scale factor')
    k = Float(iotype='in', desc='shape or form factor')

    def __init__(self):
        
        super(WeibullCDF,self).__init__()

        #controls what happens if derivatives are missing
        self.missing_deriv_policy = 'assume_zero'

    def execute(self):

        self.F = 1.0 - np.exp(-(self.x/self.A)**self.k)
        
        self.d_F_d_x = np.diag(- np.exp(-(self.x/self.A)**self.k) * (1./self.A) * (-self.k * ((self.x/self.A)**(self.k-1.0))))
        self.d_F_d_A = - np.exp(-(self.x/self.A)**self.k) * (1./self.x) * (self.k * ((self.A/self.x)**(-self.k-1.0)))
        self.d_F_d_k = - np.exp(-(self.x/self.A)**self.k) * -(self.x/self.A)**self.k * np.log(self.x/self.A)
    
    def list_deriv_vars(self):

        inputs = ('x', 'A', 'k')
        outputs = ('F')
        
        return inputs, outputs

    
    def provideJ(self):
        
        self.J = hstack((self.d_F_d_x, self.d_F_d_A, self.d_F_d_k))        
        
        return self.J

class RayleighCDF(CDFBase):
    """Rayleigh cumulative distribution function"""

    xbar = Float(iotype='in', desc='mean value of distribution')
    
    def __init__(self):
      
        super(RayleighCDF,self).__init__()
        
        #controls what happens if derivatives are missing
        self.missing_deriv_policy = 'assume_zero'

    def execute(self):

        self.F = 1.0 - np.exp(-np.pi/4.0*(self.x/self.xbar)**2)
        
        self.d_F_d_x = np.diag(- np.exp(-np.pi/4.0*(self.x/self.xbar)**2) * ((-np.pi/2.0)*(self.x/self.xbar)) * (1.0 / self.xbar))
        self.d_F_d_xbar = - np.exp(-np.pi/4.0*(self.x/self.xbar)**2) * ((np.pi/2.0)*(self.xbar/self.x)**(-3)) * (1.0 / self.x)

    def list_deriv_vars(self):
        
        inputs = ('x', 'xbar')
        outputs = ('F')

        return inputs, outputs
    
    def provideJ(self):
        
        self.J = hstack((self.d_F_d_x, self.d_F_d_xbar))
        
        return self.J

class aep_component(Component):
    """annual energy production"""
 
    # variables
    CDF_V = Array(iotype='in')
    power_curve = Array(iotype='in', units='W', desc='power curve (power)')
    
    # parameters
    array_losses = Float(0.059, iotype='in', desc = 'energy losses due to turbine interactions - across entire plant') 
    other_losses = Float(0.0, iotype='in', desc = 'energy losses due to blade soiling, electrical, etc')
    availability = Float(0.94, iotype='in', desc = 'average annual availbility of wind turbines at plant')
    turbine_number = Int(100, iotype='in', desc = 'total number of wind turbines at the plant')

    # ------------- Outputs -------------- 
    gross_aep = Float(iotype='out', desc='Gross Annual Energy Production before availability and loss impacts', unit='kWh')
    net_aep = Float(iotype='out', desc='Net Annual Energy Production after availability and loss impacts', unit='kWh') 

    def __init__(self):
        
        super(aep_component,self).__init__()

        #controls what happens if derivatives are missing
        self.missing_deriv_policy = 'assume_zero'
 
    def execute(self):
 
        self.gross_aep = self.turbine_number * np.trapz(self.power_curve, self.CDF_V)*365.0*24.0 # in kWh
        self.net_aep = self.availability * (1-self.array_losses) * (1-self.other_losses) * self.gross_aep
 
    def list_deriv_vars(self):

        inputs = ('CDF_V', 'power_curve')
        outputs = ('gross_aep', 'net_aep')
        
        return inputs, outputs
    
    def provideJ(self):

        P = self.power_curve
        CDF = self.CDF_V
        factor = self.availability * (1-self.other_losses)*(1-self.array_losses)*365.0*24.0 * self.turbine_number
 
        n = len(P)
        dAEP_dP = np.gradient(CDF)
        dAEP_dP[0] /= 2
        dAEP_dP[-1] /= 2
        d_gross_d_p = dAEP_dP * 365.0 * 24.0 * self.turbine_number
        d_net_d_p = dAEP_dP * factor
 
        dAEP_dCDF = -np.gradient(P)
        dAEP_dCDF[0] = -0.5*(P[0] + P[1])
        dAEP_dCDF[-1] = 0.5*(P[-1] + P[-2])
        d_gross_d_cdf = dAEP_dCDF * 365.0 * 24.0 * self.turbine_number
        d_net_d_cdf = dAEP_dCDF * factor
        
        #loss_factor = self.availability * (1-self.array_losses) * (1-self.other_losses)
 
        #dAEP_dlossFactor = np.array([self.net_aep/loss_factor])
 
        self.J = np.zeros((2, 2*n))
        self.J[0, 0:n] = d_gross_d_cdf
        self.J[0, n:2*n] = d_gross_d_p
        self.J[1, 0:n] = d_net_d_cdf
        self.J[1, n:2*n] = d_net_d_p        
        #self.J[0, 2*n] = dAEP_dlossFactor
 
        return self.J

def example():

    aeptest = aep_weibull_assembly()
    
    #print aeptest.aep.machine_rating
    
    aeptest.x = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, \
                           11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0, 21.0, 22.0, 23.0, 24.0, 25.0, 26.0]
    aeptest.power_curve = [0.0, 0.0, 0.0, 0.0, 187.0, 350.0, 658.30, 1087.4, 1658.3, 2391.5, 3307.0, 4415.70, \
                          5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, \
                          5000.0, 5000.0, 0.0]
    aeptest.A = 8.35
    aeptest.k = 2.15

    aeptest.execute()

    print "AEP gross output: {0}".format(aeptest.gross_aep)
    print "AEP output: {0}".format(aeptest.net_aep)

    print aeptest.cdf.F

if __name__=="__main__":

    example()
