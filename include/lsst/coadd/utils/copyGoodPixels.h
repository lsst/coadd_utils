// -*- LSST-C++ -*-

/* 
 * LSST Data Management System
 * Copyright 2008, 2009, 2010 LSST Corporation.
 * 
 * This product includes software developed by the
 * LSST Project (http://www.lsst.org/).
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 * 
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the LSST License Statement and 
 * the GNU General Public License along with this program.  If not, 
 * see <http://www.lsstcorp.org/LegalNotices/>.
 */
 
#ifndef LSST_COADD_UTILS_ADDTOCOADD_H
#define LSST_COADD_UTILS_ADDTOCOADD_H
/**
* @file
*
* @author Russell Owen
*/
#include "boost/cstdint.hpp"

#include "lsst/afw/geom.h"
#include "lsst/afw/image.h"

namespace lsst {
namespace coadd {
namespace utils {

    /**
    * @brief copy good pixels from one image to another
    *
    * Good pixels are those that are not NaN (thus they do include +/- inf).
    *
    * Only the overlapping pixels (relative to the parent) are copied;
    * thus the images do not have to be the same size.
    *
    * @return number of pixels copied
    */
    template<typename ImagePixelT>
    int copyGoodPixels(
        lsst::afw::image::Image<ImagePixelT> &destImage,        ///< [in,out] image to be modified
        lsst::afw::image::Image<ImagePixelT> const &srcImage    ///< image to copy
    );

    /**
    * @brief copy good pixels from one masked image to another
    *
    * Good pixels are those for which mask & badPixelMask == 0.
    *
    * Only the overlapping pixels (relative to the parent) are copied;
    * thus the images do not have to be the same size.
    *
    * @return number of pixels copied
    */
    template<typename ImagePixelT>
    int copyGoodPixels(
        lsst::afw::image::MaskedImage<ImagePixelT, lsst::afw::image::MaskPixel,
            lsst::afw::image::VariancePixel> &destImage,        ///< [in,out] image to be modified
        lsst::afw::image::MaskedImage<ImagePixelT, lsst::afw::image::MaskPixel,
            lsst::afw::image::VariancePixel> const &srcImage, ///< image to copy
        lsst::afw::image::MaskPixel const badPixelMask ///< skip input pixel if src mask & badPixelMask != 0
    );

}}} // lsst::coadd::utils

#endif // !defined(LSST_COADD_UTILS_ADDTOCOADD_H)
