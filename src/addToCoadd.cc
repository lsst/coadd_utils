// -*- LSST-C++ -*-
/**
* @file
*
* @author Russell Owen
*/
#include "lsst/pex/exceptions.h"
#include "lsst/coadd/utils/addToCoadd.h"

namespace pexExcept = lsst::pex::exceptions;
namespace afwImage = lsst::afw::image;
namespace coaddUtils = lsst::coadd::utils;

/**
* @brief add good pixels from an image to a coadd and associated weight map
*
* Weight map: the value of each pixel is the number of good image pixels
* that contributed to the associated pixel of the coadd.
*
* @throw pexExcept::InvalidParameterException if the image dimensions do not match.
*/
template <typename CoaddPixelT, typename WeightPixelT>
void coaddUtils::addToCoadd(
    // spell out lsst:afw::image to make Doxygen happy
    lsst::afw::image::MaskedImage<CoaddPixelT, lsst::afw::image::MaskPixel,
        lsst::afw::image::VariancePixel> &coadd,        ///< coadd to be modified (in/out)
    lsst::afw::image::Image<WeightPixelT> &weightMap,   ///< weight map to be modified (in/out)
    lsst::afw::image::MaskedImage<CoaddPixelT, lsst::afw::image::MaskPixel,
        lsst::afw::image::VariancePixel> const &maskedImage,    ///< masked image to add to coadd
    lsst::afw::image::MaskPixel const badPixelMask, ///< skip input pixel if input mask | badPixelMask != 0
    WeightPixelT weight ///< relative weight of this image
) {
    typedef typename afwImage::MaskedImage<CoaddPixelT, afwImage::MaskPixel, afwImage::VariancePixel> CoaddT;
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
    for (int y = 0, endY = maskedImage.getHeight(); y != endY; ++y) {
        typename CoaddT::const_x_iterator maskedImageIter = maskedImage.row_begin(y);
        typename CoaddT::const_x_iterator const maskedImageEndIter = maskedImage.row_end(y);
        typename CoaddT::x_iterator coaddIter = coadd.row_begin(y);
        typename WeightMapT::x_iterator weightMapIter = weightMap.row_begin(y);
        for (; maskedImageIter != maskedImageEndIter; ++maskedImageIter, ++coaddIter, ++weightMapIter) {
            if ((maskedImageIter.mask() & badPixelMask) == 0) {
                *coaddIter += *maskedImageIter;
                *weightMapIter += weight;
            }
        }
    }
}

//
// Explicit instantiations
//
#define MASKEDIMAGE(IMAGEPIXEL) afwImage::MaskedImage<IMAGEPIXEL, \
    afwImage::MaskPixel, afwImage::VariancePixel>
#define INSTANTIATE(COADDPIXEL, WEIGHTPIXEL) \
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
