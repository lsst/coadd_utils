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

/**
* @file
*
* @author Russell Owen
*/
#include <cstdint>
#include <limits>

#include "boost/format.hpp"

#include "lsst/pex/exceptions.h"
#include "lsst/afw/geom.h"
#include "lsst/coadd/utils/copyGoodPixels.h"

namespace pexExcept = lsst::pex::exceptions;
namespace afwGeom = lsst::afw::geom;
namespace afwImage = lsst::afw::image;
namespace coaddUtils = lsst::coadd::utils;

namespace {
    /*
     * A boolean functor to test if a MaskedImage pixel is valid (mask & badPixel == 0)
     */
    struct CheckMask {
        CheckMask(lsst::afw::image::MaskPixel badPixel) : _badPixel(badPixel) {}

        template<typename T>
        bool operator()(T val) const {
            return ((val.mask() & _badPixel) == 0) ? true : false;
        }
    private:
        lsst::afw::image::MaskPixel _badPixel;
    };

    /*
     * A boolean functor to test if an Image pixel has known value (not NaN)
     */
    struct CheckKnownValue {
        CheckKnownValue(lsst::afw::image::MaskPixel) {}

        template<typename T>
        bool operator()(T val) const {
            return !std::isnan(static_cast<float>(*val));
        }
    };

    /*
     * Implementation of copyGoodPixels
     *
     * The template parameter isValidPixel is a functor with operator()
     * which returns true if a given image pixel is valid.
     * This allows us to support multiple image types including
     * MaskedImage with a mask bit and Image with a check for NaN.
     *
     * @return overlapping bounding box, relative to parent image
     */
    template <typename ImageT, typename isValidPixel>
    int copyGoodPixelsImpl(
        ImageT &destImage,                                  ///< [in,out] image to modify
        ImageT const &srcImage,                             ///< image to copy
        lsst::afw::image::MaskPixel const badPixelMask      ///< bad pixel mask; may be ignored
    ) {
        afwGeom::Box2I overlapBBox = destImage.getBBox();
        overlapBBox.clip(srcImage.getBBox());
        if (overlapBBox.isEmpty()) {
            return 0;
        }

        ImageT destView(destImage, overlapBBox, afwImage::PARENT, false);
        ImageT srcView(srcImage, overlapBBox, afwImage::PARENT, false);

        isValidPixel const isValid(badPixelMask); // functor to check if a pixel is good
        int numGoodPix = 0;
        for (int y = 0, endY = srcView.getHeight(); y != endY; ++y) {
            typename ImageT::const_x_iterator srcIter = srcView.row_begin(y);
            typename ImageT::const_x_iterator const srcEndIter = srcView.row_end(y);
            typename ImageT::x_iterator destIter = destView.row_begin(y);
            for (; srcIter != srcEndIter; ++srcIter, ++destIter) {
                if (isValid(srcIter)) {
                    *destIter = *srcIter;
//                     typename ImageT::SinglePixel pix = *srcIter;
//                     *destIter = pix;
                    ++numGoodPix;
                }
            }
        }
        return numGoodPix;
    }
} // anonymous namespace

template <typename ImagePixelT>
int coaddUtils::copyGoodPixels(
    // spell out lsst:afw::image to make Doxygen happy
    lsst::afw::image::Image<ImagePixelT> &destImage,
    lsst::afw::image::Image<ImagePixelT> const &srcImage
) {
    typedef lsst::afw::image::Image<ImagePixelT> Image;
    return copyGoodPixelsImpl<Image, CheckKnownValue>(destImage, srcImage, 0x0);
}

template <typename ImagePixelT>
int coaddUtils::copyGoodPixels(
    // spell out lsst:afw::image to make Doxygen happy
    lsst::afw::image::MaskedImage<ImagePixelT, lsst::afw::image::MaskPixel,
        lsst::afw::image::VariancePixel> &destImage,
    lsst::afw::image::MaskedImage<ImagePixelT, lsst::afw::image::MaskPixel,
        lsst::afw::image::VariancePixel> const &srcImage,
    lsst::afw::image::MaskPixel const badPixelMask
) {
    typedef lsst::afw::image::MaskedImage<ImagePixelT> Image;
    return copyGoodPixelsImpl<Image, CheckMask>(destImage, srcImage, badPixelMask);
}

// Explicit instantiations

/// \cond
#define MASKEDIMAGE(IMAGEPIXEL) afwImage::MaskedImage<IMAGEPIXEL, \
    afwImage::MaskPixel, afwImage::VariancePixel>
#define INSTANTIATE(IMAGEPIXEL) \
    template int coaddUtils::copyGoodPixels<IMAGEPIXEL>( \
        afwImage::Image<IMAGEPIXEL> &destImage, \
        afwImage::Image<IMAGEPIXEL> const &srcImage       \
    ); \
    \
    template int coaddUtils::copyGoodPixels<IMAGEPIXEL>( \
        MASKEDIMAGE(IMAGEPIXEL) &destImage, \
        MASKEDIMAGE(IMAGEPIXEL) const &srcImage, \
        afwImage::MaskPixel const badPixelMask \
    );

INSTANTIATE(double);
INSTANTIATE(float);
INSTANTIATE(int);
INSTANTIATE(std::uint16_t);
/// \endcond
