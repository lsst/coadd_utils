// -*- lsst-c++ -*-
%define utilsLib_DOCSTRING
"
Python interface to lsst::coadd::utils functions and classes
"
%enddef

%feature("autodoc", "1");
%module(package="lsst.coadd.utils", docstring=utilsLib_DOCSTRING) utilsLib

// Everything we will need in the _wrap.cc file
%{
#include "boost/cstdint.hpp"
#include "lsst/coadd/utils.h"
%}

%include "lsst/p_lsstSwig.i"
%import  "lsst/afw/image/imageLib.i" 
%import  "lsst/afw/math/mathLib.i" 

%lsst_exceptions()

%include "lsst/coadd/utils/setCoaddEdgeBits.h"
%template(setCoaddEdgeBits) lsst::coadd::utils::setCoaddEdgeBits<lsst::afw::image::MaskPixel>;
