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
import sys
import lsst.pex.logging as pexLog
import lsst.afw.image as afwImage
import lsst.afw.math as afwMath
import bboxFromImage

__all__ = ["Warp"]

class Warp(object):
    """Warp exposures
    """
    def __init__(self, warpingKernelName, interpLength=10, cacheSize=0, logName="coadd.utils.WarpExposure"):
        """Create a Warp
        
        Inputs:
        - warpingKernelName: argument to lsst.afw.math.makeWarpingKernel
        - interpLength: interpLength argument to lsst.afw.warpExposure
        - cacheSize: size of computeCache
        - logName: name by which messages are logged
        """
        self._log = pexLog.Log(pexLog.Log.getDefaultLog(), logName)
        self._warpingKernel = afwMath.makeWarpingKernel(warpingKernelName)
        self._warpingKernel.computeCache(cacheSize)
        self._interpLength = int(interpLength)

    @classmethod
    def fromPolicy(cls, policy, logName="coadd.utils.WarpExposure"):
        """Create a Warp from a policy
        
        Inputs:
        - policy: see policy/WarpDictionary.paf
        - logName: name by which messages are logged
        """
        return cls(
            warpingKernelName = policy.getString("warpingKernelName"),
            interpLength = policy.getInt("interpLength"),
            cacheSize = policy.getInt("cacheSize"),
            logName = logName,
        )

    def warpExposure(self, bbox, wcs, exposure):
        """Warp an exposure
        
        Inputs:
        - bbox: bounding box of warped exposure with respect to parent (lsst.afw.geom.BoxI):
            exposure dimensions = bbox.getDimensions(); xy0 = bbox.getMin()
        - wcs: WCS of warped exposure
        - exposure: Exposure to warp
            
        Returns:
        - warpedExposure: warped exposure
        """
        self._log.log(pexLog.Log.INFO, "warp exposure")
        warpedExposure = bboxFromImage.imageFromBBox(bbox, type(exposure))
        warpedExposure.setWcs(wcs)
        afwMath.warpExposure(warpedExposure, exposure, self._warpingKernel, self._interpLength)
        return warpedExposure
