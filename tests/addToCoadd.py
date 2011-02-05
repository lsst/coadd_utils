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

"""Test lsst.coadd.utils.addToCoadd
"""
import os
import pdb # we may want to say pdb.set_trace()
import unittest
import warnings
import sys

import numpy

import eups
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
    medMIPath = os.path.join(dataDir, "med")
    
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

def slicesFromBox(box, image):
    """Computes the numpy slice in x and y associated with a parent bounding box
    given an image/maskedImage/exposure
    """
    startInd = (box.getMinX() - image.getX0(), box.getMinY() - image.getY0())
    stopInd = (startInd[0] + box.getWidth(), startInd[1] + box.getHeight())
#     print "slicesFromBox: box=(min=%s, dim=%s), imxy0=%s, imdim=%s, startInd=%s, stopInd=%s" %\
#         (box.getMin(), box.getDimensions(), image.getXY0(), image.getDimensions(), startInd, stopInd)
    return (
        slice(startInd[0], stopInd[0]),
        slice(startInd[1], stopInd[1]),
    )

def referenceAddToCoadd(coadd, weightMap, maskedImage, badPixelMask, weight):
    """Reference implementation of lsst.coadd.utils.addToCoadd
    
    Unlike lsst.coadd.utils.addToCoadd this one does not update the input coadd and weightMap,
    but instead returns the new versions (as numpy arrays).
    
    Inputs:
    - coadd: coadd before adding maskedImage (a MaskedImage)
    - weightMap: weight map before adding maskedImage (an Image)
    - maskedImage: masked image to add to coadd (a MaskedImage)
    - badPixelMask: mask of bad pixels to ignore (an int)
    - weight: relative weight of this maskedImage (a float)

    Returns three items:
    - overlapBox: the overlap region relative to the parent (afwGeom::BoxI)
    - coaddArrayList: new coadd as a list of image, mask, variance numpy arrays
    - weightMapArray: new weight map, as a numpy array
    """
    overlapBox = coaddUtils.bboxFromImage(coadd)
    overlapBox.clip(coaddUtils.bboxFromImage(maskedImage))

    coaddArrayList = imTestUtils.arraysFromMaskedImage(coadd)
    weightMapArray = imTestUtils.arrayFromImage(weightMap)
    
    if overlapBox.isEmpty():
        return (overlapBox, coaddArrayList, weightMapArray)
    
    maskedImageArrayList = imTestUtils.arraysFromMaskedImage(maskedImage)
    badMaskArr = (maskedImageArrayList[1] & badPixelMask) != 0
    
    coaddSlices = slicesFromBox(overlapBox, coadd)
    imageSlices = slicesFromBox(overlapBox, maskedImage)

    badMaskView = badMaskArr[imageSlices[0], imageSlices[1]]
    for ind in range(3):
        coaddView = coaddArrayList[ind][coaddSlices[0], coaddSlices[1]]
        maskedImageView = maskedImageArrayList[ind][imageSlices[0], imageSlices[1]]
        if ind == 1: # mask plane
            coaddView |= numpy.where(badMaskView, 0, maskedImageView)
        else: # image or variance plane
            if ind == 0: # image
                weightFac = weight
            else: # variance
                weightFac = weight**2
            coaddView += numpy.where(badMaskView, 0, maskedImageView)*weightFac
    weightMapView = weightMapArray[coaddSlices[0], coaddSlices[1]]
    weightMapView += numpy.where(badMaskView, 0, 1)*weight
    return overlapBox, coaddArrayList, weightMapArray


class AddToCoaddTestCase(unittest.TestCase):
    """A test case for addToCoadd
    """

    def _testAddToCoaddImpl(self, useMask, uniformWeight=True):
        """Test coadd"""

        trueImageValue = 10.0
        if useMask:
            coadd = afwImage.MaskedImageF(10, 20)
            weightMap = coadd.getImage().Factory(coadd.getDimensions(), 0)

            badBits = 0x1
            badPixel = (float("NaN"), badBits, 0)
            zero = (0.0, 0x0, 0)
            truth = (trueImageValue, 0x0, 0)
        else:
            coadd = afwImage.ImageF(10, 20)
            weightMap = coadd.Factory(coadd.getDimensions(), 0)

            badPixel = float("NaN")
            zero = 0.0
            truth = trueImageValue

        coadd.set(zero)

        for i in range(0, 20, 3):
            image = coadd.Factory(coadd.getDimensions())
            image.set(badPixel)

            subImage = image.Factory(image, afwImage.BBox(afwImage.PointI(0, i),
                                                          image.getWidth(), image.getHeight() - i))
            subImage.set(truth)
            del subImage

            weight = 1.0 if uniformWeight else 1.0 + 0.1*i
            if useMask:
                coaddUtils.addToCoadd(coadd, weightMap, image, badBits, weight)
            else:
                coaddUtils.addToCoadd(coadd, weightMap, image, weight)

            self.assertEqual(image.get(image.getWidth() - 1, image.getHeight() - 1), truth)

        coadd /= weightMap

        if display:
            ds9.mtv(image, title="image", frame=1)
            ds9.mtv(coadd, title="coadd", frame=2)
            ds9.mtv(weightMap, title="weightMap", frame=3)

        stats = afwMath.makeStatistics(coadd, afwMath.MEAN | afwMath.STDEV)

        return [trueImageValue, stats.getValue(afwMath.MEAN), 0.0, stats.getValue(afwMath.STDEV)]

    def testAddToCoaddMask(self):
        """Test coadded MaskedImages"""

        for uniformWeight in (False, True):
            truth_mean, mean, truth_stdev, stdev = self._testAddToCoaddImpl(True, uniformWeight)
    
            self.assertEqual(truth_mean, mean)
            self.assertEqual(truth_stdev, stdev)

    def testAddToCoaddNaN(self):
        """Test coadded Images with NaN"""

        for uniformWeight in (False, True):
            truth_mean, mean, truth_stdev, stdev = self._testAddToCoaddImpl(False, uniformWeight)

            self.assertEqual(truth_mean, mean)
            self.assertEqual(truth_stdev, stdev)

#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

class AddToCoaddAfwdataTestCase(unittest.TestCase):
    """A test case for addToCoadd using afwdata
    """
    def referenceTest(self, coadd, weightMap, image, badPixelMask, weight):
        """Compare lsst implemenation of addToCoadd to a reference implementation.
        
        Returns the overlap bounding box
        """
        # this call leaves coadd and weightMap alone:
        overlapBox, refCoaddArrayList, refweightMapArray = \
            referenceAddToCoadd(coadd, weightMap, image, badPixelMask, weight)
        # this updated coadd and weightMap:
        afwOverlapBox = coaddUtils.addToCoadd(coadd, weightMap, image, badPixelMask, weight)
        self.assertEquals(overlapBox, afwOverlapBox)
        
        coaddArrayList = imTestUtils.arraysFromMaskedImage(coadd)
        maskArr = coaddArrayList[1]
        weightMapArray = imTestUtils.arrayFromImage(weightMap)
        
        for name, ind in (("image", 0), ("mask", 1), ("variance", 2)):
            if not numpy.allclose(coaddArrayList[ind], refCoaddArrayList[ind]):
                errMsgList = (
                    "Computed %s does not match reference for badPixelMask=%s:" % (name, badPixelMask),
                    "computed=  %s" % (coaddArrayList[ind],),
                    "reference= %s" % (refCoaddArrayList[ind],),
                )
                errMsg = "\n".join(errMsgList)
                self.fail(errMsg)
        if not numpy.allclose(weightMapArray, refweightMapArray):
            errMsgList = (
                "Computed weight map does not match reference for badPixelMask=%s:" % (badPixelMask,),
                "computed=  %s" % (weightMapArray,),
                "reference= %s" % (refweightMapArray,),
            )
            errMsg = "\n".join(errMsgList)
            self.fail(errMsg)
        return overlapBox
        
    def testMed(self):
        """Test addToCoadd by adding an image with known bad pixels using varying masks
        """
        medBBox = afwImage.BBox(afwImage.PointI(130, 315), 20, 21)
        maskedImage = afwImage.MaskedImageF(afwImage.MaskedImageF(medMIPath), medBBox)
        coadd = afwImage.MaskedImageF(maskedImage.getDimensions())
        coadd.setXY0(maskedImage.getXY0())
        weightMap = afwImage.ImageF(maskedImage.getDimensions())
        weightMap.setXY0(maskedImage.getXY0())
        weight = 0.9
        for badPixelMask in (0x00, 0xFF):
            self.referenceTest(coadd, weightMap, maskedImage, badPixelMask, weight)
    
    def testMultSizes(self):
        """Test addToCoadd by adding various subregions of the med image
        to a coadd that's a slightly different shape
        """
        bbox = afwImage.BBox(afwImage.PointI(130, 315), 30, 31)
        fullMaskedImage = afwImage.MaskedImageF(medMIPath)
        maskedImage = afwImage.MaskedImageF(fullMaskedImage, bbox)
        coadd = afwImage.MaskedImageF(maskedImage.getWidth() + 10, maskedImage.getHeight() - 10)
        coadd.setXY0(maskedImage.getX0() - 6, maskedImage.getY0() + 4)
        weightMap = afwImage.ImageF(coadd.getDimensions())
        weightMap.setXY0(coadd.getXY0())
        badPixelMask = 0x0
        
        # add masked image that extends beyond coadd in y
        overlapBox = self.referenceTest(coadd, weightMap, maskedImage, badPixelMask, 0.5)
        self.assertFalse(overlapBox.isEmpty())

        # add masked image that extends beyond coadd in x
        bbox = afwImage.BBox(afwImage.PointI(120, 320), 50, 10)
        maskedImage = afwImage.MaskedImageF(fullMaskedImage, bbox)
        overlapBox = self.referenceTest(coadd, weightMap, maskedImage, badPixelMask, 0.5)
        self.assertFalse(overlapBox.isEmpty())
        
        # add masked image that is fully within the coadd
        bbox = afwImage.BBox(afwImage.PointI(130, 320), 10, 10)
        maskedImage = afwImage.MaskedImageF(fullMaskedImage, bbox)
        overlapBox = self.referenceTest(coadd, weightMap, maskedImage, badPixelMask, 0.5)
        self.assertFalse(overlapBox.isEmpty())
        
        # add masked image that does not overlap coadd
        bbox = afwImage.BBox(afwImage.PointI(0, 0), 10, 10)
        maskedImage = afwImage.MaskedImageF(fullMaskedImage, bbox)
        overlapBox = self.referenceTest(coadd, weightMap, maskedImage, badPixelMask, 0.5)
        self.assertTrue(overlapBox.isEmpty())
    
    def testAssertions(self):
        """Test that addToCoadd requires coadd and weightMap to have the same dimensions and xy0"""
        maskedImage = afwImage.MaskedImageF(10, 10)
        coadd = afwImage.MaskedImageF(11, 11)
        coadd.setXY0(5, 6)
        for dw, dh in (1, 0), (0, 1), (-1, 0), (0, -1):
            weightMap = afwImage.ImageF(coadd.getWidth() + dw, coadd.getHeight() + dh)
            weightMap.setXY0(coadd.getXY0())
            try:
                coaddUtils.addToCoadd(coadd, weightMap, maskedImage, 0x0, 0.1)
                self.fail("should have raised exception")
            except pexExcept.LsstCppException, e:
                pass
        for dx0, dy0 in (1, 0), (0, 1), (-1, 0), (0, -1):
            weightMap = afwImage.ImageF(coadd.getWidth(), coadd.getHeight())
            weightMap.setXY0(coadd.getX0() + dx0, coadd.getY0() + dy0)
            try:
                coaddUtils.addToCoadd(coadd, weightMap, maskedImage, 0x0, 0.1)
                self.fail("should have raised exception")
            except pexExcept.LsstCppException, e:
                pass

def suite():
    """Return a suite containing all the test cases in this module.
    """
    utilsTests.init()

    suites = []
    suites += unittest.makeSuite(AddToCoaddTestCase)

    if dataDir:
        suites += unittest.makeSuite(AddToCoaddAfwdataTestCase)
    else:
        warnings.warn("Skipping some tests because afwdata is not setup")
    suites += unittest.makeSuite(utilsTests.MemoryTestCase)

    return unittest.TestSuite(suites)


def run(shouldExit=False):
    """Run the tests"""
    utilsTests.run(suite(), shouldExit)

if __name__ == "__main__":
    run(True)
