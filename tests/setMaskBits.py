#!/usr/bin/env python
"""Test lsst.coadd.utils.setMaskBits
"""
import os
import math
import pdb # we may want to say pdb.set_trace()
import sys
import unittest

import lsst.afw.image as afwImage
import lsst.utils.tests as utilsTests
import lsst.pex.logging as pexLog
import lsst.pex.exceptions as pexEx
import lsst.coadd.utils as coaddUtils

Verbosity = 0

pexLog.Trace_setVerbosity("lsst.coadd.utils", Verbosity)

def countBits(val):
    nBits = 0
    while val > 0:
        if val & 1 != 0:
            nBits += 1
        val >>= 1
    return nBits

MaxBitMask = (2**afwImage.MaskU_getNumPlanesMax() - 1)

MaskPlaneNameIDDict = dict(afwImage.MaskU.getMaskPlaneDict())

class AddToCoaddTestCase(unittest.TestCase):
    """A test case for setMaskBits
    """
    def testBits(self):
        """Test that the bits set are correct"""
        
        fullPlaneNameList = MaskPlaneNameIDDict.keys()
        totNumBits = countBits(MaxBitMask)
        for i in range(len(fullPlaneNameList)):
            numPlanes = i + 1
            setPlaneNameList = fullPlaneNameList[0:numPlanes]

            bitMask = coaddUtils.makeBitMask(setPlaneNameList)
            self.assertEqual(countBits(bitMask), numPlanes)
            for planeName, planeId in MaskPlaneNameIDDict.iteritems():
                self.assertEqual((bitMask & (1 << planeId)) > 0, planeName in setPlaneNameList)

            invBitMask = coaddUtils.makeBitMask(setPlaneNameList, doInvert=True)
            self.assertEqual(countBits(invBitMask), totNumBits - numPlanes)
            for planeName, planeId in MaskPlaneNameIDDict.iteritems():
                self.assertEqual((invBitMask & (1 << planeId)) > 0, planeName not in setPlaneNameList)

def suite():
    """Return a suite containing all the test cases in this module.
    """
    utilsTests.init()

    suites = []
    suites += unittest.makeSuite(AddToCoaddTestCase)
    suites += unittest.makeSuite(utilsTests.MemoryTestCase)

    return unittest.TestSuite(suites)


def run(shouldExit=False):
    """Run the tests"""
    utilsTests.run(suite(), shouldExit)

if __name__ == "__main__":
    run(True)
