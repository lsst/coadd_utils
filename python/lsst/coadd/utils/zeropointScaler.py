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

__all__ = ["ZeropointScaler"]

class ZeropointScaler(object):
    """Scale exposures to a desired photometric zeropoint
    """
    def __init__(self, zeropoint):
        """Construct a zeropoint scaler
        
        @param[in] zeropoint: desired photometric zero point (mag)
        """
        self._zeropoint = float(zeropoint)

        fluxMag0 = 10**(0.4 * self._zeropoint)
        self._calib = afwImage.Calib()
        self._calib.setFluxMag0(fluxMag0)
        if abs(self._calib.getMagnitude(1.0) - self._zeropoint) > 1.0e-4:
            raise RuntimeError("Bug: calib.getMagnitude(1.0) = %0.4f != %0.4f = coaddZeroPoint" % \
                (self._calib.getMagnitude(1.0), self._zeropoint))
    
    def getCalib(self):
        """Get desired calibration
        
        @return desired calibration (afwImage.Calib)
        """
        return self._calib
    
    def scaleExposure(self, exposure):
        """Scale exposure to the desired photometric zeropoint, in place
        
        @param[in,out] exposure: exposure to scale; it must have a valid Calib;
            the pixel values and Calib zeropoint are scaled
        @return scaleFac: scale factor, where new image values = original image values * scaleFac
        """
        exposureCalib = exposure.getCalib()
        exposureFluxMag0Sigma = exposureCalib.getFluxMag0()[1]
        fluxAtZeropoint = exposureCalib.getFlux(self._zeropoint)
        scaleFac = 1.0 / fluxAtZeropoint
        maskedImage = exposure.getMaskedImage()
        maskedImage *= scaleFac
        exposureFluxMag0Sigma *= scaleFac
        exposureCalib.setFluxMag0(self.getCalib().getFluxMag0()[0], exposureFluxMag0Sigma)
        
        return scaleFac
