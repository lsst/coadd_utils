#!/usr/bin/env python
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
# GNU General Public License for more details.
#
# You should have received a copy of the LSST License Statement and
# the GNU General Public License along with this program.  If not,
# see <http://www.lsstcorp.org/LegalNotices/>.
#


import lsst.pex.config as pexConfig
import lsst.pipe.base as pipeBase
from lsst.pipe.tasks.selectImages import SelectImagesConfig, BaseExposureInfo

__all__ = ["BaseSelectFluxMag0Task"]

class SelectFluxMag0Config(SelectImagesConfig):
    table = pexConfig.Field(
        doc = "Name of database table",
        dtype = str,
    )

class BaseFluxMagInfo(BaseExposureInfo):
    """Create exposure information from a query result from a db connection

    Data includes:
    - dataId: data ID of exposure (a dict)
    - coordList: a list of corner coordinates of the exposure (list of IcrsCoord)
    - fluxMag0: float 
    - fluxMag0Sigma: float

    Subclasses must provide an __init__  and override getColumnNames.
    """

    def __init__(self, result):
        """Set exposure information based on a query result from a db connection
        Override this in the obs_XXX package.
        """
        BaseExposureInfo.__init__(self)


    @staticmethod
    def getColumnNames():
        """Get database columns to retrieve, in a format useful to the database interface

        @return database column names as list of strings
        Override in obs_XXX package. See obs_lsstSim for example.
        """
        raise NotImplementedError()


class BaseSelectFluxMag0Task(pipeBase.Task):
    """
    """
    ConfigClass = SelectFluxMag0Config

    @pipeBase.timeMethod
    def run(self, visit):
        """Select flugMag0's of LsstSim images for a particular visit

        @param[in] visit: visit id

        @return a pipeBase Struct containing:
        - fluxMagInfoList: a list of FluxMagInfo objects
        """
        raise NotImplementedError()

    def runArgDictFromDataId(self, dataId):
        """Extract keyword arguments for visit (other than coordList) from a data ID

        @param[in] dataId: a data ID dict
        @return keyword arguments for visit (other than coordList), as a dict
        """
        raise NotImplementedError()
