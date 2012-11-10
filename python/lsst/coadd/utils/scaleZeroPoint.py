# 
# LSST Data Management System
# Copyright 2008, 2009, 2010, 2011, 2012 LSST Corporation.
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
import lsst.afw.image as afwImage
import lsst.pex.config as pexConfig
import lsst.pipe.base as pipeBase
 
__all__ = ["ImageScaler", "ScaleZeroPointTask"]


class ImageScaler(object):
    """A class that scales an image
    
    This version uses a single scalar. Fancier versions may use a spatially varying scale.
    """
    def __init__(self, scale):
        self._scale = float(scale)

    def scaleMaskedImage(self, maskedImage):
        """Apply scale correction to the specified masked image
        
        @param[in,out] image to scale; scale is applied in place
        """
        maskedImage *= self._scale


class ScaleZeroPointConfig(pexConfig.Config):
    """Config for ScaleZeroPointTask
    """
    zeroPoint = pexConfig.Field(
        dtype = float,
        doc = "desired photometric zero point",
        default = 27.0,
    )


class ScaleZeroPointTask(pipeBase.Task):
    """Compute scale factor to scale exposures to a desired photometric zero point
    
    This simple version assumes that the zero point is spatially invariant.
    Fancier versions will likely be wanted for cameras with large fields of view.
    Such fancier versions will probably only need to override computeImageScaler.
    """
    ConfigClass = ScaleZeroPointConfig
    _DefaultName = "scaleZeroPoint"

    def __init__(self, *args, **kwargs):
        """Construct a ScaleZeroPointTask
        """
        pipeBase.Task.__init__(self, *args, **kwargs)

        fluxMag0 = 10**(0.4 * self.config.zeroPoint)
        self._calib = afwImage.Calib()
        self._calib.setFluxMag0(fluxMag0)
    
    def run(self, exposure, exposureId):
        """Scale the specified exposure to the desired photometric zeropoint
        
        @param[in,out] exposure: exposure to scale; masked image is scaled in place
        @param[in] exposureId: data ID for exposure
        
        @return a pipeBase.Struct containing:
        - imageScaler: the image scaling object used to scale exposure
        """
        imageScaler = self.computeImageScaler(exposure = exposure, exposureId = exposureId)
        mi = exposure.getMaskedImage()
        imageScaler.scaleMaskedImage(mi)
        return pipeBase.Struct(
            imageScaler = imageScaler,
        )
    
    def computeImageScaler(self, exposure, exposureId):
        """Compute image scaling object for a given exposure
        
        param[in] exposure: exposure for which scaling is desired
        param[in] exposureId: data ID for exposure; ignored in this simple version
        
        @note This implementation only reads exposure.getCalib() and ignores exposureId. Fancier versions may
        use exposureId and more data from exposure to determine spatial variation in photometric zeropoint.
        """
        scale = self.computeScale(exposure.getCalib()).scale
        return ImageScaler(scale)
        
    def getCalib(self):
        """Get desired Calib
        
        @return calibration (lsst.afw.image.Calib) with fluxMag0 set appropriately for config.zeroPoint
        """
        return self._calib

    def scaleFromFluxMag0(self, fluxMag0):
        """Compute the scale for the specified fluxMag0
        
        This is a wrapper around scaleFromCalib, which see for more information

        @param[in] fluxMag0
        @return a pipeBase.Struct containing:
        - scale, as described in scaleFromCalib.
        """
        calib = afwImage.Calib()
        calib.setFluxMag0(fluxMag0)
        return self.computeScale(calib)

    def scaleFromCalib(self, calib):
        """Compute the scale for the specified Calib
        
        Compute scale, such that if pixelCalib describes the photometric zeropoint of a pixel
        then the following scales that pixel to the photometric zeropoint specified by config.zeroPoint:
            scale = computeScale(pixelCalib)
            pixel *= scale
        
        @return a pipeBase.Struct containing:
        - scale, as described above.
        
        @note: returns a struct to leave room for scaleErr in a future implementation.
        """
        fluxAtZeroPoint = calib.getFlux(self.config.zeroPoint)
        return pipeBase.Struct(
            scale = 1.0 / fluxAtZeroPoint,
        )
