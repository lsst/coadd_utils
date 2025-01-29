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

"""Module hosting utilities in Python for coaddition."""


from __future__ import annotations

__all__ = (
    "removeMaskPlanes",
    "setRejectedMaskMapping",
)

from collections.abc import Iterable
from typing import TYPE_CHECKING

import lsst.afw.image as afwImage
from lsst.pex.exceptions import InvalidParameterError

if TYPE_CHECKING:
    from logging import Logger

    from lsst.afw.math import StatisticsControl


def removeMaskPlanes(
    mask: afwImage.Mask, mask_planes: Iterable, logger: Logger | None = None
):
    """Unset the mask of an image for mask planes specified in the config.

    Parameters
    ----------
    mask : `lsst.afw.image.Mask`
        The mask to be modified.
    mask_planes : `list`
        The list of mask planes to be removed.
    logger : `logging.Logger`, optional
        Logger to log messages.
    """
    for maskPlane in mask_planes:
        try:
            mask &= ~mask.getPlaneBitMask(maskPlane)
        except InvalidParameterError:
            if logger:
                logger.warn(
                    "Unable to remove mask plane %s: no mask plane with that name was found.",
                    maskPlane,
                )


def setRejectedMaskMapping(statsCtrl: StatisticsControl) -> list[tuple[int, int]]:
    """Map certain mask planes of the warps to new planes for the coadd.

    If a pixel is rejected due to a mask value other than EDGE, NO_DATA,
    or CLIPPED, set it to REJECTED on the coadd.
    If a pixel is rejected due to EDGE, set the coadd pixel to SENSOR_EDGE.
    If a pixel is rejected due to CLIPPED, set the coadd pixel to CLIPPED.

    Parameters
    ----------
    statsCtrl : `lsst.afw.math.StatisticsControl`
        Statistics control object for coadd.

    Returns
    -------
    maskMap : `list` of `tuple` of `int`
        A list of mappings of mask planes of the warped exposures to
        mask planes of the coadd.
    """
    edge = afwImage.Mask.getPlaneBitMask("EDGE")
    noData = afwImage.Mask.getPlaneBitMask("NO_DATA")
    clipped = 2 ** afwImage.Mask.addMaskPlane("CLIPPED")
    toReject = statsCtrl.getAndMask() & (~noData) & (~edge) & (~clipped)
    maskMap = [
        (toReject, 2 ** afwImage.Mask.addMaskPlane("REJECTED")),
        (edge, 2 ** afwImage.Mask.addMaskPlane("SENSOR_EDGE")),
        (clipped, clipped),
    ]
    return maskMap
