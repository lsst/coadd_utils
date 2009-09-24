// -*- LSST-C++ -*-
#ifndef LSST_COADD_UTILS_SETCOADDEDGEBITS_H
#define LSST_COADD_UTILS_SETCOADDEDGEBITS_H
/**
* @file
*
* @author Russell Owen
*/
#include "boost/cstdint.hpp"

#include "lsst/afw/image.h"

namespace lsst {
namespace coadd {
namespace utils {
    
    template<typename WeightPixelT>
    void setCoaddEdgeBits(
        lsst::afw::image::Mask<lsst::afw::image::MaskPixel> &coaddMask,
        lsst::afw::image::Image<WeightPixelT> const &weightMap
    );

}}} // lsst::coadd::utils

#endif // !defined(LSST_COADD_UTILS_SETCOADDEDGEBITS_H)
