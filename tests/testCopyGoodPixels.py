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

"""Test lsst.coadd.utils.copyGoodPixels
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

dataDir = eups.productDir("afwdata")
if dataDir != None:
    medMIPath = os.path.join(dataDir, "data", "med")
    
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

def referenceCopyGoodPixelsImage(destImage, srcImage):
    """Reference implementation of lsst.coadd.utils.copyGoodPixels for Images
    
    Unlike lsst.coadd.utils.copyGoodPixels this one does not update the input destImage,
    but instead returns the new version
    
    Inputs:
    - destImage: source image before adding srcImage (a MaskedImage)
    - srcImage: masked image to add to destImage (a MaskedImage)
    - badPixelMask: mask of bad pixels to ignore (an int)

    Returns:
    - destImage: new destImage
    - numGoodPix: number of good pixels
    """
    destImage = destImage.Factory(destImage, True) # make deep copy

    overlapBBox = destImage.getBBox(afwImage.PARENT)
    overlapBBox.clip(srcImage.getBBox(afwImage.PARENT))
    
    if overlapBBox.isEmpty():
        return (destImageArray, 0)
    
    destImageView = destImage.Factory(destImage, overlapBBox)
    destImageArray = destImageView.getArray()

    srcImageView = srcImage.Factory(srcImage, overlapBBox)
    srcImageArray = srcImageView.getArray()
    
    isBadArray = nump.isnan(srcImageView)

    destImageArray[:] = numpy.where(isBadArray, destImageArray, srcImageArray)
    numGoodPix = numpy.sum(isBadArray)
    return destImage, numGoodPix

def referenceCopyGoodPixelsMaskedImage(destImage, srcImage, badPixelMask):
    """Reference implementation of lsst.coadd.utils.copyGoodPixels for MaskedImages
    
    Unlike lsst.coadd.utils.copyGoodPixels this one does not update the input destImage,
    but instead returns an updated copy
    
    @param[in] destImage: source image before adding srcImage (a MaskedImage)
    @param[in] srcImage: masked image to add to destImage (a MaskedImage)
    @param[in] badPixelMask: mask of bad pixels to ignore (an int)

    Returns:
    - destImage: new destImage
    - numGoodPix: number of good pixels
    """
    destImage = destImage.Factory(destImage, True) # make deep copy

    overlapBBox = destImage.getBBox(afwImage.PARENT)
    overlapBBox.clip(srcImage.getBBox(afwImage.PARENT))
    
    if overlapBBox.isEmpty():
        return (destImageArray, 0)
    
    destImageView = destImage.Factory(destImage, overlapBBox)
    destImageArrayList = destImageView.getArrays()

    srcImageView = srcImage.Factory(srcImage, overlapBBox)
    srcImageArrayList = srcImageView.getArrays()
    
    isBadArray = (srcImageArrayList[1] & badPixelMask) != 0
    
    for ind in range(3):
        destImageView = destImageArrayList[ind]
        srcImageView = srcImageArrayList[ind]
        destImageView = numpy.where(isBadArray, destImageView, srcImageView)
    numGoodPix = numpy.sum(isBadArray)
    return destImage, numGoodPix


class CopyGoodPixelsTestCase(unittest.TestCase):
    """A test case for copyGoodPixels
    """

    def _testCopyGoodPixelsImpl(self, testMaskedImage):
        """Basic test
        
        @param[in] testMaskedImage: if True then test with a MaskedImage, else an Image
        """
        trueImageValue = 10.0
        imBBox = afwGeom.Box2I(afwGeom.Point2I(0, 0), afwGeom.Extent2I(10, 20))
        if testMaskedImage:
            destImage = afwImage.MaskedImageF(imBBox)

            badBits = 0x1
            badPixel = (float("NaN"), badBits, 0)
            zero = (0.0, 0x0, 0)
            goodPixel = (trueImageValue, 0x0, 0)
        else:
            destImage = afwImage.ImageF(imBBox)

            badPixel = float("NaN")
            zero = 0.0
            goodPixel = trueImageValue

        for i in range(0, 20, 3):
            image = destImage.Factory(destImage.getDimensions())
            image.set(badPixel)

            subBBox = afwGeom.Box2I(afwGeom.Point2I(0, i),
                image.getDimensions() - afwGeom.Extent2I(0, i))
            subImage = image.Factory(image, subBBox, afwImage.LOCAL)
            subImage.set(goodPixel)
            del subImage

            if testMaskedImage:
                coaddUtils.copyGoodPixels(destImage, image, badBits)
            else:
                coaddUtils.copyGoodPixels(destImage, image)

            self.assertEqual(image.get(image.getWidth() - 1, image.getHeight() - 1), goodPixel)

        if display:
            ds9.mtv(image, title="image", frame=1)
            ds9.mtv(destImage, title="destImage", frame=2)

        stats = afwMath.makeStatistics(destImage, afwMath.MEAN | afwMath.STDEV)

        return [trueImageValue, stats.getValue(afwMath.MEAN), 0.0, stats.getValue(afwMath.STDEV)]

    def testCopyGoodPixelsMask(self):
        """Test MaskedImages"""

        truth_mean, mean, truth_stdev, stdev = self._testCopyGoodPixelsImpl(True)

        self.assertEqual(truth_mean, mean)
        self.assertEqual(truth_stdev, stdev)

    def testCopyGoodPixelsNaN(self):
        """Test Images with NaN"""
        truth_mean, mean, truth_stdev, stdev = self._testCopyGoodPixelsImpl(False)

        self.assertEqual(truth_mean, mean)
        self.assertEqual(truth_stdev, stdev)

#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

class CopyGoodPixelsAfwdataTestCase(unittest.TestCase):
    """A test case for copyGoodPixels using afwdata
    """
    def referenceTest(self, destImage, srcImage, badPixelMask):
        """Compare lsst implemenation of copyGoodPixels to a reference implementation.
        
        Returns the number of good pixels
        """
        # this call leaves destImage alone:
        refDestImage, refNumGoodPix = referenceCopyGoodPixelsMaskedImage(destImage, srcImage, badPixelMask)
        refDestImageArrayList = refDestImage.getArrays()

        # this updates destImage:
        afwNumGoodPix = coaddUtils.copyGoodPixels(destImage, srcImage, badPixelMask)
        self.assertEqual(refNumGoodPix, afwNumGoodPix)
        
        destImageArrayList = destImage.getArrays()
        maskArr = destImageArrayList[1]
        
        for name, ind in (("image", 0), ("mask", 1), ("variance", 2)):
            if not numpy.allclose(destImageArrayList[ind], refDestImageArrayList[ind]):
                errMsgList = (
                    "Computed %s does not match reference for badPixelMask=%s:" % (name, badPixelMask),
                    "computed=  %s" % (destImageArrayList[ind],),
                    "reference= %s" % (refDestImageArrayList[ind],),
                )
                errMsg = "\n".join(errMsgList)
                self.fail(errMsg)
        return refNumGoodPix
        
    def testMed(self):
        """Test copyGoodPixels by adding an image with known bad pixels using varying masks
        """
        medBBox = afwGeom.Box2I(afwGeom.Point2I(130, 315), afwGeom.Extent2I(20, 21))
        srcImage = afwImage.MaskedImageF(afwImage.MaskedImageF(medMIPath), medBBox, afwImage.PARENT)
        destImage = afwImage.MaskedImageF(medBBox)
        for badPixelMask in (0x00, 0xFF):
            self.referenceTest(destImage, srcImage, badPixelMask)
    
    def testMultSizes(self):
        """Test copyGoodPixels by adding various subregions of the med image
        to a destImage that's a slightly different shape
        """
        bbox = afwGeom.Box2I(afwGeom.Point2I(130, 315), afwGeom.Extent2I(30, 31))
        fullMaskedImage = afwImage.MaskedImageF(medMIPath)
        srcImage = afwImage.MaskedImageF(fullMaskedImage, bbox, afwImage.PARENT)
        coaddBBox = afwGeom.Box2I(
            srcImage.getXY0() + afwGeom.Extent2I(-6, +4),
            srcImage.getDimensions() + afwGeom.Extent2I(10, -10))
        destImage = afwImage.MaskedImageF(coaddBBox)
        badPixelMask = 0x0
        
        # add masked image that extends beyond destImage in y
        numGoodPix = self.referenceTest(destImage, srcImage, badPixelMask)
        self.assertNotEqual(maskedImageView, 0)

        # add masked image that extends beyond destImage in x
        bbox = afwGeom.Box2I(afwGeom.Point2I(120, 320), afwGeom.Extent2I(50, 10))
        srcImage = afwImage.MaskedImageF(fullMaskedImage, bbox, afwImage.PARENT)
        numGoodPix = self.referenceTest(destImage, srcImage, badPixelMask)
        self.assertNotEqual(numGoodPix, 0)
        
        # add masked image that is fully within the destImage
        bbox = afwGeom.Box2I(afwGeom.Point2I(130, 320), afwGeom.Extent2I(10, 10))
        srcImage = afwImage.MaskedImageF(fullMaskedImage, bbox, afwImage.PARENT)
        numGoodPix = self.referenceTest(destImage, srcImage, badPixelMask)
        self.assertNotEqual(numGoodPix, 0)
        
        # add masked image that does not overlap destImage
        bbox = afwGeom.Box2I(afwGeom.Point2I(0, 0), afwGeom.Extent2I(10, 10))
        srcImage = afwImage.MaskedImageF(fullMaskedImage, bbox, afwImage.PARENT)
        numGoodPix = self.referenceTest(destImage, srcImage, badPixelMask)
        self.assertEqual(numGoodPix, 0)


def suite():
    """Return a suite containing all the test cases in this module.
    """
    utilsTests.init()

    suites = []
    suites += unittest.makeSuite(CopyGoodPixelsTestCase)

    if dataDir:
        suites += unittest.makeSuite(CopyGoodPixelsAfwdataTestCase)
    else:
        warnings.warn("Skipping some tests because afwdata is not setup")
    suites += unittest.makeSuite(utilsTests.MemoryTestCase)

    return unittest.TestSuite(suites)


def run(shouldExit=False):
    """Run the tests"""
    utilsTests.run(suite(), shouldExit)

if __name__ == "__main__":
    run(True)
