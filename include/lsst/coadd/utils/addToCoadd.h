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
 
#ifndef LSST_COADD_UTILS_COPYGOODPIXELS_H
#define LSST_COADD_UTILS_COPYGOODPIXELS_H
/**
* @file
*
* @author Russell Owen
*/
#include "boost/cstdint.hpp"

#include "lsst/afw/geom/Box.h"
#include "lsst/afw/image/Image.h"
#include "lsst/afw/image/MaskedImage.h"

namespace lsst {
namespace coadd {
namespace utils {

    /**
    * @brief add good pixels from an image to a coadd and associated weight map
    *
    * The images are assumed to be registered to the same wcs and parent origin, thus:
    * coadd[i+coadd.x0, j+coadd.y0] += image[i+image.x0, j+image.y0]
    * weightMap[i+weightMap.x0, j+weightMap.y0] += weight
    * for all good image pixels that overlap a coadd pixel.
    * Good pixels are those that are not NaN (thus they do include +/- inf).
    *
    * @return overlapBBox: overlapping bounding box, relative to parent image (hence xy0 is taken into account)
    *
    * @throw pexExcept::InvalidParameterException if coadd and weightMap dimensions or xy0 do not match.
    */
    template<typename CoaddPixelT, typename WeightPixelT>
    lsst::afw::geom::Box2I addToCoadd(
        lsst::afw::image::Image<CoaddPixelT> &coadd,        ///< [in,out] coadd to be modified
        lsst::afw::image::Image<WeightPixelT> &weightMap,   ///< [in,out] weight map to be modified;
            ///< this is the sum of weights of all images contributing each pixel of the coadd
        lsst::afw::image::Image<CoaddPixelT> const &image,  ///< image to add to coadd
        WeightPixelT weight                                 ///< relative weight of this image
    );

    /**
    * @brief add good pixels from a masked image to a coadd image and associated weight map
    *
    * The images are assumed to be registered to the same wcs and parent origin, thus:
    * coadd[i+coadd.x0, j+coadd.y0] += image[i+image.x0, j+image.y0]
    * weightMap[i+weightMap.x0, j+weightMap.y0] += weight
    * for all good image pixels that overlap a coadd pixel.
    * Good pixels are those for which mask & badPixelMask == 0.
    *
    * @return overlapBBox: overlapping bounding box, relative to parent image (hence xy0 is taken into account)
    *
    * @throw pexExcept::InvalidParameterException if coadd and weightMap dimensions or xy0 do not match.
    */
    template<typename CoaddPixelT, typename WeightPixelT>
    lsst::afw::geom::Box2I addToCoadd(
        lsst::afw::image::MaskedImage<CoaddPixelT, lsst::afw::image::MaskPixel,
            lsst::afw::image::VariancePixel> &coadd,        ///< [in,out] coadd to be modified
        lsst::afw::image::Image<WeightPixelT> &weightMap,   ///< [in,out] weight map to be modified;
            ///< this is the sum of weights of all images contributing each pixel of the coadd
        lsst::afw::image::MaskedImage<CoaddPixelT, lsst::afw::image::MaskPixel,
            lsst::afw::image::VariancePixel> const &maskedImage, ///< masked image to add to coadd
        lsst::afw::image::MaskPixel const badPixelMask, ///< skip input pixel if input mask & badPixelMask !=0
        WeightPixelT weight                             ///< relative weight of this image
    );

}}} // lsst::coadd::utils

#endif // !defined(LSST_COADD_UTILS_COPYGOODPIXELS_H)
