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
import numpy
import lsst.afw.image as afwImage
import lsst.pex.config as pexConfig
import lsst.pipe.base as pipeBase
import lsst.afw.math as afwMath
import lsst.afw.geom as afwGeom
 
from lsst.obs.sdss.selectSdssImages import SelectSdssfluxMag0Task
__all__ = ["ScaleZeroPointTask"]


class MultiplicativeScaleFactor():
    def __init__(self, *args, **kwargs):
        """Construct a multiplicative scale factor. It consists of  a list of points in tract coordinates. 
           Each point has an X, Y, and a scalefactor.
        """
        self.xList = []
        self.yList = []
        self.scaleList = []
        #self.scaleErrList = []

    def getInterpImage(self, bbox):
        """Return an image interpolated in R.A direction covering supplied bounding box
        
         Hard-coded to work with obs_sdss only
        """
        npoints = len(self.xList)
        xvec = afwMath.vectorF(self.xList)
        zvec = afwMath.vectorF(self.scaleList)      
        height = bbox.getHeight()
        width = bbox.getWidth()
        x0, y0 = bbox.getBegin()

        # I can't get makeInterpolate to work "Message: gsl_interp_init failed: invalid argument supplied by user [4]"
        # interp = afwMath.makeInterpolate(xvec, zvec, afwMath.Interpolate.LINEAR)
        # interp = afwMath.makeInterpolate(xvec, zvec) won't initialize spline. 
        # eval = interp.interpolate(range(y0, height))
        
        eval = numpy.interp(range(x0, x0 + width), xvec, zvec)
        
        evalGrid, _ =   numpy.meshgrid(eval.astype(numpy.float32),range(0, height))
        image = afwImage.makeImageFromArray(evalGrid)
        image.setXY0(x0, y0)
        return image
     


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
        
        self.selectFluxMag0 = SelectSdssfluxMag0Task()
        
    def getCalib(self):
        """Get desired Calib
        
        @return calibration (lsst.afw.image.Calib) with fluxMag0 set appropriately for config.zeroPoint
        """
        return self._calib

    def fluxMag0ToScale(self, fluxMag0):
        """Comput the scale for the specified fluxMag0

        @param fluxMag0 
        @return float 
        """
        calib = afwImage.Calib()
        calib.setFluxMag0(fluxMag0)
        return self.computeScale(calib).scale

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
    
    def getScaleFromDb(self, patchRef, wcs, bbox):
        """
        Query a database for fluxMag0s and return a MultiplicativeScaleFactor

        First, double the width (R.A. direction) of the patch bounding box. Query the database for
        overlapping fluxMag0s corresponding to the same run and filter.
        
        """
        scaleFactor = MultiplicativeScaleFactor()
        buffer = bbox.getWidth()//2
        biggerBbox = afwGeom.Box2I(afwGeom.Point2I(bbox.getBeginX()-buffer, bbox.getBeginY()),
                                   afwGeom.Extent2I(bbox.getWidth()+buffer, bbox.getHeight()))
        cornerPosList = afwGeom.Box2D(biggerBbox).getCorners()
        coordList = [wcs.pixelToSky(pos) for pos in cornerPosList]
        runArgDict = self.selectFluxMag0._runArgDictFromDataId(patchRef.dataId)
        fluxMagInfoList = self.selectFluxMag0.run(coordList, **runArgDict).fluxMagInfoList

        for fluxMagInfo in fluxMagInfoList:
            print fluxMagInfo.dataId, self.fluxMag0ToScale(fluxMagInfo.fluxMag0)
            raCenter = (fluxMagInfo.coordList[0].getRa() +  fluxMagInfo.coordList[1].getRa() +
                        fluxMagInfo.coordList[2].getRa() +  fluxMagInfo.coordList[3].getRa())/ 4.
            decCenter = (fluxMagInfo.coordList[0].getDec() +  fluxMagInfo.coordList[1].getDec() +
                        fluxMagInfo.coordList[2].getDec() +  fluxMagInfo.coordList[3].getDec())/ 4.
            x, y = wcs.skyToPixel(raCenter,decCenter)
            scaleFactor.xList.append(x)
            scaleFactor.yList.append(y)          
            scaleFactor.scaleList.append(self.fluxMag0ToScale(fluxMagInfo.fluxMag0))
            #self.scaleFactor.scaleErrList.append(self.fluxMag0ToScale(fluxMagInfo.fluxMag0Sigma))
        return scaleFactor
