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
import lsst.afw.geom as afwGeom
import lsst.afw.image as afwImage

__all__ = ["bboxFromImage", "imageFromBBox", "makeBlankExposure"]
    
def bboxFromImage(image):
    """Return a bounding box for an Image, MaskedImage or Exposure
    
    @param[in] image an afw Image, MaskedImage or Exposure;
        (must support getX(), getY(), getWidth(), getHeight())

    @return bounding box (lsst.afw.geom.BoxI):
        bbox dimensions = image dimensions; bbox minimum = image xy0
    """
    return afwGeom.BoxI(afwGeom.makePointI(image.getX0(), image.getY0()),
        afwGeom.makeExtentI(image.getWidth(), image.getHeight()))

def imageFromBBox(bbox, imageFactory):
    """Return an image-like object with the specified bounding box relative to its parent image
    
    Can construct an Image, MaskedImage, Mask, Exposure or similar object
    that can be constructed from (width, eight) and supports setXY0.
    
    @param[in] bbox bounding box of image with respect to parent (lsst.afw.geom.BoxI):
        image dimensions = bbox dimensions; image xy0 = bbox min position
    @param[in] imageFactory factory for desired image-like object, e.g. image.Factory.
        May also be a type, but type(image) but that does not work for butler-unpersisted data.
    """
    image = imageFactory(bbox.getWidth(), bbox.getHeight())
    image.setXY0(bbox.getMinX(), bbox.getMinY())
    return image

def makeBlankExposure(fromExposure):
    """Return a blank exposure with the same size, xy0, WCS and type as fromExposure

    @param[in] exposure exposure to match
    
    @return blank exposure whose dimensions, xy0 and WCS match fromExposure
    """
    maskedImage = fromExposure.getMaskedImage()
    blankMaskedImage = maskedImage.Factory(maskedImage.getDimensions())
    blankMaskedImage.set((0,0,0))
    blankMaskedImage.setXY0(maskedImage.getDimensions())
    return afwImage.makeExposure(blankMaskedImage, fromExposure.getWcs())
