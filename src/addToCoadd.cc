// -*- LSST-C++ -*-
/**
* @file
*
* @author Russell Owen
*/
#include <limits>
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
 * A boolean functor which always checks if its pixel value val satisfies "(val & badPixel) == 0"
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
 * A boolean functor to check for NaN
 */    
struct CheckFinite {
    CheckFinite(lsst::afw::image::MaskPixel) {}

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
        throw LSST_EXCEPT(pexExcept::InvalidParameterException, \
            "coadd and maskedImage dimensions do not match");
    }
    if (coadd.getDimensions() != weightMap.getDimensions()) {
        throw LSST_EXCEPT(pexExcept::InvalidParameterException, \
            "coadd and weightMap dimensions do not match");
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
}

/**
* @brief add good pixels from an image to a coadd and associated weight map
*
* Weight map: the value of each pixel is the number of good image pixels
* that contributed to the associated pixel of the coadd. Good pixels are defined as (val & badPixelMask) == 0
*
* @throw pexExcept::InvalidParameterException if the image dimensions do not match.
*/
template <typename CoaddPixelT, typename WeightPixelT>
void coaddUtils::addToCoadd(
    // spell out lsst:afw::image to make Doxygen happy
    lsst::afw::image::MaskedImage<CoaddPixelT, lsst::afw::image::MaskPixel,
        lsst::afw::image::VariancePixel> &coadd,        ///< [in,out] coadd to be modified
    lsst::afw::image::Image<WeightPixelT> &weightMap,   ///< [in,out] weight map to be modified
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
* Weight map: the value of each pixel is the number of good image pixels
* that contributed to the associated pixel of the coadd.  Good pixels are defined as non-NaN
*
* @throw pexExcept::InvalidParameterException if the image dimensions do not match.
*/
template <typename CoaddPixelT, typename WeightPixelT>
void coaddUtils::addToCoadd(
    // spell out lsst:afw::image to make Doxygen happy
    lsst::afw::image::Image<CoaddPixelT> &coadd,       ///< [in,out] coadd to be modified
    lsst::afw::image::Image<WeightPixelT> &weightMap,  ///< [in,out] weight map to be modified
    lsst::afw::image::Image<CoaddPixelT> const &image, ///< masked image to add to coadd
    WeightPixelT weight                                ///< relative weight of this image
) {
    typedef lsst::afw::image::Image<CoaddPixelT> Image;
    addToCoaddImpl<Image, WeightPixelT, CheckFinite>(coadd, weightMap, image, 0x0, weight);
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
