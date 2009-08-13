// -*- LSST-C++ -*-
#ifndef LSST_COADD_UTILS_SETCOADDEDGEBITS_H
#define LSST_COADD_UTILS_SETCOADDEDGEBITS_H
/**
* @brief declare setCoaddEdgeBits
*
* @file
*
* @author Russell Owen
*/
#include "boost/cstdint.hpp"

#include "lsst/afw/image.h"

namespace lsst {
namespace coadd {
namespace utils {
    
    template<typename MaskPixelT>
    void setCoaddEdgeBits(
        lsst::afw::image::Mask<MaskPixelT> &coaddMask,
        lsst::afw::image::Image<boost::uint16_t> const &depthMap
    );

}}} // lsst::coadd::utils

#endif // !defined(LSST_COADD_UTILS_SETCOADDEDGEBITS_H)
