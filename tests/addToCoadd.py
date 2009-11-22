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
import lsst.utils.tests as utilsTests
import lsst.pex.logging as pexLog
import lsst.pex.exceptions as pexEx
import lsst.coadd.utils as coaddUtils

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
        coaddArray += numpy.where(badMaskArr, 0, maskedImageArrayList[ind])
    coaddArray = coaddArrayList[1]
    coaddArray |= numpy.where(badMaskArr, 0, maskedImageArrayList[1])
    weightMapArray += numpy.where(badMaskArr, 0, 1) * weight
    return coaddArrayList, weightMapArray


class AddToCoaddTestCase(unittest.TestCase):
    """A test case for addToCoadd
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
        coadd = afwImage.MaskedImageF(image.getDimensions())
        coadd *= 0.0
        weightMap = afwImage.ImageF(image.getDimensions(), 0)
        weight = 0.9
        for badPixelMask in (0x01, 0x03):
            self.referenceTest(coadd, weightMap, image, badPixelMask, weight)


def suite():
    """Return a suite containing all the test cases in this module.
    """
    utilsTests.init()

    suites = []
    if dataDir:
        suites += unittest.makeSuite(AddToCoaddTestCase)
    suites += unittest.makeSuite(utilsTests.MemoryTestCase)

    return unittest.TestSuite(suites)

if __name__ == "__main__":
    utilsTests.run(suite())
