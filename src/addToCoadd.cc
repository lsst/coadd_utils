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
#include <limits>

#include "boost/format.hpp"

#include "lsst/pex/exceptions.h"
#include "lsst/coadd/utils/addToCoadd.h"

namespace pexExcept = lsst::pex::exceptions;
namespace afwImage = lsst::afw::image;
namespace coaddUtils = lsst::coadd::utils;

namespace {
/*
 * We're going to use a function, addToCoaddImpl, which is templated on a functor with an operator() used
 * to check if a given pixel is valid.  This allows us to implement addToCoadd for a number of combinations
 * of inputs (e.g. MaskedImage with a mask bit;  Image with a check for NaN)
 */
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

template <typename CoaddT, typename WeightPixelT, typename isValidPixel>
static void addToCoaddImpl(
    CoaddT &coadd,                                    // [in,out] coadd to be modified
    lsst::afw::image::Image<WeightPixelT> &weightMap, // [in,out] weight map to be modified
    CoaddT const &maskedImage,                        // masked image to add to coadd
    lsst::afw::image::MaskPixel const badPixelMask,   // bad pixel mask; may be ignored
    WeightPixelT weight                               // relative weight of this image
) {
    typedef typename afwImage::Image<WeightPixelT> WeightMapT;
    
    if (coadd.getDimensions() != maskedImage.getDimensions()) {
        throw LSST_EXCEPT(pexExcept::InvalidParameterException,
            (boost::format("coadd and maskedImage dimensions differ: %dx%d != %dx%d") %
            coadd.getWidth() % coadd.getHeight() % maskedImage.getWidth() % maskedImage.getHeight()).str());
    }
    if (coadd.getDimensions() != weightMap.getDimensions()) {
        throw LSST_EXCEPT(pexExcept::InvalidParameterException,
            (boost::format("coadd and weightMap dimensions differ: %dx%d != %dx%d") %
            coadd.getWidth() % coadd.getHeight() % weightMap.getWidth() % weightMap.getHeight()).str());
    }

    // Set the pixels row by row, to avoid repeated checks for end-of-row
    isValidPixel const isValid(badPixelMask); // functor to check if a pixel is good
    for (int y = 0, endY = maskedImage.getHeight(); y != endY; ++y) {
        typename CoaddT::const_x_iterator maskedImageIter = maskedImage.row_begin(y);
        typename CoaddT::const_x_iterator const maskedImageEndIter = maskedImage.row_end(y);
        typename CoaddT::x_iterator coaddIter = coadd.row_begin(y);
        typename WeightMapT::x_iterator weightMapIter = weightMap.row_begin(y);
        for (; maskedImageIter != maskedImageEndIter; ++maskedImageIter, ++coaddIter, ++weightMapIter) {
            if (isValid(maskedImageIter)) {
                typename CoaddT::SinglePixel pix = *maskedImageIter;
                pix *= typename CoaddT::Pixel(weight);
                *coaddIter += pix;
                *weightMapIter += weight;
            }
        }
    }
}
} // anonymous namespace

/**
* @brief add good pixels from an image to a coadd and associated weight map
*
* Good pixels are those for which mask & badPixelMask == 0.
*
* @throw pexExcept::InvalidParameterException if coadd, weightMap and maskedImage dimensions do not match.
*/
template <typename CoaddPixelT, typename WeightPixelT>
void coaddUtils::addToCoadd(
    // spell out lsst:afw::image to make Doxygen happy
    lsst::afw::image::MaskedImage<CoaddPixelT, lsst::afw::image::MaskPixel,
        lsst::afw::image::VariancePixel> &coadd,        ///< [in,out] coadd to be modified
    lsst::afw::image::Image<WeightPixelT> &weightMap,   ///< [in,out] weight map to be modified;
        ///< this is the sum of weights of all images contributing each pixel of the coadd
    lsst::afw::image::MaskedImage<CoaddPixelT, lsst::afw::image::MaskPixel,
        lsst::afw::image::VariancePixel> const &maskedImage, ///< masked image to add to coadd
    lsst::afw::image::MaskPixel const badPixelMask, ///< skip input pixel if input mask | badPixelMask != 0
    WeightPixelT weight                             ///< relative weight of this image
) {
    typedef lsst::afw::image::MaskedImage<CoaddPixelT> Image;
    addToCoaddImpl<Image, WeightPixelT, CheckMask>(coadd, weightMap, maskedImage, badPixelMask, weight);
}

/**
* @brief add good pixels from an image to a coadd and associated weight map
*
* Good pixels are those that are not NaN (thus they do include +/- inf).
*
* Weight map: sum of weights of all images in the coadd at each pixel of the coadd.
*
* @throw pexExcept::InvalidParameterException if coadd, weightMap and image dimensions do not match.
*/
template <typename CoaddPixelT, typename WeightPixelT>
void coaddUtils::addToCoadd(
    // spell out lsst:afw::image to make Doxygen happy
    lsst::afw::image::Image<CoaddPixelT> &coadd,       ///< [in,out] coadd to be modified
    lsst::afw::image::Image<WeightPixelT> &weightMap,  ///< [in,out] weight map to be modified
    lsst::afw::image::Image<CoaddPixelT> const &image, ///< masked image to add to coadd;
        ///< this is the sum of weights of all images contributing each pixel of the coadd
    WeightPixelT weight                                ///< relative weight of this image
) {
    typedef lsst::afw::image::Image<CoaddPixelT> Image;
    addToCoaddImpl<Image, WeightPixelT, CheckKnownValue>(coadd, weightMap, image, 0x0, weight);
}

//
// Explicit instantiations
// \cond
#define MASKEDIMAGE(IMAGEPIXEL) afwImage::MaskedImage<IMAGEPIXEL, \
    afwImage::MaskPixel, afwImage::VariancePixel>
#define INSTANTIATE(COADDPIXEL, WEIGHTPIXEL) \
    template void coaddUtils::addToCoadd<COADDPIXEL, WEIGHTPIXEL>( \
        afwImage::Image<COADDPIXEL> &coadd, \
        afwImage::Image<WEIGHTPIXEL> &weightMap, \
        afwImage::Image<COADDPIXEL> const &image,       \
        WEIGHTPIXEL weight \
    ); \
    \
    template void coaddUtils::addToCoadd<COADDPIXEL, WEIGHTPIXEL>( \
        MASKEDIMAGE(COADDPIXEL) &coadd, \
        afwImage::Image<WEIGHTPIXEL> &weightMap, \
        MASKEDIMAGE(COADDPIXEL) const &image, \
        afwImage::MaskPixel const badPixelMask, \
        WEIGHTPIXEL weight \
    );

INSTANTIATE(double, double);
INSTANTIATE(double, float);
INSTANTIATE(double, int);
INSTANTIATE(double, boost::uint16_t);
INSTANTIATE(float, double);
INSTANTIATE(float, float);
INSTANTIATE(float, int);
INSTANTIATE(float, boost::uint16_t);
/* \endcond */
