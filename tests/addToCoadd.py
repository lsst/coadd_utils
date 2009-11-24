#!/usr/bin/env python
"""Test lsst.coadd.utils.addToCoadd
"""
import os
import math
import pdb # we may want to say pdb.set_trace()
import sys
import unittest

import numpy

import eups
import lsst.afw.image as afwImage
import lsst.afw.image.testUtils as imTestUtils
import lsst.afw.math as afwMath
import lsst.afw.display.ds9 as ds9
import lsst.utils.tests as utilsTests
import lsst.pex.logging as pexLog
import lsst.pex.exceptions as pexEx
import lsst.coadd.utils as coaddUtils

try:
    display
except NameError:
    display = False
    Verbosity = 0 # increase to see trace

pexLog.Trace_setVerbosity("lsst.coadd.utils", Verbosity)

dataDir = eups.productDir("afwdata")
if not dataDir:
    print >> sys.stderr, "Must set up afwdata to run these tests"
else:
    medMIPath = os.path.join(dataDir, "med")
    
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-


def referenceAddToCoadd(coadd, weightMap, maskedImage, badPixelMask, weight):
    """Reference implementation of lsst.coadd.utils.addToCoadd
    
    Unlike lsst.coadd.utils.addToCoadd this one does not change the inputs.
    
    Inputs:
    - coadd: coadd before adding maskedImage
    - weightMap: weight map before adding maskedImage
    - maskedImage: masked image to add to coadd
    - badPixelMask: mask of bad pixels to ignore
    - weight: relative weight of this maskedImage

    Returns two items:
    - coaddArrayList: new coadd as a list of image, mask, variance numpy arrays
    - weightMapArray: new weight map, as a numpy array
    """
    maskedImageArrayList = imTestUtils.arraysFromMaskedImage(maskedImage)
    coaddArrayList = imTestUtils.arraysFromMaskedImage(coadd)
    weightMapArray = imTestUtils.arrayFromImage(weightMap)

    badMaskArr = (maskedImageArrayList[1] & badPixelMask) != 0
    for ind in (0, 2):
        coaddArray = coaddArrayList[ind]
        coaddArray += numpy.where(badMaskArr, 0, maskedImageArrayList[ind])*(weight if ind == 0 else weight**2)
    coaddArray = coaddArrayList[1]
    coaddArray |= numpy.where(badMaskArr, 0, maskedImageArrayList[1])
    weightMapArray += numpy.where(badMaskArr, 0, 1)*weight
    return coaddArrayList, weightMapArray


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

        if useMask:
            coaddUtils.divide(coadd, weightMap)
        else:
            coadd /= weightMap
            pass

        if display:
            ds9.mtv(image, title="image", frame=1)
            ds9.mtv(coadd, title="coadd", frame=2)
            ds9.mtv(weightMap, title="weightMap", frame=3)

        stats = afwMath.makeStatistics(coadd, afwMath.MEAN | afwMath.STDEV)

        return [trueImageValue, stats.getValue(afwMath.MEAN), 0.0, stats.getValue(afwMath.STDEV)]

    def testAddToCoaddMaskUniformWeight(self):
        """Test coadded MaskedImages with uniform weights"""

        uniformWeight = True
        truth_mean, mean, truth_stdev, stdev = self._testAddToCoaddImpl(True, uniformWeight)

        self.assertEqual(truth_mean, mean)
        self.assertEqual(truth_stdev, stdev)

    def testAddToCoaddMaskNonUniformWeight(self):
        """Test coadded MaskedImages with non-uniform weights"""

        uniformWeight = False
        truth_mean, mean, truth_stdev, stdev = self._testAddToCoaddImpl(True, uniformWeight)

        self.assertEqual(truth_mean, mean)
        self.assertEqual(truth_stdev, stdev)

    def testAddToCoaddNaNUniformWeight(self):
        """Test coadded Images with uniform weights and NaN"""

        uniformWeight = True
        truth_mean, mean, truth_stdev, stdev = self._testAddToCoaddImpl(False, uniformWeight)

        self.assertEqual(truth_mean, mean)
        self.assertEqual(truth_stdev, stdev)

    def testAddToCoaddNaNNonUniformWeight(self):
        """Test coadded Images with non-uniform weights"""

        uniformWeight = False
        truth_mean, mean, truth_stdev, stdev = self._testAddToCoaddImpl(False, uniformWeight)

        self.assertAlmostEqual(truth_mean, mean)
        self.assertEqual(truth_stdev, stdev)

#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

class AddToCoaddAfwdataTestCase(unittest.TestCase):
    """A test case for addToCoadd using afwdata
    """

    def referenceTest(self, coadd, weightMap, image, badPixelMask, weight):
        """Compare lsst implemenation of addToCoadd to a reference implementation.
        """
        refCoaddArrayList, refweightMapArray = \
            referenceAddToCoadd(coadd, weightMap, image, badPixelMask, weight)
        coaddUtils.addToCoadd(coadd, weightMap, image, badPixelMask, weight) # changes the inputs
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
        
    def testMed(self):
        """Test addToCoadd by adding an image with known bad pixels using varying masks
        """
        image = afwImage.MaskedImageF(medMIPath)
        coadd = image.Factory(image.getDimensions())
        coadd.set(0, 0x0, 0)
        weightMap = image.getImage().Factory(image.getDimensions(), 0)
        weight = 0.9
        for badPixelMask in (0x01, 0x03):
            self.referenceTest(coadd, weightMap, image, badPixelMask, weight)

def suite():
    """Return a suite containing all the test cases in this module.
    """
    utilsTests.init()

    suites = []
    suites += unittest.makeSuite(AddToCoaddTestCase)

    if dataDir:
        suites += unittest.makeSuite(AddToCoaddAfwdataTestCase)
    suites += unittest.makeSuite(utilsTests.MemoryTestCase)

    return unittest.TestSuite(suites)


def run(shouldExit=False):
    """Run the tests"""
    utilsTests.run(suite(), shouldExit)

if __name__ == "__main__":
    run(True)
