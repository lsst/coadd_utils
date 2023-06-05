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
#include "lsst/cpputils/python.h"

#include "lsst/coadd/utils/addToCoadd.h"

namespace py = pybind11;
using namespace pybind11::literals;

namespace lsst {
namespace coadd {
namespace utils {

namespace {

template <typename CoaddPixelT, typename WeightPixelT>
void declareAddToCoadd(py::module &mod) {
    namespace geom = lsst::geom;
    namespace afwImage = lsst::afw::image;

    mod.def("addToCoadd",
            (geom::Box2I(*)(afwImage::Image<CoaddPixelT> &, afwImage::Image<WeightPixelT> &,
                               afwImage::Image<CoaddPixelT> const &, WeightPixelT)) &
                    addToCoadd,
            "coadd"_a, "weightMap"_a, "image"_a, "weight"_a);
    mod.def("addToCoadd",
            (geom::Box2I(*)(afwImage::MaskedImage<CoaddPixelT> &, afwImage::Image<WeightPixelT> &,
                               afwImage::MaskedImage<CoaddPixelT> const &, afwImage::MaskPixel const,
                               WeightPixelT)) &
                    addToCoadd,
            "coadd"_a, "weightMap"_a, "maskedImage"_a, "badPixelMask"_a, "weight"_a);
}

}  // namespace

void wrapAddtoCoadd(lsst::cpputils::python::WrapperCollection &wrappers) {
    auto &mod = wrappers.module;
    declareAddToCoadd<double, double>(mod);
    declareAddToCoadd<double, float>(mod);
    declareAddToCoadd<double, int>(mod);
    declareAddToCoadd<double, std::uint16_t>(mod);
    declareAddToCoadd<float, double>(mod);
    declareAddToCoadd<float, float>(mod);
    declareAddToCoadd<float, int>(mod);
    declareAddToCoadd<float, std::uint16_t>(mod);
}

}  // namespace utils
}  // namespace coadd
}  // namespace lsst
