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

"""Test lsst.coadd.utils.ZeropointScaler
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
from lsst.coadd.utils import ZeropointScaler
    
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

class ZeropointScalerTestCase(unittest.TestCase):
    """A test case for ZeropointScaler
    """
    def testBasics(self):
        for outZeropoint in (23, 24):
            zpScaler = ZeropointScaler(zeropoint = outZeropoint)
            
            for inZeropoint in (24, 25.5):
                inExposure = self.makeExposure(inZeropoint)
                inMaskedImage = inExposure.getMaskedImage()
                
                # use a copy to scale, since the operation is "in place"
                outExposure = self.makeExposure(inZeropoint)
                outMaskedImage = outExposure.getMaskedImage()
                scaleFac = zpScaler.scaleExposure(outExposure)
                
                predScaleFac = 1.0 / inExposure.getCalib().getFlux(outZeropoint)
                self.assertAlmostEqual(predScaleFac, scaleFac)

                inFluxAtOutZeropoint = inExposure.getCalib().getFlux(outZeropoint)
                outFluxAtOutZeropoint = outExposure.getCalib().getFlux(outZeropoint)
                self.assertAlmostEqual(outFluxAtOutZeropoint / scaleFac, inFluxAtOutZeropoint)
                inFluxMag0 = inExposure.getCalib().getFluxMag0()
                outFluxMag0 = outExposure.getCalib().getFluxMag0()
                self.assertAlmostEqual(numpy.round(outFluxMag0[0] / scaleFac, 4), numpy.round(inFluxMag0[0], 4))
                self.assertAlmostEqual(outFluxMag0[1] / scaleFac, inFluxMag0[1])
                
                inImageArr = inMaskedImage.getImage().getArray()
                outImageArr = outMaskedImage.getImage().getArray()
                self.assertTrue(numpy.allclose(outImageArr / scaleFac, inImageArr))
    
    def makeExposure(self, zeropoint):
        maskedImage = afwImage.MaskedImageF(afwGeom.Extent2I(10, 10))
        exposure = afwImage.ExposureF(maskedImage)
        calib = afwImage.Calib()
        fluxMag0 = 10**(0.4 * zeropoint)
        calib.setFluxMag0(fluxMag0, 1.0)
        exposure.setCalib(calib)
        return exposure
        


def suite():
    """Return a suite containing all the test cases in this module.
    """
    utilsTests.init()

    suites = [
        unittest.makeSuite(ZeropointScalerTestCase),
        unittest.makeSuite(utilsTests.MemoryTestCase),
    ]

    return unittest.TestSuite(suites)


def run(shouldExit=False):
    """Run the tests"""
    utilsTests.run(suite(), shouldExit)

if __name__ == "__main__":
    run(True)
