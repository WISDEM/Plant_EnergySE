
#!/usr/bin/env python
# encoding: utf-8
"""
test_Turbine_CostsSE.py

Created by Katherine Dykes on 2014-01-07.
Copyright (c) NREL. All rights reserved.
"""

import unittest
import numpy as np
from commonse.utilities import check_gradient_unit_test
from Plant_AEPSE.Basic_AEP.basic_aep import aep_component, WeibullCDF, RayleighCDF


class Test_WeibullCDF(unittest.TestCase):

    def test1(self):

        cdf = WeibullCDF()
        cdf.x = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, \
                 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0, 21.0, 22.0, 23.0, 24.0, 25.0, 26.0]
        cdf.A = 8.35
        cdf.k = 2.15

        check_gradient_unit_test(self, cdf, display=False)

class Test_RayleighCDF(unittest.TestCase):

    def test1(self):

        cdf = RayleighCDF()
        cdf.x = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, \
                 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0, 21.0, 22.0, 23.0, 24.0, 25.0, 26.0]
        cdf.xbar = 8.35

        check_gradient_unit_test(self, cdf, display=False)


class Test_aep_component(unittest.TestCase):

    def test1(self):

        aep = aep_component()
        aep.power_curve = [0.0, 0.0, 0.0, 187.0, 350.0, 658.30, 1087.4, 1658.3, 2391.5, 3307.0, 4415.70, \
                          5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, 5000.0, \
                          5000.0, 5000.0, 0.0]
        aep.CDF_V = [0.010, 0.045, 0.105, 0.186, 0.283, 0.388, 0.496, 0.598, 0.691, 0.771, 0.836, \
                     0.887, 0.925, 0.952, 0.971, 0.983, 0.990, 0.995, 0.997, 0.999, 0.999, 1.000, 1.000, \
                     1.000, 1.000, 1.000]

        # Gradient method on power curve results in issues in the region of transition from region 2 to region 3
        check_gradient_unit_test(self, aep, tol=1.0, display=False)

if __name__ == "__main__":
    unittest.main()
    