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

"""Test lsst.coadd.utils.Coadd
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
import lsst.afw.image.testUtils as imTestUtils
import lsst.afw.math as afwMath
import lsst.afw.display.ds9 as ds9
import lsst.utils.tests as utilsTests
import lsst.pex.exceptions as pexExcept
import lsst.pex.logging as pexLog
import lsst.coadd.utils as coaddUtils

try:
    display
except NameError:
    display = False
    Verbosity = 0 # increase to see trace

pexLog.Trace_setVerbosity("lsst.coadd.utils", Verbosity)

AfwDataDir = eups.productDir("afwdata")
if AfwDataDir != None:
    ImSimFile = os.path.join(AfwDataDir, "ImSim/calexp/v85408556-fr/R23/S11.fits")
    
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

class CoaddTestCase(unittest.TestCase):
    """A test case for Coadd
    """

    def testAddOne(self):
        """Add a single exposure; make sure coadd = input, appropriately scaled
        """
        inExp = afwImage.ExposureF(ImSimFile)
        bbox = inExp.getBBox(afwImage.PARENT)
        wcs = inExp.getWcs()
        for coaddZeroPoint, badMaskPlanes in (
            (25.0, ()),
            (20.0, ("EDGE", "BAD"))):
            coadd = coaddUtils.Coadd(
                bbox = inExp.getBBox(afwImage.PARENT),
                wcs = inExp.getWcs(),
                badMaskPlanes = badMaskPlanes,
                coaddZeroPoint = coaddZeroPoint,
            )
            coadd.addExposure(inExp)
            coaddExp = coadd.getCoadd()
            
            # the coadd has been scaled, so deal with that
            inFluxMag0 = inExp.getCalib().getFluxMag0()[0]
            inMaskedImage = inExp.getMaskedImage()
            coaddMaskedImage = coaddExp.getMaskedImage()
            coaddFluxMag0 = coaddExp.getCalib().getFluxMag0()[0]
            coaddMaskedImage *= inFluxMag0 / coaddFluxMag0
            
            inMaskArr = inMaskedImage.getMask().getArray()
            badMask = coadd.getBadPixelMask()
            skipMaskArr = inMaskArr & badMask != 0
    
            errStr = imTestUtils.maskedImagesDiffer(inMaskedImage.getArrays(), coaddMaskedImage.getArrays(),
                skipMaskArr=skipMaskArr)
            if errStr:
                self.fail("coadd != input exposure: %s" % (errStr,))

    def assertWcsSame(self, wcs1, wcs2):
        for xPixPos in (0, 1000, 2000):
            for yPixPos in (0, 1000, 2000):
                fromPixPos = afwGeom.Point2D(xPixPos, yPixPos)
                sky1 = wcs1.pixelToSky(fromPixPos)
                sky2 = wcs2.pixelToSky(fromPixPos)
                if not numpy.allclose(sky1.getPosition(), sky2.getPosition()):
                    self.fail("wcs do not match at fromPixPos=%s: sky1=%s != sky2=%s" % \
                        (fromPixPos, sky1, sky2))
                toPixPos1 = wcs1.skyToPixel(sky1)
                toPixPos2 = wcs2.skyToPixel(sky1)
                if not numpy.allclose((xPixPos, yPixPos), toPixPos1):
                    self.fail("wcs do not match at sky1=%s: fromPixPos=%s != toPixPos1=%s" % \
                        (sky1, fromPixPos1, toPixPos1))
                if not numpy.allclose(toPixPos1, toPixPos2):
                    self.fail("wcs do not match at fromPixPos=%s, sky1=%s: toPixPos1=%s != toPixPos2=%s" % \
                        (fromPixPos, sky1, toPixPos1, toPixPos2))
    
    def xtestGetters(self):
        """Test getters for coadd
        """
        inExp = afwImage.ExposureF(ImSimFile)
        bbox = inExp.getBBox(afwImage.PARENT)
        wcs = inExp.getWcs()
        for coaddZeroPoint, badMaskPlanes, bbox in (
            (0.0,  ("EDGE",), afwGeom.Box2I(afwGeom.Point2I(1, 2), afwGeom.Extent2I(100, 102))),
            (12.3, ("EDGE", "BAD"), afwGeom.Box2I(afwGeom.Point2I(0, 0), afwGeom.Extent2I(100, 102))),
            (-5.6, ("EDGE",), afwGeom.Box2I(afwGeom.Point2I(104, 0), afwGeom.Extent2I(5, 10))),
            (25.7, ("EDGE",), afwGeom.Box2I(afwGeom.Point2I(0, 1020), afwGeom.Extent2I(100, 102))),
        ):
            coadd = coaddUtils.Coadd(
                bbox = bbox,
                wcs = wcs,
                badMaskPlanes = badMaskPlanes,
                coaddZeroPoint = coaddZeroPoint,
            )
            badPixelMask = 0
            for maskPlaneName in badMaskPlanes:
                badPixelMask += afwImage.MaskU.getPlaneBitMask(maskPlaneName)
            self.assertEquals(bbox, coadd.getBBox())
            self.assertEquals(badPixelMask, coadd.getBadPixelMask())
            self.assertEquals(coaddZeroPoint, coadd.getCoaddZeroPoint())
            self.assertWcsSame(wcs, coadd.getWcs())


def suite():
    """Return a suite containing all the test cases in this module.
    """
    utilsTests.init()

    suites = []

    if AfwDataDir:
        suites += unittest.makeSuite(CoaddTestCase)
    else:
        warnings.warn("Skipping some tests because afwdata is not setup")
    suites += unittest.makeSuite(utilsTests.MemoryTestCase)

    return unittest.TestSuite(suites)


def run(shouldExit=False):
    """Run the tests"""
    utilsTests.run(suite(), shouldExit)

if __name__ == "__main__":
    run(True)
