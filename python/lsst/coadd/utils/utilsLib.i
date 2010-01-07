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
#include "lsst/afw/geom.h" /* why is this needed?
Without it I see the following when compiling utilsLib_wrap:
python/lsst/coadd/utils/utilsLib_wrap.cc: In function 'void* _p_lsst__afw__geom__ellipses__QuadrupoleTo_p_lsst__afw__geom__ellipses__BaseCore(void*, int*)':
python/lsst/coadd/utils/utilsLib_wrap.cc:13321: error: 'lsst::afw::geom::ellipses' has not been declared
...
*/
%}

%include "lsst/p_lsstSwig.i"
%import "lsst/afw/image/imageLib.i"

%lsst_exceptions()

%include "lsst/coadd/utils/addToCoadd.h"
%define %ADDTOCOADD(COADDPIXEL, WEIGHTPIXEL)
    %template(addToCoadd) lsst::coadd::utils::addToCoadd<COADDPIXEL, WEIGHTPIXEL>;
%enddef
%ADDTOCOADD(double, double);
%ADDTOCOADD(double, float);
%ADDTOCOADD(double, int);
%ADDTOCOADD(double, boost::uint16_t);
%ADDTOCOADD(float, double);
%ADDTOCOADD(float, float);
%ADDTOCOADD(float, int);
%ADDTOCOADD(float, boost::uint16_t);

%include "lsst/coadd/utils/setCoaddEdgeBits.h"
%define %SETCOADDEDGEBITS(WEIGHTPIXEL)
    %template(setCoaddEdgeBits) lsst::coadd::utils::setCoaddEdgeBits<WEIGHTPIXEL>;
%enddef
%SETCOADDEDGEBITS(double);
%SETCOADDEDGEBITS(float);
%SETCOADDEDGEBITS(int);
%SETCOADDEDGEBITS(boost::uint16_t);
