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
"""Basic test of Warp (the warping algorithm is thoroughly tested in lsst.afw.math)
"""
import os

import unittest

import numpy

import eups
import lsst.afw.image as afwImage
import lsst.afw.image.testUtils as imageTestUtils
import lsst.utils.tests as utilsTests
import lsst.pex.logging as logging
import lsst.coadd.utils as coaddUtils

VERBOSITY = 0                       # increase to see trace

logging.Debug("lsst.afw.math", VERBOSITY)

dataDir = eups.productDir("afwdata")
if not dataDir:
    raise RuntimeError("Must set up afwdata to run these tests")

originalExposureName = "med"
originalExposurePath = os.path.join(dataDir, originalExposureName)
subExposureName = "medsub"
subExposurePath = os.path.join(dataDir, originalExposureName)
originalFullExposureName = os.path.join("CFHT", "D4", "cal-53535-i-797722_1")
originalFullExposurePath = os.path.join(dataDir, originalFullExposureName)

class WarpExposureTestCase(unittest.TestCase):
    """Test case for Warp
    """
    def testMatchSwarpLanczos2Exposure(self):
        """Test that warpExposure matches swarp using a lanczos2 warping kernel.
        """
        self.compareToSwarp("lanczos2")

    def testMatchSwarpLanczos2SubExposure(self):
        """Test that warpExposure matches swarp using a lanczos2 warping kernel with a subexposure
        """
        for useDeepCopy in (False, True):
            self.compareToSwarp("lanczos2", useSubregion=True, useDeepCopy=useDeepCopy)

    def compareToSwarp(self, kernelName, 
                       useSubregion=False, useDeepCopy=False,
                       interpLength=10, cacheSize=100000,
                       rtol=4e-05, atol=1e-2):
        """Compare warpExposure to swarp for given warping kernel.
        
        Note that swarp only warps the image plane, so only test that plane.
        
        Inputs:
        - kernelName: name of kernel in the form used by afwImage.makeKernel
        - useSubregion: if True then the original source exposure (from which the usual
            test exposure was extracted) is read and the correct subregion extracted
        - useDeepCopy: if True then the copy of the subimage is a deep copy,
            else it is a shallow copy; ignored if useSubregion is False
        - interpLength: interpLength argument for lsst.afw.math.warpExposure
        - cacheSize: cacheSize argument for lsst.afw.math.SeparableKernel.computeCache;
            0 disables the cache
            10000 gives some speed improvement but less accurate results (atol must be increased)
            100000 gives better accuracy but no speed improvement in this test
        - rtol: relative tolerance as used by numpy.allclose
        - atol: absolute tolerance as used by numpy.allclose
        """
        warper = coaddUtils.Warp(kernelName)

        if useSubregion:
            originalFullExposure = afwImage.ExposureF(originalExposurePath)
            # "medsub" is a subregion of med starting at 0-indexed pixel (40, 150) of size 145 x 200
            bbox = afwImage.BBox(afwImage.PointI(40, 150), 145, 200)
            originalExposure = afwImage.ExposureF(originalFullExposure, bbox, useDeepCopy)
            swarpedImageName = "medsubswarp1%s.fits" % (kernelName,)
        else:
            originalExposure = afwImage.ExposureF(originalExposurePath)
            swarpedImageName = "medswarp1%s.fits" % (kernelName,)

        swarpedImagePath = os.path.join(dataDir, swarpedImageName)
        swarpedDecoratedImage = afwImage.DecoratedImageF(swarpedImagePath)
        swarpedImage = swarpedDecoratedImage.getImage()
        swarpedMetadata = swarpedDecoratedImage.getMetadata()
        warpedWcs = afwImage.makeWcs(swarpedMetadata)
        destWidth = swarpedImage.getWidth()
        destHeight = swarpedImage.getHeight()
        
        # path for saved afw-warped image
        afwWarpedImagePath = "afwWarpedExposure1%s" % (kernelName,)

        afwWarpedExposure = warper.warpExposure(
            dimensions = swarpedImage.getDimensions(),
            xy0 = swarpedImage.getXY0(),
            wcs = warpedWcs,
            exposure = originalExposure,
        )
        afwWarpedMaskedImage = afwWarpedExposure.getMaskedImage()

        afwWarpedMask = afwWarpedMaskedImage.getMask()
        edgeBitMask = afwWarpedMask.getPlaneBitMask("EDGE")
        if edgeBitMask == 0:
            self.fail("warped mask has no EDGE bit")
        afwWarpedMaskedImageArrSet = imageTestUtils.arraysFromMaskedImage(afwWarpedMaskedImage)
        afwWarpedMaskArr = afwWarpedMaskedImageArrSet[1]

        swarpedMaskedImage = afwImage.MaskedImageF(swarpedImage)
        swarpedMaskedImageArrSet = imageTestUtils.arraysFromMaskedImage(swarpedMaskedImage)

        errStr = imageTestUtils.maskedImagesDiffer(afwWarpedMaskedImageArrSet, swarpedMaskedImageArrSet,
            doImage=True, doMask=False, doVariance=False, skipMaskArr=afwWarpedMaskArr,
            rtol=rtol, atol=atol)
        if errStr:
            self.fail("afw and swarp %s-warped %s (ignoring bad pixels)" % (kernelName, errStr))
        
        
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

def suite():
    """
    Returns a suite containing all the test cases in this module.
    """
    utilsTests.init()

    suites = []
    suites += unittest.makeSuite(WarpExposureTestCase)
    suites += unittest.makeSuite(utilsTests.MemoryTestCase)

    return unittest.TestSuite(suites)

def run(doExit=False):
    """Run the tests"""
    utilsTests.run(suite(), doExit)

if __name__ == "__main__":
    run(True)
