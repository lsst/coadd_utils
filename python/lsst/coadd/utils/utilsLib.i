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

%include "lsst/coadd/utils/imageMath.h"
%define %DIVIDEMASKEDIMAGEBYIMAGE(MASKEDIMAGEPIXEL, IMAGEPIXEL)
    %template(divide)
        lsst::coadd::utils::divide<MASKEDIMAGEPIXEL, IMAGEPIXEL>;
%enddef
%DIVIDEMASKEDIMAGEBYIMAGE(double, double);
%DIVIDEMASKEDIMAGEBYIMAGE(double, float);
%DIVIDEMASKEDIMAGEBYIMAGE(double, int);
%DIVIDEMASKEDIMAGEBYIMAGE(double, boost::uint16_t);
%DIVIDEMASKEDIMAGEBYIMAGE(float, double);
%DIVIDEMASKEDIMAGEBYIMAGE(float, float);
%DIVIDEMASKEDIMAGEBYIMAGE(float, int);
%DIVIDEMASKEDIMAGEBYIMAGE(float, boost::uint16_t);

%include "lsst/coadd/utils/setCoaddEdgeBits.h"
%define %SETCOADDEDGEBITS(WEIGHTPIXEL)
    %template(setCoaddEdgeBits) lsst::coadd::utils::setCoaddEdgeBits<WEIGHTPIXEL>;
%enddef
%SETCOADDEDGEBITS(double);
%SETCOADDEDGEBITS(float);
%SETCOADDEDGEBITS(int);
%SETCOADDEDGEBITS(boost::uint16_t);
