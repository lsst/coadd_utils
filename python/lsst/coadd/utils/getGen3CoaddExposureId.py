# This file is part of coadd_utils.
#
# Developed for the LSST Data Management System.
# This product includes software developed by the LSST Project
# (https://www.lsst.org).
# See the COPYRIGHT file at the top-level directory of this distribution
# for details of code ownership.
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
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

__all__ = ["getGen3CoaddExposureId"]

from lsst.daf.persistence import NoResults


def getGen3CoaddExposureId(dataRef, coaddName="deep", includeBand=True, log=None):
    """Return the coadd expId consistent with Gen3 implementation.

    This is a temporary interface intended to aid with the migration from
    Gen2 to Gen3 middleware.  It will be removed with the Gen2 middleware.

    Parameters
    ----------
    dataRef : `lsst.daf.persistence.butlerSubset.ButlerDataRef`
        The data reference for the patch.
    coaddName : `str`, optional
        The prefix for the coadd name, e.g. "deep" for "deepCoadd"
    includeBand : `bool`, optional
        Whether to include band as part of the dataId packing.
    log : `lsst.log.Log` or `None`, optional
        Logger object for logging messages.

    Returns
    -------
    expId : `int`
        The integer id associated with `patchRef` that mimics that of Gen3.
    """
    tract = dataRef.dataId["tract"]
    patch = dataRef.dataId["patch"]
    filter = dataRef.dataId["filter"]
    skyMap = dataRef.get(coaddName + "Coadd_skyMap")
    tractInfo = skyMap[tract]
    if includeBand:
        try:
            band = dataRef.get(coaddName + "Coadd_band")
            if log is not None:
                camera = dataRef.get("camera")
                log.info("Filter %s has been assigned %s as the associated generic band for expId "
                         "computation.", filter, band)
        except NoResults:
            band = filter
            if log is not None:
                camera = dataRef.get("camera")
                log.info("No %s mapping found for %s.  Using filter %s in dataId as band",
                         coaddName + "Coadd_band", camera.getName(), band)
    else:
        band = None

    # Note: the function skyMap.pack_data_id() requires Gen3-style
    # dataId entries, namely the generic "band" rather than the
    # "physical_filter", and the sequential patch id number rather
    # than the comma separated string version.
    for patchInfo in tractInfo:
        patchIndexStr = str(patchInfo.getIndex()[0]) + "," + str(patchInfo.getIndex()[1])
        if patchIndexStr == patch:
            patchNumId = tractInfo.getSequentialPatchIndex(patchInfo)
            break
    try:
        expId, maxBits = skyMap.pack_data_id(tract, patchNumId, band=band)
    except Exception as e:
        if log is not None:
            log.warning("Setting exposureId to match Gen3 failed with: %s.  Falling back to "
                        "Gen2 implementation.", e)
        expId = int(dataRef.get(coaddName + "CoaddId"))
    return expId
