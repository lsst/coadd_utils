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
import unittest

import numpy as np

import lsst.utils
import lsst.utils.tests
import lsst.geom as geom
import lsst.afw.image as afwImage
import lsst.afw.math as afwMath
import lsst.afw.display.ds9 as ds9
import lsst.pex.exceptions as pexExcept
import lsst.coadd.utils as coaddUtils
from lsst.log import Log

try:
    display
except NameError:
    display = False

Log.getLogger("coadd.utils").setLevel(Log.INFO)

try:
    AfwdataDir = lsst.utils.getPackageDir('afwdata')
except Exception:
    AfwdataDir = None
# path to a medium-sized MaskedImage, relative to afwdata package root
MedMiSubpath = os.path.join("data", "med.fits")


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
    - overlapBBox: the overlap region relative to the parent (geom.Box2I)
    - coaddArrayList: new coadd as a list of image, mask, variance numpy arrays
    - weightMapArray: new weight map, as a numpy array
    """
    overlapBBox = coadd.getBBox()
    overlapBBox.clip(maskedImage.getBBox())

    weightMapArray = weightMap.getArray().copy()
    coaddArrayList = coadd.image.array.copy(), coadd.mask.array.copy(), coadd.variance.array.copy()

    if overlapBBox.isEmpty():
        return (overlapBBox, coaddArrayList, weightMapArray)

    maskedImageArrayList = maskedImage.image.array, maskedImage.mask.array, maskedImage.variance.array
    badMaskArr = (maskedImageArrayList[1] & badPixelMask) != 0

    coaddSlices = slicesFromBox(overlapBBox, coadd)
    imageSlices = slicesFromBox(overlapBBox, maskedImage)

    badMaskView = badMaskArr[imageSlices[1], imageSlices[0]]
    for ind in range(3):
        coaddView = coaddArrayList[ind][coaddSlices[1], coaddSlices[0]]
        maskedImageView = maskedImageArrayList[ind][imageSlices[1], imageSlices[0]]
        if ind == 1:  # mask plane
            coaddView |= np.where(badMaskView, 0, maskedImageView)
        else:  # image or variance plane
            if ind == 0:  # image
                weightFac = weight
            else:  # variance
                weightFac = weight**2
            coaddView += np.where(badMaskView, 0, maskedImageView)*weightFac
    weightMapView = weightMapArray[coaddSlices[1], coaddSlices[0]]
    weightMapView += np.where(badMaskView, 0, 1)*weight
    return overlapBBox, coaddArrayList, weightMapArray


class AddToCoaddTestCase(unittest.TestCase):
    """A test case for addToCoadd
    """

    def _testAddToCoaddImpl(self, useMask, uniformWeight=True):
        """Test coadd"""

        trueImageValue = 10.0
        imBBox = geom.Box2I(geom.Point2I(0, 0), geom.Extent2I(10, 20))
        if useMask:
            coadd = afwImage.MaskedImageF(imBBox)
            weightMap = coadd.getImage().Factory(coadd.getBBox())

            badBits = 0x1
            badPixel = (float("NaN"), badBits, 0)
            truth = (trueImageValue, 0x0, 0)
        else:
            coadd = afwImage.ImageF(imBBox)
            weightMap = coadd.Factory(coadd.getBBox())

            badPixel = float("NaN")
            truth = trueImageValue

        for i in range(0, 20, 3):
            image = coadd.Factory(coadd.getDimensions())
            image.set(badPixel)

            subBBox = geom.Box2I(geom.Point2I(0, i),
                                 image.getDimensions() - geom.Extent2I(0, i))
            subImage = image.Factory(image, subBBox, afwImage.LOCAL)
            subImage.set(truth)
            del subImage

            weight = 1.0 if uniformWeight else 1.0 + 0.1*i
            if useMask:
                coaddUtils.addToCoadd(coadd, weightMap, image, badBits, weight)
            else:
                coaddUtils.addToCoadd(coadd, weightMap, image, weight)

            self.assertEqual(image[-1, -1, afwImage.LOCAL], truth)

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


class AddToCoaddAfwdataTestCase(unittest.TestCase):
    """A test case for addToCoadd using afwdata
    """

    def referenceTest(self, coadd, weightMap, image, badPixelMask, weight):
        """Compare lsst implemenation of addToCoadd to a reference implementation.

        Returns the overlap bounding box
        """
        # this call leaves coadd and weightMap alone:
        overlapBBox, refCoaddArrayList, refweightMapArray = \
            referenceAddToCoadd(coadd, weightMap, image, badPixelMask, weight)
        # this updates coadd and weightMap:
        afwOverlapBox = coaddUtils.addToCoadd(coadd, weightMap, image, badPixelMask, weight)
        self.assertEqual(overlapBBox, afwOverlapBox)

        weightMapArray = weightMap.getArray()
        coaddArrayList = coadd.image.array, coadd.mask.array, coadd.variance.array

        for name, ind in (("image", 0), ("mask", 1), ("variance", 2)):
            if not np.allclose(coaddArrayList[ind], refCoaddArrayList[ind]):
                errMsgList = (
                    "Computed %s does not match reference for badPixelMask=%s:" % (name, badPixelMask),
                    "computed=  %s" % (coaddArrayList[ind],),
                    "reference= %s" % (refCoaddArrayList[ind],),
                )
                errMsg = "\n".join(errMsgList)
                self.fail(errMsg)
        if not np.allclose(weightMapArray, refweightMapArray):
            errMsgList = (
                "Computed weight map does not match reference for badPixelMask=%s:" % (badPixelMask,),
                "computed=  %s" % (weightMapArray,),
                "reference= %s" % (refweightMapArray,),
            )
            errMsg = "\n".join(errMsgList)
            self.fail(errMsg)
        return overlapBBox

    @unittest.skipUnless(AfwdataDir, "afwdata not available")
    def testMed(self):
        """Test addToCoadd by adding an image with known bad pixels using varying masks
        """
        medBBox = geom.Box2I(geom.Point2I(130, 315), geom.Extent2I(20, 21))
        medMIPath = os.path.join(AfwdataDir, MedMiSubpath)
        maskedImage = afwImage.MaskedImageF(afwImage.MaskedImageF(medMIPath), medBBox)
        coadd = afwImage.MaskedImageF(medBBox)
        weightMap = afwImage.ImageF(medBBox)
        weight = 0.9
        for badPixelMask in (0x00, 0xFF):
            self.referenceTest(coadd, weightMap, maskedImage, badPixelMask, weight)

    @unittest.skipUnless(AfwdataDir, "afwdata not available")
    def testMultSizes(self):
        """Test addToCoadd by adding various subregions of the med image
        to a coadd that's a slightly different shape
        """
        bbox = geom.Box2I(geom.Point2I(130, 315), geom.Extent2I(30, 31))
        medMIPath = os.path.join(AfwdataDir, MedMiSubpath)
        fullMaskedImage = afwImage.MaskedImageF(medMIPath)
        maskedImage = afwImage.MaskedImageF(fullMaskedImage, bbox)
        coaddBBox = geom.Box2I(
            maskedImage.getXY0() + geom.Extent2I(-6, +4),
            maskedImage.getDimensions() + geom.Extent2I(10, -10))
        coadd = afwImage.MaskedImageF(coaddBBox)
        weightMap = afwImage.ImageF(coaddBBox)
        badPixelMask = 0x0

        # add masked image that extends beyond coadd in y
        overlapBBox = self.referenceTest(coadd, weightMap, maskedImage, badPixelMask, 0.5)
        self.assertFalse(overlapBBox.isEmpty())

        # add masked image that extends beyond coadd in x
        bbox = geom.Box2I(geom.Point2I(120, 320), geom.Extent2I(50, 10))
        maskedImage = afwImage.MaskedImageF(fullMaskedImage, bbox)
        overlapBBox = self.referenceTest(coadd, weightMap, maskedImage, badPixelMask, 0.5)
        self.assertFalse(overlapBBox.isEmpty())

        # add masked image that is fully within the coadd
        bbox = geom.Box2I(geom.Point2I(130, 320), geom.Extent2I(10, 10))
        maskedImage = afwImage.MaskedImageF(fullMaskedImage, bbox)
        overlapBBox = self.referenceTest(coadd, weightMap, maskedImage, badPixelMask, 0.5)
        self.assertFalse(overlapBBox.isEmpty())

        # add masked image that does not overlap coadd
        bbox = geom.Box2I(geom.Point2I(0, 0), geom.Extent2I(10, 10))
        maskedImage = afwImage.MaskedImageF(fullMaskedImage, bbox)
        overlapBBox = self.referenceTest(coadd, weightMap, maskedImage, badPixelMask, 0.5)
        self.assertTrue(overlapBBox.isEmpty())

    def testAssertions(self):
        """Test that addToCoadd requires coadd and weightMap to have the same dimensions and xy0"""
        maskedImage = afwImage.MaskedImageF(geom.Extent2I(10, 10))
        coadd = afwImage.MaskedImageF(geom.Extent2I(11, 11))
        coadd.setXY0(5, 6)
        for dw, dh in (1, 0), (0, 1), (-1, 0), (0, -1):
            weightMapBBox = geom.Box2I(coadd.getXY0(), coadd.getDimensions() + geom.Extent2I(dw, dh))
            weightMap = afwImage.ImageF(weightMapBBox)
            weightMap.setXY0(coadd.getXY0())
            try:
                coaddUtils.addToCoadd(coadd, weightMap, maskedImage, 0x0, 0.1)
                self.fail("should have raised exception")
            except pexExcept.Exception:
                pass
        for dx0, dy0 in (1, 0), (0, 1), (-1, 0), (0, -1):
            weightMapBBox = geom.Box2I(coadd.getXY0() + geom.Extent2I(dx0, dy0), coadd.getDimensions())
            weightMap = afwImage.ImageF(weightMapBBox)
            try:
                coaddUtils.addToCoadd(coadd, weightMap, maskedImage, 0x0, 0.1)
                self.fail("should have raised exception")
            except pexExcept.Exception:
                pass


class MemoryTester(lsst.utils.tests.MemoryTestCase):
    pass


def setup_module(module):
    lsst.utils.tests.init()


if __name__ == "__main__":
    lsst.utils.tests.init()
    unittest.main()
