#!/usr/bin/env python
"""Test lsst.coadd.utils.imageMath
"""
import os
import math
import pdb # we may want to say pdb.set_trace()
import unittest

import numpy

import lsst.afw.image as afwImage
import lsst.afw.image.testUtils as imTestUtils
import lsst.afw.math as afwMath
import lsst.utils.tests as utilsTests
import lsst.pex.logging as pexLog
import lsst.pex.exceptions as pexEx
import lsst.coadd.utils as coaddUtils

Verbosity = 0 # increase to see trace
pexLog.Trace_setVerbosity("lsst.coadd.utils", Verbosity)

def referenceDivideMaskedImageByImage(maskedImageArrays, imageArray):
    """Reference implementation of lsst.coadd.utils.divide
    
    Unlike lsst.coadd.utils.divide, this one does not change the inputs.
    
    Inputs:
    - maskedImageArrays: numerator as (image, mask, variance) arrays
    - imageArray: denominator

    Returns the result of maskedImageArrays / imageArray:
        out image = numerator image / denominator
        out mask = in mask
        out variance = numerator variance / (denominator^2)
    """
    return (
        maskedImageArrays[0] / imageArray,
        maskedImageArrays[1],
        maskedImageArrays[2] / (imageArray**2),
    )


class DivideTestCase(unittest.TestCase):
    """A test case for imageMath
    """
    def testMaskedImageOverImage(self):
        """Test division of a MaskedImage by an Image
        """
        Shape = [100, 100]
        MaxFloat = numpy.finfo(numpy.float32).max
        MinFloat = numpy.finfo(numpy.float32).min
        numpy.random.seed(100)
        maskedImageArrays = [
            (numpy.random.random_sample(Shape) - 0.5) * MaxFloat * 2.0,
            numpy.random.random_integers(0, 16, Shape),
            (numpy.random.random_sample(Shape) - 0.5) * MaxFloat * 2.0,
        ]
        imageArray = numpy.zeros(Shape, dtype=float)
        
        specialFloats = (0.0, 0.5, 1.0, 2.0, MaxFloat, MinFloat, MaxFloat / 2.0, MinFloat / 2.0, \
            numpy.nan, numpy.inf, -numpy.inf)
        ind = 0
        for numSf in specialFloats:
            for denSf in specialFloats:
                maskedImageArrays[0].flat[ind] = numSf
                imageArray.flat[ind] = denSf
                ind += 1

        maskedImage = imTestUtils.maskedImageFromArrays(maskedImageArrays, afwImage.MaskedImageF)
        image = imTestUtils.imageFromArray(imageArray, afwImage.ImageF)
        
        # now that the maskedImage and image have been constructed,
        # cast the arrays to float32. This could not be done earlier
        # because the set method of Image/MaskedImage demands double precision, not single precision
        maskedImageArrays[0] = maskedImageArrays[0].astype(numpy.float32)
        maskedImageArrays[2] = maskedImageArrays[2].astype(numpy.float32)
        imageArray = imageArray.astype(numpy.float32)

        referenceMaskedImageArrays = referenceDivideMaskedImageByImage(
            maskedImageArrays, imageArray)
        
        coaddUtils.divide(maskedImage, image)
        cppMaskedImageArrays = imTestUtils.arraysFromMaskedImage(maskedImage)

        errStr = imTestUtils.maskedImagesDiffer(referenceMaskedImageArrays, cppMaskedImageArrays)
        if errStr:
            self.fail(errStr)

def suite():
    """Return a suite containing all the test cases in this module.
    """
    utilsTests.init()

    suites = []
    suites += unittest.makeSuite(DivideTestCase)
    suites += unittest.makeSuite(utilsTests.MemoryTestCase)

    return unittest.TestSuite(suites)

if __name__ == "__main__":
    utilsTests.run(suite())
