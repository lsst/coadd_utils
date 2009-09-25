// -*- LSST-C++ -*-
/**
* @brief bits of image math needed for coadd generation that should perhaps be part of afw instead
*
* @file
*
* @author Russell Owen
*/
#include "lsst/pex/exceptions.h"
#include "lsst/coadd/utils/imageMath.h"

namespace pexExcept = lsst::pex::exceptions;
namespace afwImage = lsst::afw::image;
namespace coaddUtils = lsst::coadd::utils;

/**
* @brief divide a masked image by an image, altering the masked image in place
*
* @throw pexExcept::InvalidParameterException if the image dimensions do not match.
*/
template <typename MaskedImagePixelT, typename ImagePixelT>
void coaddUtils::divide(
    afwImage::MaskedImage<MaskedImagePixelT, afwImage::MaskPixel, afwImage::VariancePixel> &maskedImage,
        ///< masked image to be altered (in/out)
    afwImage::Image<ImagePixelT> const &image         ///< image by which to divide masked image
) {
    typedef typename afwImage::MaskedImage<MaskedImagePixelT, afwImage::MaskPixel,
        afwImage::VariancePixel>::x_iterator MaskedImageXIter;
    typedef typename afwImage::Image<ImagePixelT>::const_x_iterator ImageConstXIter;

    if (maskedImage.getDimensions() != image.getDimensions()) {
        throw LSST_EXCEPT(pexExcept::InvalidParameterException,
            "masked image and image dimensions do not match");
    }

    // Set the pixels row by row, to avoid repeated checks for end-of-row
    for (int y = 0, endY = image.getHeight(); y != endY; ++y) {
        ImageConstXIter imageIter = image.row_begin(y);
        ImageConstXIter imageEndIter = image.row_end(y);
        MaskedImageXIter maskedImageIter = maskedImage.row_begin(y);
        for (; imageIter != imageEndIter; ++imageIter, ++maskedImageIter) {
            MaskedImagePixelT castImagePixel = static_cast<MaskedImagePixelT>(*imageIter);
            maskedImageIter.image() /= castImagePixel;
            maskedImageIter.variance() /= castImagePixel * castImagePixel;
        }
    }
}

//
// Explicit instantiations
//
#define INSTANTIATE(MASKEDIMAGEPIXEL, IMAGEPIXEL) \
    template void coaddUtils::divide<MASKEDIMAGEPIXEL, IMAGEPIXEL> ( \
        afwImage::MaskedImage<MASKEDIMAGEPIXEL, afwImage::MaskPixel, afwImage::VariancePixel> &maskedImage, \
        afwImage::Image<IMAGEPIXEL> const &image);

INSTANTIATE(double, double);
INSTANTIATE(double, float);
INSTANTIATE(double, int);
INSTANTIATE(double, uint16_t);
INSTANTIATE(float, double);
INSTANTIATE(float, float);
INSTANTIATE(float, int);
INSTANTIATE(float, uint16_t);
