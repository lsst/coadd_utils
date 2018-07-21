/*
 * LSST Data Management System
 * Copyright 2008-2016  AURA/LSST.
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
 * see <https://www.lsstcorp.org/LegalNotices/>.
 */

#include "pybind11/pybind11.h"

#include "lsst/coadd/utils/setCoaddEdgeBits.h"

namespace py = pybind11;
using namespace pybind11::literals;

namespace lsst {
namespace coadd {
namespace utils {

namespace {

template <typename WeightPixelT>
void declareSetCoaddEdgeBits(py::module &mod) {
    namespace afwImage = lsst::afw::image;

    mod.def("setCoaddEdgeBits",
            (void (*)(afwImage::Mask<afwImage::MaskPixel> &, afwImage::Image<WeightPixelT> const &)) &
                    setCoaddEdgeBits,
            "coaddMask"_a, "weightMap"_a);
}

}  // namespace

PYBIND11_MODULE(setCoaddEdgeBits, mod) {
    py::module::import("lsst.afw.image");

    declareSetCoaddEdgeBits<double>(mod);
    declareSetCoaddEdgeBits<float>(mod);
    declareSetCoaddEdgeBits<int>(mod);
    declareSetCoaddEdgeBits<std::uint16_t>(mod);
}

}  // namespace utils
}  // namespace coadd
}  // namespace lsst
