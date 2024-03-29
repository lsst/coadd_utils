/*
 * This file is part of coadd_utils.
 *
 * Developed for the LSST Data Management System.
 * This product includes software developed by the LSST Project
 * (https://www.lsst.org).
 * See the COPYRIGHT file at the top-level directory of this distribution
 * for details of code ownership.
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
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <https://www.gnu.org/licenses/>.
 */

#include "pybind11/pybind11.h"
#include "lsst/cpputils/python.h"

namespace lsst {
namespace coadd {
namespace utils {

using lsst::cpputils::python::WrapperCollection;
void wrapAddtoCoadd(WrapperCollection &wrappers);
void wrapCopyGoodPixels(WrapperCollection &wrappers);
void wrapSetCoaddEdgeBits(WrapperCollection &wrappers);

PYBIND11_MODULE(_coaddUtilsLib, mod) {
    lsst::cpputils::python::WrapperCollection wrappers(mod, "lsst.coadd.utils");
    wrappers.addSignatureDependency("lsst.afw.image");
    wrappers.addSignatureDependency("lsst.afw.geom");
    wrapAddtoCoadd(wrappers);
    wrapCopyGoodPixels(wrappers);
    wrapSetCoaddEdgeBits(wrappers);
    wrappers.finish();
}

}  // utils
}  // coadd
}  // lsst
