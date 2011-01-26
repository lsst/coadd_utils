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
import lsst.pex.logging as pexLog
import lsst.afw.image as afwImage
import lsst.afw.math as afwMath
import bboxFromImage
import makeBitMask
import utilsLib

__all__ = ["Coadd"]

class Coadd(object):
    """Basic coadd.
    
    Exposures are (by default) warped to the coadd WCS and then added to the coadd
    with a weight of 1 / clipped mean variance.
    
    This class may be subclassed to implement other coadd techniques.
    Typically this is done by overriding addExposure.
    """
    def __init__(self, bbox, wcs, badMaskPlanes, logName="coadd.utils.Coadd"):
        """Create a coadd
        
        Inputs:
        - bbox: bounding box of coadd Exposure with respect to parent (lsst.afw.geom.BoxI):
            coadd dimensions = bbox.getDimensions(); xy0 = bbox.getMin()
        - wcs: WCS of coadd exposure (lsst.afw.math.Wcs)
        - badMaskPlanes: mask planes to pay attention to when rejecting masked pixels.
            Specify as a collection of names.
            badMaskPlanes should always include "EDGE".
        - logName: name by which messages are logged
        """
        self._log = pexLog.Log(pexLog.Log.getDefaultLog(), logName)

        self._badPixelMask = makeBitMask.makeBitMask(badMaskPlanes)

        self._bbox = bbox
        self._wcs = wcs
        blankMaskedImage = bboxFromImage.imageFromBBox(bbox, afwImage.MaskedImageF)
        self._coadd = afwImage.ExposureF(blankMaskedImage, wcs)

        self._weightMap = bboxFromImage.imageFromBBox(bbox, afwImage.ImageF)
        
        self._statsControl = afwMath.StatisticsControl()
        self._statsControl.setNumSigmaClip(3.0)
        self._statsControl.setNumIter(2)
        self._statsControl.setAndMask(self._badPixelMask)
    
    @classmethod
    def fromPolicy(cls, bbox, wcs, policy, logName="coadd.utils.Coadd"):
        """Create a coadd
        
        Inputs:
        - bbox: bounding box of coadd Exposure with respect to parent (lsst.afw.geom.BoxI):
            coadd dimensions = bbox.getDimensions(); xy0 = bbox.getMin()
        - wcs: WCS of coadd exposure (lsst.afw.math.Wcs)
        - policy: coadd policy; see policy/CoaddPolicyDictionary.paf
        - logName: name by which messages are logged
        """
        badMaskPlanes = policy.getArray("badMaskPlanes")
        return cls(bbox, wcs, badMaskPlanes, logName)

    def addExposure(self, exposure, weightFactor=1.0):
        """Add an Exposure to the coadd
        
        Inputs:
        - exposure: Exposure to add to coadd; must be background-subtracted and warped to match the coadd.
        - weightFactor: extra weight factor for this exposure; weight = weightFactor / clipped mean variance
        
        Subclasses may override to preprocess the exposure or change the way it is added to the coadd.
        """
        maskedImage = exposure.getMaskedImage()
        statObj = afwMath.makeStatistics(maskedImage.getVariance(), maskedImage.getMask(),
            afwMath.MEANCLIP, self._statsControl)
        meanVar, meanVarErr = statObj.getResult(afwMath.MEANCLIP);
        weight = weightFactor / float(meanVar)

        self._log.log(pexLog.Log.INFO, "add masked image to coadd; weight=%0.3g" % (weight,))

        utilsLib.addToCoadd(self._coadd.getMaskedImage(), self._weightMap,
            maskedImage, self._badPixelMask, weight)

        return weight

    def getCoadd(self):
        """Get the coadd Exposure, as computed so far
        
        Return the coadd Exposure consisting of the reference exposure and all exposures
        you have added so far. You may call addExposure and getCoadd as often as you like.
        """
        # make a deep copy so I can scale it
        coaddMaskedImage = self._coadd.getMaskedImage()
        scaledMaskedImage = coaddMaskedImage.__class__(coaddMaskedImage, True)

        # set the edge pixels
        utilsLib.setCoaddEdgeBits(scaledMaskedImage.getMask(), self._weightMap)
        
        # scale non-edge pixels by weight map
        scaledMaskedImage /= self._weightMap
        
        return afwImage.makeExposure(scaledMaskedImage, self._wcs)
    
    def getBadPixelMask(self):
        """Return the bad pixel mask
        """
        return self._badPixelMask

    def getBBox(self):
        """Return the bounding box of the coadd
        """
        return self._bbox

    def getWcs(self):
        """Return the wcs of the coadd
        """
        return self._wcs
        
    def getWeightMap(self):
        """Get the weight map
        
        The weight map is a float Image of the same dimensions as the coadd;
        the value of each pixel is the number of input images
        that contributed to the associated pixel of the coadd.
        """
        return self._weightMap
