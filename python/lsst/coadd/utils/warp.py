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
import lsst.afw.geom as afwGeom
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
        
        @param policy: see policy/WarpDictionary.paf
        @param logName: name by which messages are logged
        """
        return cls(
            warpingKernelName = policy.getString("warpingKernelName"),
            interpLength = policy.getInt("interpLength"),
            cacheSize = policy.getInt("cacheSize"),
            logName = logName,
        )
    
    def overlappingBBox(self, wcs, exposure):
        """Compute the bounding box of the exposure that results from warping an exposure to a new wcs
        
        The bounding box must include all warped pixels; it may be a bit oversize.
        
        @param wcs: WCS of warped exposure
        @param Exposure to warp

        @return bbox: bounding box of warped exposure
        """
        inWcs = exposure.getWcs()
        inBBox = bboxFromImage.bboxFromImage(exposure)
        inPosBox = afwGeom.BoxD(inBBox)
        inCornerPosList = (
            inPosBox.getMin(),
            afwGeom.makePointD(inPosBox.getMinX(), inPosBox.getMaxY()),
            afwGeom.makePointD(inPosBox.getMaxX(), inPosBox.getMinY()),
            inPosBox.getMax(),
        )
        outCornerPosList = [wcs.skyToPixel(inWcs.pixelToSky(inPos)) for inPos in inCornerPosList]
        outPosBox = afwGeom.BoxD()
        for outCornerPos in outCornerPosList:
            outPosBox.include(outCornerPos)
        outBBox = afwGeom.BoxI(outPosBox, afwGeom.BoxI.EXPAND)
        return outBBox

    def warpExposure(self, wcs, exposure, border=0, maxBBox=None):
        """Warp an exposure
        
        @param wcs: WCS of warped exposure
        @param Exposure to warp
        @param border grow bbox of warped exposure by this amount in all directions (pixels);
            if negative then the bbox is shrunk;
            border is applied before maxBBox
        @param maxBBox: maximum allowed bbox of warped exposure (an afwGeom.BoxI);
            if None then the warped exposure will be just big enough to contain all warped pixels;
            if provided then the warped exposure may be smaller, and so missing some warped pixels

        @return warpedExposure: warped exposure
        """
        self._log.log(pexLog.Log.INFO, "warp exposure")
        
        outBBox = self.overlappingBBox(wcs, exposure)
        if border:
            outBBox.grow(border)
        if maxBBox:
            outBBox.clip(maxBBox)
        warpedExposure = bboxFromImage.imageFromBBox(outBBox, type(exposure))
        warpedExposure.setWcs(wcs)
        afwMath.warpExposure(warpedExposure, exposure, self._warpingKernel, self._interpLength)
        return warpedExposure
