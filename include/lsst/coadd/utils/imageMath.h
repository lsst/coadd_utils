// -*- LSST-C++ -*-
#ifndef LSST_COADD_UTILS_IMAGEMATH_H
#define LSST_COADD_UTILS_IMAGEMATH_H
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

    template <typename MaskedImagePixelT, typename ImagePixelT>
    void divide(
        lsst::afw::image::MaskedImage<MaskedImagePixelT, lsst::afw::image::MaskPixel,
            lsst::afw::image::VariancePixel> &maskedImage,
        lsst::afw::image::Image<ImagePixelT> const &image
    );

}}} // lsst::coadd::utils

#endif // !defined(LSST_COADD_UTILS_IMAGEMATH_H)
