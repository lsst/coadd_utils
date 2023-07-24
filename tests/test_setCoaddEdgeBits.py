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

"""Test lsst.coadd.utils.setCoaddEdgeBits
"""
import unittest

import numpy as np

import lsst.utils.tests
import lsst.geom as geom
import lsst.afw.image as afwImage
import lsst.coadd.utils as coaddUtils
from lsst.log import Log

Log.getLogger("coadd.utils").setLevel(Log.INFO)


class SetCoaddEdgeBitsTestCase(lsst.utils.tests.TestCase):
    """A test case for setCoaddEdgeBits
    """

    def testRandomMap(self):
        """Test setCoaddEdgeBits using a random depth map
        """
        imDim = geom.Extent2I(50, 55)
        coaddMask = afwImage.Mask(imDim)

        np.random.seed(12345)
        depthMapArray = np.random.randint(0, 3, list((imDim[1], imDim[0]))).astype(np.uint16)
        depthMap = afwImage.makeImageFromArray(depthMapArray)

        refCoaddMask = afwImage.Mask(imDim)
        edgeMask = afwImage.Mask.getPlaneBitMask("NO_DATA")
        refCoaddMask.array |= np.array(np.where(depthMapArray > 0, 0, edgeMask),
                                       dtype=refCoaddMask.array.dtype)

        coaddUtils.setCoaddEdgeBits(coaddMask, depthMap)
        self.assertMasksEqual(coaddMask, refCoaddMask)


class MemoryTester(lsst.utils.tests.MemoryTestCase):
    pass


def setup_module(module):
    lsst.utils.tests.init()


if __name__ == "__main__":
    lsst.utils.tests.init()
    unittest.main()
