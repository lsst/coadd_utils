// -*- LSST-C++ -*-
/**
* @brief define addToCoadd
*
* @file
*
* @author Russell Owen
*/
#include "lsst/pex/exceptions.h"
#include "lsst/coadd/utils/setCoaddEdgeBits.h"

namespace pexExcept = lsst::pex::exceptions;

/**
* @brief set edge bits of coadd mask based on depth map
*
* @throw pexExcept::InvalidParameterException if the image dimensions do not match.
*/
template<typename MaskPixelT>
void lsst::coadd::utils::setCoaddEdgeBits(
    lsst::afw::image::Mask<MaskPixelT> &coaddMask, ///< mask plane of coadd
    lsst::afw::image::Image<boost::uint16_t> const &depthMap    ///< depth map
) {
    typedef lsst::afw::image::Mask<MaskPixelT> MaskT;
    typedef lsst::afw::image::Image<boost::uint16_t> DepthMapT;

    if (coaddMask.getDimensions() != depthMap.getDimensions()) {
        throw LSST_EXCEPT(pexExcept::InvalidParameterException, "coaddMask and depthMap dimensions do not match");
    }
    
    MaskPixelT const edgeMask = MaskT::getPlaneBitMask("EDGE");

    // Set the pixels row by row, to avoid repeated checks for end-of-row
    for (int y = 0, endY = depthMap.getHeight(); y != endY; ++y) {
        typename DepthMapT::const_x_iterator depthMapPtr = depthMap.row_begin(y);
        typename DepthMapT::const_x_iterator depthMapEndPtr = depthMap.row_end(y);
        typename MaskT::x_iterator coaddMaskPtr = coaddMask.row_begin(y);
        for (; depthMapPtr != depthMapEndPtr; ++depthMapPtr, ++coaddMaskPtr) {
            if (*depthMapPtr == 0) {
                (*coaddMaskPtr) = (*coaddMaskPtr) | edgeMask;
            }
        }
    }
}


//
// Explicit instantiations
//
template void lsst::coadd::utils::setCoaddEdgeBits<lsst::afw::image::MaskPixel>(
    lsst::afw::image::Mask<lsst::afw::image::MaskPixel> &coaddMask,
    lsst::afw::image::Image<boost::uint16_t> const &depthMap
);
