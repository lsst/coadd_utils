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

"""Utilities for coadd generation
"""
import math

import numpy

import lsst.daf.base as dafBase
import lsst.afw.image as afwImage

__all__ = ["makeBlankCoadd", "makeBlankExposure"]

def makeBlankCoadd(fromExposure, resolutionFactor, coaddClass=afwImage.ExposureF):
    """Generate a blank coadd Exposure based on a given Exposure
    
    Inputs:
    - fromExposure: the exposure on which to base the coadd
    - resolutionFactor: relative linear resolution (x or y) of returned Exposure compared to fromExposure
    
    Returned:
    - coaddExposure: a blank Exposure with:
        - resolutionFactor^2 times as many pixels as fromExposure
        - The same center sky position as fromExposure
        - tangent-plane projection
        - North up, east to the right
    
    Note that the amount of overlap between the returned coadd exposure and fromExposure will vary significantly
    based on how fromExposure is rotated.
    
    @todo: check coordinate system of fromExposure or match it in the coadd
    
    Warning:
    - fromExposure must use FK5 J2000 coordinates for its WCS. This is NOT yet checked.
    """
    fromShape = numpy.array(fromExposure.getMaskedImage().getDimensions())
    coaddShape = numpy.round(fromShape * resolutionFactor).astype(int)
    
    # make tangent-plane projection WCS for the coadd
    fromWcs = fromExposure.getWcs()
    fromCtr = (fromShape - 1) / 2.0
    fromCtrPt = afwImage.PointD(*fromCtr)
    raDecCtr = numpy.array(fromWcs.xyToRaDec(fromCtrPt))
    coaddDegPerPix = math.sqrt(fromWcs.pixArea(fromCtrPt)) / float(resolutionFactor)
    
    coaddMetadata = dafBase.PropertySet()
    coaddMetadata.add("EPOCH", 2000.0)
    coaddMetadata.add("EQUINOX", 2000.0)
    coaddMetadata.add("RADECSYS", "FK5")
    coaddMetadata.add("CTYPE1", "RA---TAN")
    coaddMetadata.add("CTYPE2", "DEC--TAN")
    coaddMetadata.add("CRPIX1", coaddShape[0]/2.0)
    coaddMetadata.add("CRPIX2", coaddShape[1]/2.0)
    coaddMetadata.add("CRVAL1", raDecCtr[0])
    coaddMetadata.add("CRVAL2", raDecCtr[1])
    coaddMetadata.add("CD1_1", coaddDegPerPix)
    coaddMetadata.add("CD1_2", 0.0)
    coaddMetadata.add("CD2_1", 0.0)
    coaddMetadata.add("CD2_2", coaddDegPerPix)
    coaddWcs = afwImage.Wcs(coaddMetadata)
    coaddExposure = coaddClass(coaddShape[0], coaddShape[1], coaddWcs)
    return coaddExposure

def makeBlankExposure(fromExposure):
    """Return a blank exposure with the same size and WCS as fromExposure
    """
    maskedImage = fromExposure.getMaskedImage()
    blankMaskedImage = maskedImage.Factory(maskedImage.getDimensions())
    blankMaskedImage.set((0,0,0))
    return afwImage.makeExposure(blankMaskedImage, fromExposure.getWcs())

