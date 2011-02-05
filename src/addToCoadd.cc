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
#include "lsst/afw/geom.h"
#include "lsst/coadd/utils/addToCoadd.h"

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
 * Implementation of addToCoadd
 *
 * The template parameter isValidPixel is a functor with operator()
 * which returns true if a given image pixel is valid.
 * This allows us to support multiple image types including
 * MaskedImage with a mask bit and Image with a check for NaN.
 *
 * @return overlapping bounding box, relative to parent image
 */
template <typename CoaddT, typename WeightPixelT, typename isValidPixel>
static lsst::afw::geom::BoxI addToCoaddImpl(
    CoaddT &coadd,                                      // [in,out] coadd to be modified
    lsst::afw::image::Image<WeightPixelT> &weightMap,   // [in,out] weight map to be modified
    CoaddT const &image,                                // image to add to coadd
    lsst::afw::image::MaskPixel const badPixelMask,     // bad pixel mask; may be ignored
    WeightPixelT weight                                 // relative weight of this image
) {
    typedef typename afwImage::Image<WeightPixelT> WeightMapT;
    
    if (coadd.getDimensions() != weightMap.getDimensions()) {
        throw LSST_EXCEPT(pexExcept::InvalidParameterException,
            (boost::format("coadd and weightMap dimensions differ: %dx%d != %dx%d") %
            coadd.getWidth() % coadd.getHeight() % weightMap.getWidth() % weightMap.getHeight()).str());
    }
    if (coadd.getXY0() != weightMap.getXY0()) {
        throw LSST_EXCEPT(pexExcept::InvalidParameterException,
            (boost::format("coadd and weightMap xy0 differ: %d,%d != %d,%d") %
            coadd.getX0() % coadd.getY0() % weightMap.getX0() % weightMap.getY0()).str());
    }
    
    afwGeom::BoxI overlapBox = afwGeom::BoxI(
        afwGeom::makePointI(coadd.getX0(), coadd.getY0()),
        afwGeom::makeExtentI(coadd.getWidth(), coadd.getHeight()));
    overlapBox.clip(afwGeom::BoxI(
        afwGeom::makePointI(image.getX0(), image.getY0()),
        afwGeom::makeExtentI(image.getWidth(), image.getHeight())));
    if (overlapBox.isEmpty()) {
        return overlapBox;
    }

    afwImage::BBox coaddSubregion(
        afwImage::PointI(overlapBox.getMinX() - coadd.getX0(), overlapBox.getMinY() - coadd.getY0()),
        overlapBox.getWidth(), overlapBox.getHeight());
    CoaddT coaddView(coadd, coaddSubregion, false);
    WeightMapT weightMapView(weightMap, coaddSubregion, false);

    afwImage::BBox imageSubregion(
        afwImage::PointI(overlapBox.getMinX() - image.getX0(), overlapBox.getMinY() - image.getY0()),
        overlapBox.getWidth(), overlapBox.getHeight());
    CoaddT imageView(image, imageSubregion, false);

    isValidPixel const isValid(badPixelMask); // functor to check if a pixel is good
    for (int y = 0, endY = imageView.getHeight(); y != endY; ++y) {
        typename CoaddT::const_x_iterator imageIter = imageView.row_begin(y);
        typename CoaddT::const_x_iterator const imageEndIter = imageView.row_end(y);
        typename CoaddT::x_iterator coaddIter = coaddView.row_begin(y);
        typename WeightMapT::x_iterator weightMapIter = weightMapView.row_begin(y);
        for (; imageIter != imageEndIter; ++imageIter, ++coaddIter, ++weightMapIter) {
            if (isValid(imageIter)) {
                typename CoaddT::SinglePixel pix = *imageIter;
                pix *= typename CoaddT::Pixel(weight);
                *coaddIter += pix;
                *weightMapIter += weight;
            }
        }
    }
    return overlapBox;
}
} // anonymous namespace

/**
* @brief add good pixels from an image to a coadd and associated weight map
*
* The images are assumed to be registered to the same wcs and parent origin, thus:
* coadd[i+coadd.x0, j+coadd.y0] += image[i+image.x0, j+image.y0]
* weightMap[i+weightMap.x0, j+weightMap.y0] += weight
* for all good image pixels that overlap a coadd pixel.
* Good pixels are those for which mask & badPixelMask == 0.
*
* @return overlapBBox: overlapping bounding box, relative to parent image (hence XY0 is taken into account)
*
* @throw pexExcept::InvalidParameterException if coadd and weightMap dimensions or xy0 do not match.
*/
template <typename CoaddPixelT, typename WeightPixelT>
lsst::afw::geom::BoxI coaddUtils::addToCoadd(
    // spell out lsst:afw::image to make Doxygen happy
    lsst::afw::image::MaskedImage<CoaddPixelT, lsst::afw::image::MaskPixel,
        lsst::afw::image::VariancePixel> &coadd,        ///< [in,out] coadd to be modified
    lsst::afw::image::Image<WeightPixelT> &weightMap,   ///< [in,out] weight map to be modified;
        ///< this is the sum of weights of all images contributing each pixel of the coadd
    lsst::afw::image::MaskedImage<CoaddPixelT, lsst::afw::image::MaskPixel,
        lsst::afw::image::VariancePixel> const &maskedImage, ///< masked image to add to coadd
    lsst::afw::image::MaskPixel const badPixelMask, ///< skip input pixel if input mask & badPixelMask != 0
    WeightPixelT weight                             ///< relative weight of this image
) {
    typedef lsst::afw::image::MaskedImage<CoaddPixelT> Image;
    return addToCoaddImpl<Image,WeightPixelT,CheckMask>(coadd, weightMap, maskedImage, badPixelMask, weight);
}

/**
* @brief add good pixels from an image to a coadd and associated weight map
*
* The images are assumed to be registered to the same wcs and parent origin, thus:
* coadd[i+coadd.x0, j+coadd.y0] += image[i+image.x0, j+image.y0]
* weightMap[i+weightMap.x0, j+weightMap.y0] += weight
* for all good image pixels that overlap a coadd pixel.
* Good pixels are those that are not NaN (thus they do include +/- inf).
*
* @return overlapBBox: overlapping bounding box, relative to parent image (hence XY0 is taken into account)
*
* @throw pexExcept::InvalidParameterException if coadd and weightMap dimensions or xy0 do not match.
*/
template <typename CoaddPixelT, typename WeightPixelT>
lsst::afw::geom::BoxI coaddUtils::addToCoadd(
    // spell out lsst:afw::image to make Doxygen happy
    lsst::afw::image::Image<CoaddPixelT> &coadd,       ///< [in,out] coadd to be modified
    lsst::afw::image::Image<WeightPixelT> &weightMap,  ///< [in,out] weight map to be modified
    lsst::afw::image::Image<CoaddPixelT> const &image, ///< masked image to add to coadd;
        ///< this is the sum of weights of all images contributing each pixel of the coadd
    WeightPixelT weight                                ///< relative weight of this image
) {
    typedef lsst::afw::image::Image<CoaddPixelT> Image;
    return addToCoaddImpl<Image, WeightPixelT, CheckKnownValue>(coadd, weightMap, image, 0x0, weight);
}

//
// Explicit instantiations
// \cond
#define MASKEDIMAGE(IMAGEPIXEL) afwImage::MaskedImage<IMAGEPIXEL, \
    afwImage::MaskPixel, afwImage::VariancePixel>
#define INSTANTIATE(COADDPIXEL, WEIGHTPIXEL) \
    template lsst::afw::geom::BoxI coaddUtils::addToCoadd<COADDPIXEL, WEIGHTPIXEL>( \
        afwImage::Image<COADDPIXEL> &coadd, \
        afwImage::Image<WEIGHTPIXEL> &weightMap, \
        afwImage::Image<COADDPIXEL> const &image,       \
        WEIGHTPIXEL weight \
    ); \
    \
    template lsst::afw::geom::BoxI coaddUtils::addToCoadd<COADDPIXEL, WEIGHTPIXEL>( \
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
