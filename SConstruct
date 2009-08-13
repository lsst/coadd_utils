# -*- python -*-
#
# Setup our environment
#
import os.path
import lsst.SConsUtils as scons

env = scons.makeEnv(
    "coadd_utils",
    r"$HeadURL: svn+ssh://svn.lsstcorp.org/DMS/coadd/utils/trunk/SConstruct $",
    [
        ["boost", "boost/version.hpp", "boost_system:C++"],
        ["boost", "boost/version.hpp", "boost_filesystem:C++"],
        ["boost", "boost/regex.hpp", "boost_regex:C++"],
        ["boost", "boost/serialization/base_object.hpp", "boost_serialization:C++"],
        ["boost", "boost/tr1/cmath.hpp", "boost_math_c99:C++"],
        ["python", "Python.h"],
        ["cfitsio", "fitsio.h", "m cfitsio", "ffopen"],
        ["wcslib", "wcslib/wcs.h", "m wcs"],
        ["xpa", "xpa.h", "xpa", "XPAPuts"],
        ["minuit", "Minuit/FCNBase.h", "lcg_Minuit:C++"],
        ["gsl", "gsl/gsl_rng.h", "gslcblas gsl"],
        ["pex_exceptions", "lsst/pex/exceptions.h", "pex_exceptions:C++"],
        ["utils", "lsst/utils/Utils.h", "utils:C++"],
        ["daf_base", "lsst/daf/base.h", "daf_base:C++"],
        ["pex_logging", "lsst/pex/logging/Trace.h", "pex_logging:C++"],
        ["security", "lsst/security/Security.h", "security:C++"],
        ["pex_policy", "lsst/pex/policy/Policy.h", "pex_policy:C++"],
        ["daf_persistence", "lsst/daf/persistence.h", "daf_persistence:C++"],
        ["daf_data", "lsst/daf/data.h", "daf_data:C++"],
        ["eigen", "Eigen/Core.h"],
        ["afw", "lsst/afw/image.h", "afw:C++"],
    ],
)
env.libs["coadd_utils"] += env.getlibs("boost wcslib cfitsio minuit gsl utils daf_base daf_data daf_persistence pex_exceptions pex_logging pex_policy security afw")

#
# Build/install things
#
for d in Split("doc examples lib python/lsst/coadd/utils tests"):
    SConscript(os.path.join(d, "SConscript"))

env['IgnoreFiles'] = r"(~$|\.pyc$|^\.svn$|\.o$)"

Alias("install", [
    env.Install(env['prefix'], "python"),
    env.Install(env['prefix'], "include"),
    env.Install(env['prefix'], "lib"),
    env.Install(env['prefix'] + "/bin", Glob("bin/*.py")),
    env.InstallEups(env['prefix'] + "/ups", Glob("ups/*.table")),
])

scons.CleanTree(r"*~ core *.so *.os *.o *.pyc")

files = scons.filesToTag()
if files:
    env.Command("TAGS", files, "etags -o $TARGET $SOURCES")

env.Declare()
env.Help("""
Utilities for coaddition of images
""")

