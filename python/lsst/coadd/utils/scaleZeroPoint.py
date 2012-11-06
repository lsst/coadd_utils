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

__all__ = ["ScaleZeroPointTask"]

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
    A fancier version will likely be wanted for cameras with large fields of view.
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
    
    def getCalib(self):
        """Get desired Calib
        
        @return calibration (lsst.afw.image.Calib) with fluxMag0 set appropriately for config.zeroPoint
        """
        return self._calib
    
    def computeScale(self, calib):
        """Compute the scale for the specified Calib
        
        Compute the scale such that:
            scale = computeScale(exposure.getCalib())
            mi = exposure.getMaskedImage()
            mi *= scale
        will scale the exposure to the desired photometric zeropoint

        In this case the scale is a scalar, but it may be some sort of spatially varying function
        for variants of this task.
        
        @return a pipeBase.Struct containing:
        - scale, as described above.
        """
        fluxAtZeroPoint = calib.getFlux(self.config.zeroPoint)
        return pipeBase.Struct(
            scale = 1.0 / fluxAtZeroPoint,
        )
