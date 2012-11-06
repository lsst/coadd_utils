#!/usr/bin/env python

# 
# LSST Data Management System
# Copyright 2008, 2009, 2010 LSST Corporation.
# 
# This product includes software developed by the
# LSST Project (http://www.lsst.org/).
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the LSST License Statement and 
# the GNU General Public License along with this program.  If not, 
# see <http://www.lsstcorp.org/LegalNotices/>.
#

"""Test lsst.coadd.utils.ScaleZeroPointTask
"""
import os
import pdb # we may want to say pdb.set_trace()
import unittest
import warnings
import sys

import numpy

import eups
import lsst.afw.geom as afwGeom
import lsst.afw.image as afwImage
import lsst.afw.image.utils as imageUtils
import lsst.afw.image.testUtils as imTestUtils
import lsst.afw.math as afwMath
import lsst.utils.tests as utilsTests
import lsst.pex.exceptions as pexExcept
import lsst.pex.logging as pexLog
import lsst.coadd.utils as coaddUtils
import lsst.pex.policy as pexPolicy
from lsst.coadd.utils import ScaleZeroPointTask
    
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

class ScaleZeroPointTaskTestCase(unittest.TestCase):
    """A test case for ScaleZeroPointTask
    """
    def testBasics(self):
        for outZeroPoint in (23, 24):
            config = ScaleZeroPointTask.ConfigClass()
            config.zeroPoint = outZeroPoint
            zpScaler = ScaleZeroPointTask(config=config)
            outCalib = zpScaler.getCalib()

            self.assertAlmostEqual(outCalib.getMagnitude(1.0), outZeroPoint)
            
            for inZeroPoint in (24, 25.5):
                inCalib = self.makeCalib(inZeroPoint)
                scale = zpScaler.computeScale(inCalib).scale
                
                predScale = 1.0 / inCalib.getFlux(outZeroPoint)
                self.assertAlmostEqual(predScale, scale)

                inFluxAtOutZeroPoint = inCalib.getFlux(outZeroPoint)
                outFluxAtOutZeroPoint = outCalib.getFlux(outZeroPoint)
                self.assertAlmostEqual(outFluxAtOutZeroPoint / scale, inFluxAtOutZeroPoint)

                inFluxMag0 = inCalib.getFluxMag0()
                outFluxMag0 = outCalib.getFluxMag0()
                self.assertAlmostEqual(numpy.round(outFluxMag0[0] / scale, 4), numpy.round(inFluxMag0[0], 4))
                
    def makeCalib(self, zeroPoint):
        calib = afwImage.Calib()
        fluxMag0 = 10**(0.4 * zeroPoint)
        calib.setFluxMag0(fluxMag0, 1.0)
        return calib


def suite():
    """Return a suite containing all the test cases in this module.
    """
    utilsTests.init()

    suites = [
        unittest.makeSuite(ScaleZeroPointTaskTestCase),
        unittest.makeSuite(utilsTests.MemoryTestCase),
    ]

    return unittest.TestSuite(suites)


def run(shouldExit=False):
    """Run the tests"""
    utilsTests.run(suite(), shouldExit)

if __name__ == "__main__":
    run(True)
