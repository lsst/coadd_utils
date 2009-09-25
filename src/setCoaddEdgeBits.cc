// -*- LSST-C++ -*-
/**
* @file
*
* @author Russell Owen
*/
#include "lsst/pex/exceptions.h"
#include "lsst/coadd/utils/setCoaddEdgeBits.h"

namespace pexExcept = lsst::pex::exceptions;
namespace afwImage = lsst::afw::image;
namespace coaddUtils = lsst::coadd::utils;

/**
* @brief set edge bits of coadd mask based on weight map
*
* @throw pexExcept::InvalidParameterException if the dimensions of coaddMask and weightMap do not match.
*/
template<typename WeightPixelT>
void coaddUtils::setCoaddEdgeBits(
    // spell out lsst:afw::image to make Doxygen happy
    lsst::afw::image::Mask<lsst::afw::image::MaskPixel> &coaddMask, ///< mask of coadd
    lsst::afw::image::Image<WeightPixelT> const &weightMap  ///< weight map
) {
    typedef afwImage::Mask<afwImage::MaskPixel>::x_iterator MaskXIter;
    typedef typename afwImage::Image<WeightPixelT>::const_x_iterator WeightMapConstXIter;

    if (coaddMask.getDimensions() != weightMap.getDimensions()) {
        throw LSST_EXCEPT(pexExcept::InvalidParameterException,
            "coaddMask and weightMap dimensions do not match");
    }
    
    afwImage::MaskPixel const edgeMask = afwImage::Mask<afwImage::MaskPixel>::getPlaneBitMask("EDGE");

    // Set the pixels row by row, to avoid repeated checks for end-of-row
    for (int y = 0, endY = weightMap.getHeight(); y != endY; ++y) {
        WeightMapConstXIter weightMapPtr = weightMap.row_begin(y);
        WeightMapConstXIter const weightMapEndPtr = weightMap.row_end(y);
        MaskXIter coaddMaskPtr = coaddMask.row_begin(y);
        for (; weightMapPtr != weightMapEndPtr; ++weightMapPtr, ++coaddMaskPtr) {
            if (*weightMapPtr == 0) {
                (*coaddMaskPtr) = (*coaddMaskPtr) | edgeMask;
            }
        }
    }
}

//
// Explicit instantiations
//
#define INSTANTIATE(WEIGHTPIXEL) \
    template void coaddUtils::setCoaddEdgeBits<WEIGHTPIXEL>( \
        afwImage::Mask<afwImage::MaskPixel> &coaddMask, \
        afwImage::Image<WEIGHTPIXEL> const &weightMap \
    );

INSTANTIATE(double);
INSTANTIATE(float);
INSTANTIATE(int);
INSTANTIATE(boost::uint16_t);
